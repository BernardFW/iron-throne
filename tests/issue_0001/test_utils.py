from iron_throne.utils import (
    is_contiguous,
)


def test_contiguous():
    assert is_contiguous([1, 2, 3])
    assert is_contiguous([100, 101, 102, 103])
    assert is_contiguous([])
    assert is_contiguous([0])
    assert not is_contiguous([1, 3])
    assert not is_contiguous([0, 42])
