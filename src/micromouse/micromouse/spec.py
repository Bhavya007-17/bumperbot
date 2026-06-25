"""maze_spec.json -- the machine-readable contract shared by every component.

The Gazebo world builder, the mms solver, and the cell-motion controller all
read this single file so they never disagree about the maze.
"""
import json

from .maze import Maze
from . import conventions as C


def to_dict(maze: Maze, cell_size: float, wall_thickness: float,
            wall_height: float) -> dict:
    walls = {}
    for (x, y), w in maze.walls.items():
        walls["{},{}".format(x, y)] = {
            "N": bool(w["N"]), "E": bool(w["E"]),
            "S": bool(w["S"]), "W": bool(w["W"]),
        }
    return {
        "n": maze.n,
        "cell_size_m": cell_size,
        "wall_thickness_m": wall_thickness,
        "wall_height_m": wall_height,
        "start_cell": list(C.start_cell()),
        "goal_cells": [list(g) for g in C.goal_cells(maze.n)],
        "walls": walls,
    }


def write(path: str, maze: Maze, cell_size: float, wall_thickness: float,
          wall_height: float):
    with open(path, "w") as f:
        json.dump(to_dict(maze, cell_size, wall_thickness, wall_height),
                  f, indent=2)


def read(path: str):
    """Load a spec file and rebuild a Maze plus the metadata dict."""
    with open(path) as f:
        data = json.load(f)
    n = data["n"]
    maze = Maze(n)
    for key, w in data["walls"].items():
        x, y = (int(v) for v in key.split(","))
        maze.walls[(x, y)] = {
            "N": bool(w["N"]), "E": bool(w["E"]),
            "S": bool(w["S"]), "W": bool(w["W"]),
        }
    return maze, data
