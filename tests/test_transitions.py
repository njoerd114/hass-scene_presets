from scene_presets.transitions import ease, interpolate


def test_ease_endpoints():
    for style in ["ease_in", "ease_out", "ease_in_out"]:
        assert ease(0.0, style) == 0.0
        assert ease(1.0, style) == 1.0


def test_ease_in_is_front_loaded():
    assert ease(0.5, "ease_in") == 0.25


def test_ease_out_is_back_loaded():
    assert ease(0.5, "ease_out") == 0.75


def test_ease_in_out_is_symmetric():
    assert ease(0.25, "ease_in_out") == 0.125
    assert ease(0.75, "ease_in_out") == 0.875


def test_ease_clamps_progress():
    assert ease(-1.0, "ease_in") == 0.0
    assert ease(2.0, "ease_out") == 1.0


def test_interpolate_reaches_the_target():
    steps = interpolate(0, 100, 5, "ease_in_out")

    assert len(steps) == 5
    assert steps[-1] == 100


def test_interpolate_single_step_returns_target():
    assert interpolate(10, 20, 1, "ease_in") == [20]


def test_interpolate_is_monotonic_for_ease_in_out():
    steps = interpolate(0, 100, 10, "ease_in_out")

    assert steps == sorted(steps)
