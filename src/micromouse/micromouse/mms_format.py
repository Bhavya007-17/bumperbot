"""Write a maze in mms 'Num format' so the mms GUI can load it.

Format (one line per cell):  X Y N E S W
  X,Y  cell coordinates (x=col from left, y=row from bottom)
  N E S W  '1' if a wall exists on that side, else '0'

Confirmed against the example in the mms README (its prose mislabels the S and
E columns, but the literal column order N E S W is correct).
"""
from .maze import Maze


def write(path: str, maze: Maze):
    lines = []
    for x in range(maze.n):          # X outer, Y inner (matches README example)
        for y in range(maze.n):
            w = maze.walls[(x, y)]
            lines.append("{} {} {} {} {} {}".format(
                x, y,
                1 if w["N"] else 0,
                1 if w["E"] else 0,
                1 if w["S"] else 0,
                1 if w["W"] else 0,
            ))
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
