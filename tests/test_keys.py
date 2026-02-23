"""Tests for keys module — escape sequence parsing."""

from pytea.keys import KeyMsg, SEQUENCES, CTRL_MAP, _read_utf8
import io


class TestKeyMsg:
    def test_equality_with_string(self):
        k = KeyMsg("enter")
        assert k == "enter"
        assert k != "tab"

    def test_equality_with_keymsg(self):
        assert KeyMsg("up") == KeyMsg("up")
        assert KeyMsg("up") != KeyMsg("down")

    def test_char_field(self):
        k = KeyMsg("a", "a")
        assert k.char == "a"

    def test_frozen(self):
        k = KeyMsg("enter")
        try:
            k.key = "tab"  # type: ignore
            assert False, "Should be frozen"
        except AttributeError:
            pass


class TestSequences:
    def test_arrow_keys(self):
        assert SEQUENCES[b'\x1b[A'].key == 'up'
        assert SEQUENCES[b'\x1b[B'].key == 'down'
        assert SEQUENCES[b'\x1b[C'].key == 'right'
        assert SEQUENCES[b'\x1b[D'].key == 'left'

    def test_function_keys(self):
        assert SEQUENCES[b'\x1bOP'].key == 'f1'
        assert SEQUENCES[b'\x1bOQ'].key == 'f2'

    def test_special_keys(self):
        assert SEQUENCES[b'\x1b[H'].key == 'home'
        assert SEQUENCES[b'\x1b[F'].key == 'end'
        assert SEQUENCES[b'\x1b[3~'].key == 'delete'

    def test_shift_tab(self):
        assert SEQUENCES[b'\x1b[Z'].key == 'shift+tab'


class TestCtrlMap:
    def test_enter(self):
        assert CTRL_MAP[13] == 'enter'

    def test_tab(self):
        assert CTRL_MAP[9] == 'tab'

    def test_ctrl_c(self):
        assert CTRL_MAP[3] == 'ctrl+c'

    def test_backspace(self):
        assert CTRL_MAP[127] == 'backspace'

    def test_ctrl_s(self):
        assert CTRL_MAP[19] == 'ctrl+s'
