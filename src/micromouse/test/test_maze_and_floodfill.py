from micromouse import maze as M, flood_fill as FF, conventions as C


def test_generated_maze_is_valid():
    m = M.generate(n=16, seed=1)
    assert m.perimeter_closed()
    assert m.reciprocal()


def test_goal_cells_for_16():
    assert set(C.goal_cells(16)) == {(7, 7), (7, 8), (8, 7), (8, 8)}


def test_floodfill_goal_is_zero_and_reachable():
    for seed in range(10):
        m = M.generate(n=16, seed=seed)
        goals = C.goal_cells(16)
        d = FF.flood_fill_distances(m, goals)
        assert all(d[g] == 0 for g in goals)
        assert d[C.start_cell()] < FF.INF
        assert sum(1 for v in d.values() if v >= FF.INF) == 0


def test_distances_form_a_gradient():
    # every non-goal reachable cell has a neighbor exactly one closer
    m = M.generate(n=16, seed=3)
    goals = set(C.goal_cells(16))
    d = FF.flood_fill_distances(m, list(goals))
    for (x, y), val in d.items():
        if (x, y) in goals or val >= FF.INF:
            continue
        better = [d[m.neighbor(x, y, dr)]
                  for dr in (C.N, C.E, C.S, C.W) if m.open_between(x, y, dr)]
        assert min(better) == val - 1
