"""TextInput component — single-line text input field.

Equivalent to huh Input / bubbles/textinput.
"""

from __future__ import annotations

from dataclasses import dataclass

from .. import strutil
from ..keys import KeyMsg
from ..model import Cmd, CursorBlinkMsg, Msg
from ..style import Style


@dataclass
class TextInput:
    """Single-line text input with cursor.

    Attributes:
        value: Current text value
        placeholder: Placeholder text shown when empty
        prompt: Prompt string shown before input
        cursor: Cursor position in the value string
        focused: Whether this input is focused (receives key events)
        width: Maximum display width
        char_limit: Maximum character count (0 = unlimited)
    """
    value: str = ''
    placeholder: str = ''
    prompt: str = '> '
    cursor: int = 0
    focused: bool = False
    width: int = 40
    char_limit: int = 0
    _label: str = ''

    # Styles (configurable)
    label_style: Style | None = None
    prompt_style: Style | None = None
    text_style: Style | None = None
    placeholder_style: Style | None = None
    cursor_style: Style | None = None

    # Cursor blink
    cursor_blink: bool = False
    _cursor_visible: bool = True
    _blink_tag: int = 0
    _blink_active: bool = False

    def label(self, text: str) -> 'TextInput':
        self._label = text
        return self

    def focus(self) -> None:
        self.focused = True
        self._blink_active = False
        self._cursor_visible = True

    def blur(self) -> None:
        self.focused = False
        self._blink_tag += 1
        self._blink_active = False

    def set_value(self, v: str) -> None:
        self.value = v
        self.cursor = len(v)

    def _new_blink_cmd(self) -> Cmd:
        tag = self._blink_tag

        def cmd():
            import time
            time.sleep(0.53)
            return CursorBlinkMsg(tag=tag)

        return cmd

    def update(self, msg: Msg) -> tuple['TextInput', Cmd]:
        if not self.focused:
            return self, None

        # Handle blink messages
        if isinstance(msg, CursorBlinkMsg):
            if msg.tag == self._blink_tag:
                self._cursor_visible = not self._cursor_visible
                return self, self._new_blink_cmd()
            # Stale tag — ignore, but start blink if needed (falls through below)

        # Start blink timer if needed
        blink_cmd = None
        if self.cursor_blink and not self._blink_active:
            self._blink_active = True
            self._cursor_visible = True
            blink_cmd = self._new_blink_cmd()

        if not isinstance(msg, KeyMsg):
            return self, blink_cmd

        # On any key press, reset cursor to visible and restart blink
        self._cursor_visible = True
        self._blink_tag += 1
        self._blink_active = True
        blink_cmd = self._new_blink_cmd() if self.cursor_blink else None

        key = msg.key

        if key == 'backspace':
            if self.cursor > 0:
                self.value = self.value[:self.cursor - 1] + self.value[self.cursor:]
                self.cursor -= 1
        elif key == 'delete':
            if self.cursor < len(self.value):
                self.value = self.value[:self.cursor] + self.value[self.cursor + 1:]
        elif key == 'left':
            self.cursor = max(0, self.cursor - 1)
        elif key == 'right':
            self.cursor = min(len(self.value), self.cursor + 1)
        elif key == 'home' or key == 'ctrl+a':
            self.cursor = 0
        elif key == 'end' or key == 'ctrl+e':
            self.cursor = len(self.value)
        elif key == 'ctrl+k':
            # Kill to end of line
            self.value = self.value[:self.cursor]
        elif key == 'ctrl+u':
            # Kill to start of line
            self.value = self.value[self.cursor:]
            self.cursor = 0
        elif key == 'ctrl+w':
            # Kill word backward
            if self.cursor > 0:
                i = self.cursor - 1
                while i > 0 and self.value[i - 1] == ' ':
                    i -= 1
                while i > 0 and self.value[i - 1] != ' ':
                    i -= 1
                self.value = self.value[:i] + self.value[self.cursor:]
                self.cursor = i
        elif msg.char and len(msg.char) == 1 and msg.char.isprintable():
            if self.char_limit == 0 or len(self.value) < self.char_limit:
                self.value = self.value[:self.cursor] + msg.char + self.value[self.cursor:]
                self.cursor += 1
        elif key == 'space':
            if self.char_limit == 0 or len(self.value) < self.char_limit:
                self.value = self.value[:self.cursor] + ' ' + self.value[self.cursor:]
                self.cursor += 1

        return self, blink_cmd

    def view(self) -> str:
        lines: list[str] = []

        # Label
        if self._label:
            lbl = self._label
            if self.label_style:
                lbl = self.label_style.render(lbl)
            lines.append(lbl)

        # Build input line
        prompt = self.prompt if self.prompt else ''
        if self.prompt_style and prompt:
            prompt = self.prompt_style.render(prompt)

        if not self.value and not self.focused:
            # Show placeholder
            ph = self.placeholder
            if self.placeholder_style:
                ph = self.placeholder_style.render(ph)
            lines.append(prompt + ph)
        else:
            # Show value with cursor
            display = self.value
            if self.focused and self.cursor <= len(display):
                # Insert visual cursor
                before = display[:self.cursor]
                after = display[self.cursor:]
                cursor_char = after[0] if after else ' '
                after = after[1:] if after else ''
                # Render cursor character — blink off shows plain char
                if self._cursor_visible or not self.cursor_blink:
                    cs = (self.cursor_style or Style()).reverse()
                    cursor_display = cs.render(cursor_char)
                else:
                    cursor_display = cursor_char
                display = before + cursor_display + after

            lines.append(prompt + display)

        return '\n'.join(lines)

    def cursor_position(self) -> tuple[int, int] | None:
        """Return (row, col) of the hardware cursor relative to this component's output.

        Returns None when not focused. Row accounts for the label line if present.
        Col accounts for the prompt width.
        """
        if not self.focused:
            return None
        row = 1 if self._label else 0
        prompt = self.prompt if self.prompt else ''
        col = strutil.visible_width(prompt) + self.cursor
        return (row, col)
