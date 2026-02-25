"""TextArea component — multi-line text editor.

Equivalent to bubbles/textarea. Used for note editing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .. import strutil
from ..keys import KeyMsg
from ..model import Cmd, Msg
from ..style import Style


@dataclass
class TextArea:
    """Multi-line text editor.

    Attributes:
        lines: List of text lines
        cursor_row: Current cursor row
        cursor_col: Current cursor column
        focused: Whether this component receives key events
        width: Display width
        height: Display height (visible lines)
        y_offset: Scroll offset
    """
    lines: list[str] = field(default_factory=lambda: [''])
    cursor_row: int = 0
    cursor_col: int = 0
    focused: bool = False
    width: int = 80
    height: int = 20
    y_offset: int = 0
    _label: str = ''
    show_line_numbers: bool = False
    char_limit: int = 0  # 0 = unlimited

    # Styles
    cursor_style: Style | None = None
    line_number_style: Style | None = None
    focused_line_style: Style | None = None

    def label(self, text: str) -> 'TextArea':
        self._label = text
        return self

    def focus(self) -> None:
        self.focused = True

    def blur(self) -> None:
        self.focused = False

    @property
    def value(self) -> str:
        """Return full text content."""
        return '\n'.join(self.lines)

    def set_value(self, text: str) -> None:
        """Set text content."""
        self.lines = text.split('\n') if text else ['']
        self.cursor_row = 0
        self.cursor_col = 0
        self.y_offset = 0

    def _ensure_cursor_visible(self) -> None:
        """Scroll to keep cursor in view."""
        if self.cursor_row < self.y_offset:
            self.y_offset = self.cursor_row
        elif self.cursor_row >= self.y_offset + self.height:
            self.y_offset = self.cursor_row - self.height + 1

    def _clamp_col(self) -> None:
        """Ensure cursor column is within current line bounds."""
        max_col = len(self.lines[self.cursor_row])
        self.cursor_col = min(self.cursor_col, max_col)

    def update(self, msg: Msg) -> tuple['TextArea', Cmd]:
        if not self.focused or not isinstance(msg, KeyMsg):
            return self, None

        key = msg.key

        # Navigation
        if key == 'up':
            if self.cursor_row > 0:
                self.cursor_row -= 1
                self._clamp_col()
                self._ensure_cursor_visible()
        elif key == 'down':
            if self.cursor_row < len(self.lines) - 1:
                self.cursor_row += 1
                self._clamp_col()
                self._ensure_cursor_visible()
        elif key == 'left':
            if self.cursor_col > 0:
                self.cursor_col -= 1
            elif self.cursor_row > 0:
                self.cursor_row -= 1
                self.cursor_col = len(self.lines[self.cursor_row])
                self._ensure_cursor_visible()
        elif key == 'right':
            if self.cursor_col < len(self.lines[self.cursor_row]):
                self.cursor_col += 1
            elif self.cursor_row < len(self.lines) - 1:
                self.cursor_row += 1
                self.cursor_col = 0
                self._ensure_cursor_visible()
        elif key == 'home' or key == 'ctrl+a':
            self.cursor_col = 0
        elif key == 'end' or key == 'ctrl+e':
            self.cursor_col = len(self.lines[self.cursor_row])

        # Editing
        elif key == 'enter':
            # Split line at cursor
            line = self.lines[self.cursor_row]
            before = line[:self.cursor_col]
            after = line[self.cursor_col:]
            self.lines[self.cursor_row] = before
            self.lines.insert(self.cursor_row + 1, after)
            self.cursor_row += 1
            self.cursor_col = 0
            self._ensure_cursor_visible()
        elif key == 'backspace':
            if self.cursor_col > 0:
                line = self.lines[self.cursor_row]
                self.lines[self.cursor_row] = line[:self.cursor_col - 1] + line[self.cursor_col:]
                self.cursor_col -= 1
            elif self.cursor_row > 0:
                # Merge with previous line
                prev_len = len(self.lines[self.cursor_row - 1])
                self.lines[self.cursor_row - 1] += self.lines[self.cursor_row]
                self.lines.pop(self.cursor_row)
                self.cursor_row -= 1
                self.cursor_col = prev_len
                self._ensure_cursor_visible()
        elif key == 'delete':
            line = self.lines[self.cursor_row]
            if self.cursor_col < len(line):
                self.lines[self.cursor_row] = line[:self.cursor_col] + line[self.cursor_col + 1:]
            elif self.cursor_row < len(self.lines) - 1:
                # Merge with next line
                self.lines[self.cursor_row] += self.lines[self.cursor_row + 1]
                self.lines.pop(self.cursor_row + 1)
        elif key == 'ctrl+k':
            # Kill to end of line
            self.lines[self.cursor_row] = self.lines[self.cursor_row][:self.cursor_col]
        elif key == 'tab':
            # Insert spaces for tab
            self.lines[self.cursor_row] = (
                self.lines[self.cursor_row][:self.cursor_col]
                + '    '
                + self.lines[self.cursor_row][self.cursor_col:]
            )
            self.cursor_col += 4

        # Character input
        elif msg.char and len(msg.char) == 1 and msg.char.isprintable():
            line = self.lines[self.cursor_row]
            self.lines[self.cursor_row] = line[:self.cursor_col] + msg.char + line[self.cursor_col:]
            self.cursor_col += 1
        elif key == 'space':
            line = self.lines[self.cursor_row]
            self.lines[self.cursor_row] = line[:self.cursor_col] + ' ' + line[self.cursor_col:]
            self.cursor_col += 1

        # Page navigation
        elif key == 'pgup':
            self.cursor_row = max(0, self.cursor_row - self.height)
            self._clamp_col()
            self._ensure_cursor_visible()
        elif key == 'pgdown':
            self.cursor_row = min(len(self.lines) - 1, self.cursor_row + self.height)
            self._clamp_col()
            self._ensure_cursor_visible()

        return self, None

    def view(self) -> str:
        result: list[str] = []

        if self._label:
            result.append(self._label)

        # Line number gutter width
        gutter_w = 0
        if self.show_line_numbers:
            gutter_w = len(str(len(self.lines))) + 1  # e.g. "  3 "

        content_w = self.width - gutter_w

        # Visible range
        start = self.y_offset
        end = min(start + self.height, len(self.lines))

        for i in range(start, end):
            line = self.lines[i]

            # Line number
            gutter = ''
            if self.show_line_numbers:
                ln = str(i + 1).rjust(gutter_w - 1) + ' '
                if self.line_number_style:
                    ln = self.line_number_style.render(ln)
                gutter = ln

            # Content with cursor
            display = line
            if self.focused and i == self.cursor_row:
                # Show cursor
                col = min(self.cursor_col, len(display))
                before = display[:col]
                after = display[col:]
                cursor_char = after[0] if after else ' '
                after = after[1:] if after else ''
                cs = self.cursor_style or Style().reverse()
                display = before + cs.render(cursor_char) + after

            # Truncate to content width
            display = strutil.truncate(display, content_w)

            result.append(gutter + display)

        # Pad remaining height
        while len(result) - (1 if self._label else 0) < self.height:
            result.append(' ' * gutter_w if self.show_line_numbers else '')

        return '\n'.join(result)

    def cursor_position(self) -> tuple[int, int] | None:
        """Return (row, col) of the hardware cursor relative to this component's output.

        Returns None when not focused or cursor is not visible (scrolled off-screen).
        Accounts for label line, scroll offset, and line number gutter.
        """
        if not self.focused:
            return None
        # Check if cursor row is in the visible range
        if self.cursor_row < self.y_offset or self.cursor_row >= self.y_offset + self.height:
            return None
        row = self.cursor_row - self.y_offset
        if self._label:
            row += 1
        col = self.cursor_col
        if self.show_line_numbers:
            gutter_w = len(str(len(self.lines))) + 1
            col += gutter_w
        return (row, col)
