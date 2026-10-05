from scene_presets.color_management import (
    assign_colors,
    get_next_color,
    get_next_smart_random_color,
    get_random_color,
    get_randomized_colors,
)


def test_get_next_color_wraps_around():
    options = [(1, 1), (2, 2), (3, 3)]

    assert get_next_color(3, options) == (1, 1)
    assert get_next_color(0, options) == (1, 1)


def test_get_next_color_returns_single_option():
    assert get_next_color(5, [(9, 9)]) == (9, 9)


def test_get_random_color_returns_single_option():
    assert get_random_color([(4, 4)]) == (4, 4)


def test_randomized_colors_include_every_color_when_targets_exceed_preset():
    options = [(0.1, 0.1), (0.2, 0.2), (0.3, 0.3), (0.4, 0.4), (0.5, 0.5)]

    colors = get_randomized_colors(options, 6)

    assert len(colors) == 6
    assert set(colors[:5]) == set(options)
    assert all(color in options for color in colors)


def test_smart_shuffle_never_picks_color_across_the_white_point():
    current = (0.6, 0.329)
    opposite = (0.0, 0.329)
    valid = (0.6, 0.6)

    for _ in range(50):
        assert get_next_smart_random_color(current, [opposite, valid]) == valid


def test_smart_shuffle_falls_back_when_no_valid_color_exists():
    current = (0.6, 0.329)
    opposite = (0.0, 0.329)

    assert get_next_smart_random_color(current, [opposite]) == opposite


def test_assign_colors_sequence_repeats_in_order():
    options = [(0.1, 0.1), (0.2, 0.2)]

    assert assign_colors(options, 4, "sequence") == [
        (0.1, 0.1),
        (0.2, 0.2),
        (0.1, 0.1),
        (0.2, 0.2),
    ]


def test_assign_colors_balanced_uses_all_colors_first():
    options = [(0.1, 0.1), (0.2, 0.2), (0.3, 0.3)]

    colors = assign_colors(options, 3, "balanced")

    assert set(colors) == set(options)


def test_assign_colors_random_only_uses_options():
    options = [(0.1, 0.1), (0.2, 0.2)]

    colors = assign_colors(options, 5, "random")

    assert len(colors) == 5
    assert all(color in options for color in colors)
