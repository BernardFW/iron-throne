from typing import (
    List,
)


def is_contiguous(values: List[int]):
    """
    Checks if all ints of this list are contiguous
    """

    if not values:
        return True

    last = values[0]

    for value in values[1:]:
        if value != last + 1:
            return False
        last = value

    return True
