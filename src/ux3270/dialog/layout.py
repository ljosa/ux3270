"""Layout utilities for dialog components."""

from typing import List


def shrink_widths_to_fit(
    widths: List[int],
    min_widths: List[int],
    fixed_width: int,
    available_width: int
) -> List[int]:
    """Shrink column widths to fit within available width.

    Shrinks the longest columns first, respecting minimum widths.

    Args:
        widths: Natural column widths (modified in place and returned)
        min_widths: Minimum width for each column
        fixed_width: Fixed overhead (indent, separators, etc.)
        available_width: Total available terminal width

    Returns:
        The adjusted widths list
    """
    total_width = fixed_width + sum(widths)

    if total_width <= available_width or not widths:
        return widths

    excess = total_width - available_width

    while excess > 0:
        # Find the longest column that can still be shrunk
        max_width = 0
        max_idx = -1
        for i, w in enumerate(widths):
            if w > min_widths[i] and w > max_width:
                max_width = w
                max_idx = i

        if max_idx < 0:
            break  # Can't shrink any more

        widths[max_idx] -= 1
        excess -= 1

    return widths
