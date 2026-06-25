#!/usr/bin/env python3
"""Live 'brain' window.

A standalone window (independent of mms and the Gazebo GUI, and light on the CPU
since it does no 3D rendering) that shows the maze, the flood-fill distance in
every cell, the goal, the robot's current cell, and the path taken so far. It
follows /maze/current_cell published by the brain and updates live.

Run:  ros2 run micromouse brain_viz
      (or)  python3 brain_viz.py
"""
import os
import sys
import threading

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point

from micromouse import spec as spec_mod
from micromouse import flood_fill as FF

try:
    import pygame
except ImportError:
    sys.stderr.write("brain_viz needs pygame:  pip install pygame\n")
    raise

SPEC_PATH = os.environ.get("MICROMOUSE_SPEC",
                           os.path.expanduser("~/.micromouse/maze_spec.json"))
CELL_PX = 40
MARGIN = 24


class VizState:
    def __init__(self):
        self.cur = None
        self.trail = []
        self.lock = threading.Lock()

    def set_cur(self, col, row):
        with self.lock:
            self.cur = (col, row)
            if not self.trail or self.trail[-1] != (col, row):
                self.trail.append((col, row))

    def snapshot(self):
        with self.lock:
            return self.cur, list(self.trail)


class VizNode(Node):
    def __init__(self, state):
        super().__init__("brain_viz")
        self.state = state
        self.create_subscription(Point, "/maze/current_cell", self._on_cell, 10)

    def _on_cell(self, msg: Point):
        self.state.set_cur(int(round(msg.x)), int(round(msg.y)))


def _shade(v, vmax):
    """Subtle blue->light gradient by distance; goal handled by caller."""
    if v >= FF.INF:
        return (60, 60, 60)
    f = min(1.0, v / max(1, vmax))
    return (int(205 - 35 * f), int(215 - 75 * f), int(238 - 30 * f))


def run_pygame(node, maze, data, state):
    n = maze.n
    goals = set(tuple(g) for g in data["goal_cells"])
    dist = FF.flood_fill_distances(maze, list(goals))
    vmax = max((v for v in dist.values() if v < FF.INF), default=1)

    pygame.init()
    size = n * CELL_PX + 2 * MARGIN
    screen = pygame.display.set_mode((size, size + 44))
    pygame.display.set_caption("Micromouse brain - flood-fill")
    font = pygame.font.SysFont(None, 20)
    big = pygame.font.SysFont(None, 24)
    clock = pygame.time.Clock()

    def rect(col, row):
        return pygame.Rect(MARGIN + col * CELL_PX,
                           MARGIN + (n - 1 - row) * CELL_PX, CELL_PX, CELL_PX)

    running = True
    while running and rclpy.ok():
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

        cur, trail = state.snapshot()
        screen.fill((245, 245, 245))

        for col in range(n):
            for row in range(n):
                r = rect(col, row)
                fill = (120, 220, 120) if (col, row) in goals \
                    else _shade(dist[(col, row)], vmax)
                pygame.draw.rect(screen, fill, r)
                t = str(dist[(col, row)]) if dist[(col, row)] < FF.INF else "x"
                txt = font.render(t, True, (25, 25, 25))
                screen.blit(txt, txt.get_rect(center=r.center))

        for (col, row) in trail:
            r = rect(col, row).inflate(-int(CELL_PX * 0.55),
                                       -int(CELL_PX * 0.55))
            pygame.draw.rect(screen, (90, 140, 240), r, border_radius=3)

        if cur is not None:
            pygame.draw.rect(screen, (20, 60, 220), rect(*cur), 4)

        for col in range(n):
            for row in range(n):
                r = rect(col, row)
                w = maze.walls[(col, row)]
                if w["N"]:
                    pygame.draw.line(screen, (0, 0, 0), r.topleft, r.topright, 4)
                if w["S"]:
                    pygame.draw.line(screen, (0, 0, 0),
                                     r.bottomleft, r.bottomright, 4)
                if w["E"]:
                    pygame.draw.line(screen, (0, 0, 0),
                                     r.topright, r.bottomright, 4)
                if w["W"]:
                    pygame.draw.line(screen, (0, 0, 0),
                                     r.topleft, r.bottomleft, 4)

        screen.blit(big.render(
            "center = 0   current = blue outline   trail = path so far",
            True, (40, 40, 40)), (MARGIN, size + 10))

        pygame.display.flip()
        rclpy.spin_once(node, timeout_sec=0.0)
        clock.tick(30)

    pygame.quit()


def main(argv=None):
    rclpy.init(args=argv)
    state = VizState()
    node = VizNode(state)
    maze, data = spec_mod.read(SPEC_PATH)
    try:
        run_pygame(node, maze, data, state)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
