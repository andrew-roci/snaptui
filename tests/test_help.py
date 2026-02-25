"""Tests for the Help component."""

from snaptui.components.help import Help, KeyBinding
from snaptui.strutil import visible_width


class TestKeyBinding:
    def test_creation(self):
        kb = KeyBinding("q", "quit")
        assert kb.key == "q"
        assert kb.description == "quit"
        assert kb.enabled is True

    def test_disabled(self):
        kb = KeyBinding("q", "quit", enabled=False)
        assert kb.enabled is False


class TestHelpShort:
    def test_empty(self):
        h = Help(bindings=[])
        assert h.short_help() == ""

    def test_single_binding(self):
        h = Help(bindings=[KeyBinding("q", "quit")])
        result = h.short_help()
        assert "q" in result
        assert "quit" in result

    def test_multiple_bindings(self):
        h = Help(bindings=[
            KeyBinding("q", "quit"),
            KeyBinding("?", "help"),
        ])
        result = h.short_help()
        assert "q" in result
        assert "quit" in result
        assert "?" in result
        assert "help" in result

    def test_disabled_excluded(self):
        h = Help(bindings=[
            KeyBinding("q", "quit"),
            KeyBinding("x", "hidden", enabled=False),
        ])
        result = h.short_help()
        assert "q" in result
        assert "hidden" not in result

    def test_width_truncation(self):
        h = Help(bindings=[
            KeyBinding("q", "quit"),
            KeyBinding("very-long-key", "very long description"),
        ], width=20)
        result = h.short_help()
        # Should include at least the first binding
        assert "q" in result


class TestHelpFull:
    def test_empty(self):
        h = Help(bindings=[])
        assert h.full_help() == ""

    def test_alignment(self):
        h = Help(bindings=[
            KeyBinding("q", "quit"),
            KeyBinding("ctrl+s", "save"),
        ])
        result = h.full_help()
        lines = result.split("\n")
        assert len(lines) == 2
        # Both lines should exist
        assert "quit" in lines[0]
        assert "save" in lines[1]

    def test_disabled_excluded(self):
        h = Help(bindings=[
            KeyBinding("q", "quit"),
            KeyBinding("x", "hidden", enabled=False),
        ])
        result = h.full_help()
        assert "hidden" not in result


class TestHelpView:
    def test_short_mode(self):
        h = Help(bindings=[KeyBinding("q", "quit")], show_all=False)
        result = h.view()
        assert "q" in result
        assert "quit" in result

    def test_full_mode(self):
        h = Help(bindings=[KeyBinding("q", "quit")], show_all=True)
        result = h.view()
        assert "q" in result
        assert "quit" in result
