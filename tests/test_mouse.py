"""Tests for mouse event parsing."""

from snaptui.keys import (
    MouseMsg, MouseAction, MouseButton,
    _parse_sgr_mouse, PasteMsg, FocusMsg,
)


class TestSgrMouseParsing:
    def test_left_press(self):
        buf = b'\x1b[<0;10;5M'
        result = _parse_sgr_mouse(buf)
        assert isinstance(result, MouseMsg)
        assert result.x == 9  # 1-based to 0-based
        assert result.y == 4
        assert result.button == MouseButton.LEFT
        assert result.action == MouseAction.PRESS

    def test_left_release(self):
        buf = b'\x1b[<0;10;5m'
        result = _parse_sgr_mouse(buf)
        assert isinstance(result, MouseMsg)
        assert result.action == MouseAction.RELEASE

    def test_right_press(self):
        buf = b'\x1b[<2;1;1M'
        result = _parse_sgr_mouse(buf)
        assert isinstance(result, MouseMsg)
        assert result.button == MouseButton.RIGHT

    def test_middle_press(self):
        buf = b'\x1b[<1;1;1M'
        result = _parse_sgr_mouse(buf)
        assert isinstance(result, MouseMsg)
        assert result.button == MouseButton.MIDDLE

    def test_wheel_up(self):
        buf = b'\x1b[<64;10;5M'
        result = _parse_sgr_mouse(buf)
        assert isinstance(result, MouseMsg)
        assert result.action == MouseAction.WHEEL_UP

    def test_wheel_down(self):
        buf = b'\x1b[<65;10;5M'
        result = _parse_sgr_mouse(buf)
        assert isinstance(result, MouseMsg)
        assert result.action == MouseAction.WHEEL_DOWN

    def test_motion(self):
        buf = b'\x1b[<32;15;20M'
        result = _parse_sgr_mouse(buf)
        assert isinstance(result, MouseMsg)
        assert result.action == MouseAction.MOTION

    def test_invalid_format(self):
        result = _parse_sgr_mouse(b'\x1b[A')
        assert result is None

    def test_incomplete(self):
        result = _parse_sgr_mouse(b'\x1b[<0;10M')
        assert result is None
