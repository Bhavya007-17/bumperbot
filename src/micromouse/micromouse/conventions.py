"""Single source of truth for coordinates shared by mms and Gazebo.

mms convention (https://github.com/mackorone/mms):
    x = column, 0 at the LEFT,  increasing to the right
    y = row,    0 at the BOTTOM, increasing upward
    origin = bottom-left corner of the maze
    the mouse starts at cell (0, 0) facing NORTH (+y)

Directions are indexed clockwise so that:
    turnRight = (dir + 1) % 4      turnLeft = (dir - 1) % 4
"""
import math

# Directions (clockwise order) ------------------------------------------------
N, E, S, W = 0, 1, 2, 3
DIR_NAMES = {N: "N", E: "E", S: "S", W: "W"}
DIR_KEYS = {N: "N", E: "E", S: "S", W: "W"}

# (d_col, d_row) for each direction
DELTA = {
    N: (0, 1),
    E: (1, 0),
    S: (0, -1),
    W: (-1, 0),
}


def opposite(direction: int) -> int:
    return (direction + 2) % 4


def turn_right(direction: int) -> int:
    return (direction + 1) % 4


def turn_left(direction: int) -> int:
    return (direction - 1) % 4


def heading_to_yaw_rad(direction: int) -> float:
    """World yaw in radians for a given heading.

    N=+90deg (+y), E=0deg (+x), S=-90deg (-y), W=180deg (-x).
    """
    return math.radians(90.0 - 90.0 * direction)


def goal_cells(n: int):
    """Center 2x2 goal cells for an n x n maze (n even)."""
    a = n // 2 - 1
    b = n // 2
    return [(a, a), (a, b), (b, a), (b, b)]


def start_cell():
    return (0, 0)


def cell_to_world(col: int, row: int, cell_size: float):
    """Center of cell (col,row) in world meters.

    World origin sits at the maze's bottom-left (south-west) corner.
    """
    return (col * cell_size + cell_size / 2.0,
            row * cell_size + cell_size / 2.0)


def normalize_angle(a: float) -> float:
    """Wrap an angle to (-pi, pi]."""
    while a > math.pi:
        a -= 2.0 * math.pi
    while a <= -math.pi:
        a += 2.0 * math.pi
    return a
