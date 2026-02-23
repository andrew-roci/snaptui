"""TextInput component — single-line text input field.

Equivalent to huh Input / bubbles/textinput.
"""

from __future__ import annotations

from dataclasses import dataclass

from .. import strutil
from ..keys import KeyMsg
from ..model import Cmd, Msg
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
    prompt_style: Style | None = None
    text_style: Style | None = None
    placeholder_style: Style | None = None
    cursor_style: Style | None = None

    def label(self, text: str) -> 'TextInput':
        self._label = text
        return self

    def focus(self) -> None:
        self.focused = True

    def blur(self) -> None:
        self.focused = False

    def set_value(self, v: str) -> None:
        self.value = v
        self.cursor = len(v)

    def update(self, msg: Msg) -> tuple['TextInput', Cmd]:
        if not self.focused:
            return self, None

        if not isinstance(msg, KeyMsg):
            return self, None

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

        return self, None

    def view(self) -> str:
        lines: list[str] = []

        # Label
        if self._label:
            lines.append(self._label)

        # Build input line
        prompt = self.prompt if self.prompt else ''

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
                # Render cursor character with reverse video
                cs = self.cursor_style or Style().reverse()
                cursor_display = cs.render(cursor_char)
                display = before + cursor_display + after

            lines.append(prompt + display)

        return '\n'.join(lines)
