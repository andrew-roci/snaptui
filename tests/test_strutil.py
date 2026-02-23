"""Tests for strutil module — ANSI-aware string operations."""

from pytea.strutil import strip_ansi, visible_width, pad_right, truncate, word_wrap


class TestStripAnsi:
    def test_no_ansi(self):
        assert strip_ansi("hello") == "hello"

    def test_fg_color(self):
        assert strip_ansi("\x1b[38;2;255;0;0mred\x1b[0m") == "red"

    def test_bold(self):
        assert strip_ansi("\x1b[1mbold\x1b[0m") == "bold"

    def test_multiple_sequences(self):
        s = "\x1b[1m\x1b[38;2;0;255;0mgreen bold\x1b[0m"
        assert strip_ansi(s) == "green bold"


class TestVisibleWidth:
    def test_plain_ascii(self):
        assert visible_width("hello") == 5

    def test_empty(self):
        assert visible_width("") == 0

    def test_with_ansi(self):
        assert visible_width("\x1b[1mbold\x1b[0m") == 4

    def test_cjk_characters(self):
        assert visible_width("漢字") == 4  # Each CJK char is width 2

    def test_mixed(self):
        assert visible_width("a漢b") == 4  # 1 + 2 + 1


class TestPadRight:
    def test_shorter(self):
        assert pad_right("hi", 5) == "hi   "

    def test_exact(self):
        assert pad_right("hello", 5) == "hello"

    def test_longer(self):
        assert pad_right("hello!", 5) == "hello!"

    def test_with_ansi(self):
        s = "\x1b[1mhi\x1b[0m"
        result = pad_right(s, 5)
        assert result == s + "   "


class TestTruncate:
    def test_shorter(self):
        assert truncate("hi", 5) == "hi"

    def test_exact(self):
        assert truncate("hello", 5) == "hello"

    def test_longer(self):
        assert truncate("hello world", 5) == "hello"

    def test_zero_width(self):
        assert truncate("hello", 0) == ""

    def test_preserves_ansi(self):
        s = "\x1b[1mhello world\x1b[0m"
        result = truncate(s, 5)
        # Should include the bold code and first 5 chars
        assert visible_width(result) == 5
        assert "\x1b[1m" in result

    def test_cjk_truncation(self):
        # CJK chars are width 2, so "漢字" (width 4) truncated to 3
        # should only include "漢" (width 2)
        result = truncate("漢字", 3)
        assert result == "漢"
        assert visible_width(result) == 2


class TestWordWrap:
    def test_short_line(self):
        assert word_wrap("hello", 10) == "hello"

    def test_wrap_at_space(self):
        result = word_wrap("hello world", 6)
        assert "hello" in result
        assert "world" in result

    def test_preserves_newlines(self):
        result = word_wrap("a\nb", 10)
        assert result == "a\nb"

    def test_long_word_breaks(self):
        result = word_wrap("abcdefghij", 5)
        lines = result.split('\n')
        assert all(visible_width(l) <= 5 for l in lines)
