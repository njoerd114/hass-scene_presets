from __future__ import annotations

EASING_STYLES = ("ease_in", "ease_out", "ease_in_out")
TRANSITION_STYLES = ("fade", "instant", *EASING_STYLES)
DEFAULT_TRANSITION_STEPS = 5


def ease(progress: float, style: str) -> float:
    progress = max(0.0, min(1.0, progress))

    if style == "ease_in":
        return progress * progress

    if style == "ease_out":
        return progress * (2 - progress)

    if style == "ease_in_out":
        if progress < 0.5:
            return 2 * progress * progress
        return -1 + (4 - 2 * progress) * progress

    return progress


def interpolate(start: float, end: float, steps: int, style: str) -> list[float]:
    if steps <= 1:
        return [end]

    return [start + (end - start) * ease(index / steps, style) for index in range(1, steps + 1)]
