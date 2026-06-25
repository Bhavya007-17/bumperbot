"""Navigation decisions, kept free of mms/ROS so they can be unit-tested.

With the full maze known, flood-fill distances form a gradient with no local
minima, so always stepping to the lowest reachable neighbor walks straight to
the goal.
"""
from . import conventions as C


def pick_next_dir(maze, dist, cur, heading):
    """Return the best direction to step from `cur`, or None if already a sink.

    Chooses the reachable neighbor with the smallest distance. Ties prefer
    going straight (current heading), then the fixed order N, E, S, W -- this
    keeps the path smooth and the behavior deterministic.
    """
    best_dir = None
    best_val = None
    for d in (C.N, C.E, C.S, C.W):
        if not maze.open_between(cur[0], cur[1], d):
            continue
        nx, ny = maze.neighbor(cur[0], cur[1], d)
        val = dist[(nx, ny)]
        if best_val is None or val < best_val:
            best_val, best_dir = val, d
        elif val == best_val:
            # tie-break: prefer continuing straight, else lower direction index
            if d == heading and best_dir != heading:
                best_dir = d
    if best_dir is None or best_val >= dist[cur]:
        return None  # no strictly-better neighbor (we are at/below the goal)
    return best_dir


def turns_for(heading, target_dir):
    """Minimal sequence of 'turnLeft'/'turnRight' to face `target_dir`."""
    delta = (target_dir - heading) % 4
    if delta == 0:
        return []
    if delta == 1:
        return ["turnRight"]
    if delta == 2:
        return ["turnRight", "turnRight"]
    return ["turnLeft"]  # delta == 3


def apply_turn(heading, cmd):
    return C.turn_right(heading) if cmd == "turnRight" else C.turn_left(heading)
