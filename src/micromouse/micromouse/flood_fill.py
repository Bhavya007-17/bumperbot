"""Flood-fill distances, identical in spirit to a classic micromouse solver.

`flood_fill_distances` does a breadth-first flood from the goal cells outward,
stepping only through open passages. The goal cells get distance 0 and every
other reachable cell gets the number of moves to reach the goal. This is exactly
what mms shows in its idle display.
"""
from collections import deque

from . import conventions as C

INF = 10 ** 9


def flood_fill_distances(maze, goals):
    """Return {(x,y): distance} for an open-passage BFS from `goals`."""
    dist = {(x, y): INF for x in range(maze.n) for y in range(maze.n)}
    q = deque()
    for g in goals:
        dist[g] = 0
        q.append(g)
    while q:
        x, y = q.popleft()
        for d in (C.N, C.E, C.S, C.W):
            if maze.open_between(x, y, d):
                nx, ny = maze.neighbor(x, y, d)
                if dist[(nx, ny)] > dist[(x, y)] + 1:
                    dist[(nx, ny)] = dist[(x, y)] + 1
                    q.append((nx, ny))
    return dist
