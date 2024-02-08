"""Unit tests for the extract script."""


from extract import add_nums
import sys

sys.path.append("..")


def test_add_nums():
    assert add_nums(1, 2) == 3
