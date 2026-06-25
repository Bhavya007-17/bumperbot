#!/usr/bin/env python3
"""Render an mms-style flood-fill solve animation (no ROS / no Gazebo).

Replays the gradient walk the brain performs and writes:
  * GIF  — step-by-step exploration with distance labels
  * PNG  — final frame with the full optimal path highlighted

Usage:
  python3 scripts/render_solve_gif.py --seed 42 --gif media/mms_solve.gif
"""
import argparse
import os
import sys

# Workspace src on path when run from repo root.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "micromouse"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import animation
from PIL import Image

from micromouse import conventions as C
from micromouse import flood_fill as FF
from micromouse import maze as maze_mod
from micromouse import planner as P


def _simulate_path(maze, dist, data):
    goals = set(tuple(g) for g in data["goal_cells"])
    cur = tuple(data["start_cell"])
    heading = C.N
    trail = [cur]
    frames = [("paint", list(trail), cur)]

    while cur not in goals:
        nxt_dir = P.pick_next_dir(maze, dist, cur, heading)
        if nxt_dir is None:
            break
        for t in P.turns_for(heading, nxt_dir):
            heading = P.apply_turn(heading, t)
        cur = maze.neighbor(cur[0], cur[1], nxt_dir)
        trail.append(cur)
        frames.append(("step", list(trail), cur))
    return trail, frames


def _draw_maze(ax, maze, dist, goals, trail, cur, vmax):
    n = maze.n
    ax.clear()
    ax.set_xlim(-0.05, n - 0.05)
    ax.set_ylim(-0.05, n - 0.05)
    ax.set_aspect("equal")
    ax.set_title("mms flood-fill — distances from center goal", fontsize=11)
    ax.set_xticks([])
    ax.set_yticks([])

    for col in range(n):
        for row in range(n):
            val = dist[(col, row)]
            color = "#78dc78" if (col, row) in goals else plt.cm.Blues(
                1.0 - min(1.0, val / max(1, vmax)))
            rect = mpatches.Rectangle((col, row), 1, 1, facecolor=color,
                                      edgecolor="none")
            ax.add_patch(rect)
            label = str(val) if val < FF.INF else "x"
            ax.text(col + 0.5, row + 0.5, label, ha="center", va="center",
                    fontsize=7, color="#1a1a1a")

    for (col, row) in trail[:-1]:
        ax.add_patch(mpatches.Rectangle(
            (col + 0.22, row + 0.22), 0.56, 0.56,
            facecolor="#5a8ce0", edgecolor="none", alpha=0.85))

    if cur is not None:
        ax.add_patch(mpatches.Rectangle(
            (cur[0], cur[1]), 1, 1, fill=False, edgecolor="#143cdc", lw=3))

    for col in range(n):
        for row in range(n):
            w = maze.walls[(col, row)]
            if w["N"]:
                ax.plot([col, col + 1], [row, row], "k", lw=2)
            if w["S"]:
                ax.plot([col, col + 1], [row + 1, row + 1], "k", lw=2)
            if w["E"]:
                ax.plot([col + 1, col + 1], [row, row + 1], "k", lw=2)
            if w["W"]:
                ax.plot([col, col], [row, row + 1], "k", lw=2)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--size", type=int, default=16)
    p.add_argument("--gif", default="media/mms_solve.gif")
    p.add_argument("--png", default="media/mms_solved.png")
    p.add_argument("--fps", type=int, default=8)
    p.add_argument("--dpi", type=int, default=100)
    args = p.parse_args(argv)

    maze = maze_mod.generate(n=args.size, seed=args.seed)
    goals = C.goal_cells(maze.n)
    dist = FF.flood_fill_distances(maze, goals)
    data = {
        "start_cell": list(C.start_cell()),
        "goal_cells": [list(g) for g in goals],
    }
    trail, frames = _simulate_path(maze, dist, data)
    vmax = max((v for v in dist.values() if v < FF.INF), default=1)

    os.makedirs(os.path.dirname(args.gif) or ".", exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 7.2), dpi=args.dpi)

    def update(i):
        _, tr, cur = frames[min(i, len(frames) - 1)]
        _draw_maze(ax, maze, dist, set(goals), tr, cur, vmax)
        return ax.patches

    anim = animation.FuncAnimation(
        fig, update, frames=len(frames), interval=1000 // args.fps, blit=False)
    anim.save(args.gif, writer="pillow", fps=args.fps)
    _draw_maze(ax, maze, dist, set(goals), trail, trail[-1], vmax)
    fig.savefig(args.png, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", args.gif, "and", args.png, "(%d cells)" % len(trail))


if __name__ == "__main__":
    main()
