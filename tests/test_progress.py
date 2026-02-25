"""Tests for the Progress bar component."""

from snaptui.components.progress import Progress
from snaptui.strutil import strip_ansi


class TestProgress:
    def test_zero_percent(self):
        p = Progress(percent=0.0, width=10, show_percent=False)
        result = strip_ansi(p.view())
        assert "█" not in result

    def test_full_percent(self):
        p = Progress(percent=1.0, width=10, show_percent=False)
        result = strip_ansi(p.view())
        assert "░" not in result

    def test_half_percent(self):
        p = Progress(percent=0.5, width=10, show_percent=False)
        result = strip_ansi(p.view())
        assert "█" in result
        assert "░" in result

    def test_with_percent_text(self):
        p = Progress(percent=0.5, width=20, show_percent=True)
        result = strip_ansi(p.view())
        assert "50%" in result

    def test_set_percent_clamps(self):
        p = Progress()
        p.set_percent(1.5)
        assert p.percent == 1.0
        p.set_percent(-0.5)
        assert p.percent == 0.0
