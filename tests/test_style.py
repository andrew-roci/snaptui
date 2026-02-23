"""Tests for style module — Lip Gloss equivalent."""

from pytea.style import Style, ROUNDED_BORDER, NORMAL_BORDER, RESET
from pytea.strutil import visible_width, strip_ansi


class TestStyleBasic:
    def test_plain_render(self):
        s = Style()
        assert s.render("hello") == "hello"

    def test_bold(self):
        result = Style().bold().render("hello")
        assert "\x1b[1m" in result
        assert "hello" in result
        assert result.endswith(RESET)

    def test_fg_color(self):
        result = Style().fg("#FF0000").render("red")
        assert "\x1b[38;2;255;0;0m" in result

    def test_bg_color(self):
        result = Style().bg("#00FF00").render("green")
        assert "\x1b[48;2;0;255;0m" in result

    def test_chaining(self):
        result = Style().bold().fg("#FFFFFF").bg("#000000").render("styled")
        assert "\x1b[1m" in result
        assert "\x1b[38;2;255;255;255m" in result
        assert "\x1b[48;2;0;0;0m" in result


class TestStylePadding:
    def test_padding_horizontal(self):
        result = Style().padding(0, 2).render("hi")
        assert strip_ansi(result) == "  hi  "

    def test_padding_all(self):
        result = Style().padding(1).render("hi")
        lines = result.split('\n')
        assert len(lines) == 3  # 1 top + content + 1 bottom

    def test_padding_2_args(self):
        result = Style().padding(0, 1).render("hi")
        assert strip_ansi(result) == " hi "


class TestStyleWidth:
    def test_width_pads(self):
        result = Style().width(10).render("hi")
        assert visible_width(result) == 10

    def test_width_wraps(self):
        """Width wraps long text at word boundaries (like Lip Gloss)."""
        result = Style().width(5).render("hello world")
        lines = result.split('\n')
        assert len(lines) == 2
        assert strip_ansi(lines[0]).rstrip() == "hello"
        assert strip_ansi(lines[1]).rstrip() == "world"

    def test_width_wraps_with_padding(self):
        """Content area shrinks to accommodate padding."""
        # width=10, padding 1 on each side → content area = 8
        result = Style().width(10).padding(0, 1).render("hello world foo")
        for line in result.split('\n'):
            assert visible_width(line) == 10

    def test_width_wraps_with_border(self):
        """Content area shrinks to accommodate border."""
        # width=12, border takes 2 → content area = 10
        result = Style().width(12).border(ROUNDED_BORDER).render("hello world foo")
        lines = result.split('\n')
        # All lines should be total width 12
        for line in lines:
            assert visible_width(line) == 12

    def test_width_hard_breaks_long_word(self):
        """A single long word is hard-broken to fit."""
        result = Style().width(5).render("abcdefghij")
        lines = result.split('\n')
        assert len(lines) == 2
        for line in lines:
            assert visible_width(line) == 5


class TestStyleBorder:
    def test_rounded_border(self):
        result = Style().border(ROUNDED_BORDER).render("hi")
        lines = result.split('\n')
        assert lines[0].startswith('╭')
        assert lines[0].endswith('╮')
        assert lines[-1].startswith('╰')
        assert lines[-1].endswith('╯')

    def test_border_with_fg(self):
        result = Style().border(ROUNDED_BORDER).border_fg("#555555").render("hi")
        assert "\x1b[38;2;85;85;85m" in result

    def test_border_adds_to_width(self):
        result = Style().border(NORMAL_BORDER).render("hi")
        lines = result.split('\n')
        # Content "hi" is 2 wide + 2 border chars = 4
        assert visible_width(lines[1]) == 4  # │hi│

    def test_width_with_border(self):
        result = Style().border(ROUNDED_BORDER).width(10).render("hi")
        lines = result.split('\n')
        # Total width should be 10 (border included)
        assert visible_width(lines[0]) == 10


class TestStyleImmutability:
    def test_methods_return_new_style(self):
        s1 = Style()
        s2 = s1.bold()
        assert s1._bold is False
        assert s2._bold is True

    def test_chained_does_not_mutate(self):
        base = Style().fg("#FF0000")
        bold_version = base.bold()
        assert base._bold is False
        assert bold_version._bold is True
        assert bold_version._fg_color == "#FF0000"
