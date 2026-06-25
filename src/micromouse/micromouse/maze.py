"""Maze representation and generation.

A maze is an n x n grid of cells. Each cell stores 4 wall booleans keyed
"N","E","S","W" (True = wall present). Walls are kept reciprocal: the N wall of
(x,y) is the same physical wall as the S wall of (x,y+1).
"""
import random

from . import conventions as C


class Maze:
    def __init__(self, n: int):
        self.n = n
        # walls[(x, y)] = {"N": bool, "E": bool, "S": bool, "W": bool}
        self.walls = {
            (x, y): {"N": True, "E": True, "S": True, "W": True}
            for x in range(n) for y in range(n)
        }

    # -- queries -------------------------------------------------------------
    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.n and 0 <= y < self.n

    def has_wall(self, x: int, y: int, direction: int) -> bool:
        return self.walls[(x, y)][C.DIR_KEYS[direction]]

    def neighbor(self, x: int, y: int, direction: int):
        dx, dy = C.DELTA[direction]
        return (x + dx, y + dy)

    def open_between(self, x: int, y: int, direction: int) -> bool:
        """True if you can move from (x,y) in `direction` (no wall, in bounds)."""
        nx, ny = self.neighbor(x, y, direction)
        if not self.in_bounds(nx, ny):
            return False
        return not self.has_wall(x, y, direction)

    # -- mutation ------------------------------------------------------------
    def carve(self, x: int, y: int, direction: int):
        """Remove the wall between (x,y) and its neighbor in `direction`."""
        nx, ny = self.neighbor(x, y, direction)
        if not self.in_bounds(nx, ny):
            return
        self.walls[(x, y)][C.DIR_KEYS[direction]] = False
        self.walls[(nx, ny)][C.DIR_KEYS[C.opposite(direction)]] = False

    # -- validation ----------------------------------------------------------
    def perimeter_closed(self) -> bool:
        for i in range(self.n):
            if not self.walls[(i, 0)]["S"]:
                return False
            if not self.walls[(i, self.n - 1)]["N"]:
                return False
            if not self.walls[(0, i)]["W"]:
                return False
            if not self.walls[(self.n - 1, i)]["E"]:
                return False
        return True

    def reciprocal(self) -> bool:
        for (x, y), w in self.walls.items():
            for d in (C.N, C.E, C.S, C.W):
                nx, ny = self.neighbor(x, y, d)
                if self.in_bounds(nx, ny):
                    if w[C.DIR_KEYS[d]] != self.walls[(nx, ny)][C.DIR_KEYS[C.opposite(d)]]:
                        return False
        return True


def generate(n: int = 16, seed=None) -> Maze:
    """Recursive-backtracker (DFS) perfect maze, then open the 2x2 center."""
    rng = random.Random(seed)
    maze = Maze(n)

    visited = set()
    start = (0, 0)
    stack = [start]
    visited.add(start)

    while stack:
        x, y = stack[-1]
        unvisited = []
        for d in (C.N, C.E, C.S, C.W):
            nx, ny = maze.neighbor(x, y, d)
            if maze.in_bounds(nx, ny) and (nx, ny) not in visited:
                unvisited.append(d)
        if not unvisited:
            stack.pop()
            continue
        d = rng.choice(unvisited)
        maze.carve(x, y, d)
        nxt = maze.neighbor(x, y, d)
        visited.add(nxt)
        stack.append(nxt)

    _open_center(maze)
    return maze


def _open_center(maze: Maze):
    """Knock down the 4 interior walls of the center 2x2 goal so it is a room."""
    a = maze.n // 2 - 1
    b = maze.n // 2
    maze.carve(a, a, C.E)   # (a,a) <-> (b,a)
    maze.carve(a, b, C.E)   # (a,b) <-> (b,b)
    maze.carve(a, a, C.N)   # (a,a) <-> (a,b)
    maze.carve(b, a, C.N)   # (b,a) <-> (b,b)


def ascii_art(maze: Maze, dist=None) -> str:
    """Render the maze as ASCII. If `dist` (dict cell->int) is given, print the
    distance centered in each cell (max width 3)."""
    n = maze.n
    lines = []
    # top border
    lines.append("+" + "---+" * n)
    for y in range(n - 1, -1, -1):
        mid = "|"
        bot = "+"
        for x in range(n):
            if dist is not None and (x, y) in dist and dist[(x, y)] < 10**6:
                cell = "{:^3}".format(dist[(x, y)])
            else:
                cell = "   "
            mid += cell + ("|" if maze.walls[(x, y)]["E"] else " ")
            bot += ("---" if maze.walls[(x, y)]["S"] else "   ") + "+"
        lines.append(mid)
        lines.append(bot)
    return "\n".join(lines)
