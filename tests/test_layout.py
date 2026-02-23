"""Tests for layout module — join_horizontal, join_vertical, place."""

from pytea.layout import join_horizontal, join_vertical, place, LEFT, CENTER, RIGHT, TOP, BOTTOM
from pytea.strutil import visible_width


class TestJoinHorizontal:
    def test_two_blocks(self):
        a = "AA\nAA"
        b = "BB\nBB"
        result = join_horizontal(TOP, a, b)
        lines = result.split('\n')
        assert len(lines) == 2
        assert lines[0] == "AABB"
        assert lines[1] == "AABB"

    def test_different_heights_top_align(self):
        a = "A\nA\nA"
        b = "B"
        result = join_horizontal(TOP, a, b)
        lines = result.split('\n')
        assert len(lines) == 3
        assert lines[0] == "AB"
        assert lines[1] == "A "
        assert lines[2] == "A "

    def test_different_heights_bottom_align(self):
        a = "A\nA\nA"
        b = "B"
        result = join_horizontal(BOTTOM, a, b)
        lines = result.split('\n')
        assert len(lines) == 3
        assert lines[0] == "A "
        assert lines[1] == "A "
        assert lines[2] == "AB"

    def test_single_block(self):
        assert join_horizontal(TOP, "hello") == "hello"

    def test_empty(self):
        assert join_horizontal(TOP) == ""


class TestJoinVertical:
    def test_two_blocks(self):
        result = join_vertical(LEFT, "top", "bottom")
        assert result == "top\nbottom"

    def test_center_align(self):
        result = join_vertical(CENTER, "hi", "hello")
        lines = result.split('\n')
        # "hi" should be centered relative to "hello" (width 5)
        assert lines[0].startswith(" ")  # padded
        assert "hi" in lines[0]
        assert lines[1] == "hello"


class TestPlace:
    def test_center(self):
        result = place(10, 5, 0.5, 0.5, "hi")
        lines = result.split('\n')
        assert len(lines) == 5
        for line in lines:
            assert visible_width(line) == 10
        # "hi" should be roughly centered vertically
        content_line = lines[2]  # middle line
        assert "hi" in content_line

    def test_top_left(self):
        result = place(10, 3, 0.0, 0.0, "hi")
        lines = result.split('\n')
        assert lines[0].startswith("hi")
        assert len(lines) == 3

    def test_bottom_right(self):
        result = place(10, 3, 1.0, 1.0, "hi")
        lines = result.split('\n')
        assert "hi" in lines[2]
        assert lines[2].endswith("hi")
