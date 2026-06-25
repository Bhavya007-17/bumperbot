from micromouse import maze as M, flood_fill as FF, conventions as C, planner as P


def _solve(seed, n=16):
    m = M.generate(n=n, seed=seed)
    goals = set(C.goal_cells(n))
    dist = FF.flood_fill_distances(m, list(goals))
    cur, heading, steps = C.start_cell(), C.N, 0
    while cur not in goals:
        d = P.pick_next_dir(m, dist, cur, heading)
        assert d is not None
        for t in P.turns_for(heading, d):
            heading = P.apply_turn(heading, t)
        assert heading == d
        cur = m.neighbor(cur[0], cur[1], d)
        steps += 1
        assert steps < 5000
    return steps, dist[C.start_cell()]


def test_walk_reaches_center_optimally():
    for seed in range(30):
        steps, start_dist = _solve(seed)
        assert steps == start_dist  # gradient walk is optimal


def test_turns_for_basic():
    assert P.turns_for(C.N, C.N) == []
    assert P.turns_for(C.N, C.E) == ["turnRight"]
    assert P.turns_for(C.N, C.W) == ["turnLeft"]
    assert P.turns_for(C.N, C.S) == ["turnRight", "turnRight"]
