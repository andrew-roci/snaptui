"""Viewport component — scrollable text content.

Equivalent to bubbles/viewport. Used for detail screens with scrollable content.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .. import strutil
from ..keys import KeyMsg
from ..model import Cmd, Msg, WindowSizeMsg


@dataclass
class Viewport:
    """Scrollable text viewport.

    Set content via set_content(), scroll with update().
    Renders visible portion via view().
    """
    width: int = 80
    height: int = 24
    y_offset: int = 0
    _lines: list[str] = field(default_factory=list)

    def set_content(self, content: str) -> None:
        """Set the content to display. Wraps lines to viewport width."""
        self._lines = []
        for line in content.split('\n'):
            if strutil.visible_width(line) > self.width:
                wrapped = strutil.word_wrap(line, self.width)
                self._lines.extend(wrapped.split('\n'))
            else:
                self._lines.append(line)
        # Clamp offset
        self.y_offset = min(self.y_offset, self._max_offset())

    @property
    def total_lines(self) -> int:
        return len(self._lines)

    @property
    def at_top(self) -> bool:
        return self.y_offset <= 0

    @property
    def at_bottom(self) -> bool:
        return self.y_offset >= self._max_offset()

    @property
    def scroll_percent(self) -> float:
        mo = self._max_offset()
        if mo <= 0:
            return 1.0
        return self.y_offset / mo

    def _max_offset(self) -> int:
        return max(0, len(self._lines) - self.height)

    def line_up(self, n: int = 1) -> None:
        self.y_offset = max(0, self.y_offset - n)

    def line_down(self, n: int = 1) -> None:
        self.y_offset = min(self._max_offset(), self.y_offset + n)

    def half_page_up(self) -> None:
        self.line_up(self.height // 2)

    def half_page_down(self) -> None:
        self.line_down(self.height // 2)

    def page_up(self) -> None:
        self.line_up(self.height)

    def page_down(self) -> None:
        self.line_down(self.height)

    def goto_top(self) -> None:
        self.y_offset = 0

    def goto_bottom(self) -> None:
        self.y_offset = self._max_offset()

    def update(self, msg: Msg) -> tuple[Viewport, Cmd]:
        """Handle messages. Returns (self, cmd)."""
        if isinstance(msg, KeyMsg):
            key = msg.key
            if key in ('up', 'k'):
                self.line_up()
            elif key in ('down', 'j'):
                self.line_down()
            elif key == 'pgup':
                self.page_up()
            elif key == 'pgdown':
                self.page_down()
            elif key == 'home':
                self.goto_top()
            elif key == 'end':
                self.goto_bottom()
            elif key == 'ctrl+u':
                self.half_page_up()
            elif key == 'ctrl+d':
                self.half_page_down()
        elif isinstance(msg, WindowSizeMsg):
            self.width = msg.width
            self.height = msg.height
        return self, None

    def view(self) -> str:
        """Render visible portion of content."""
        visible = self._lines[self.y_offset:self.y_offset + self.height]
        # Pad/truncate each line to viewport width
        result: list[str] = []
        for line in visible:
            result.append(strutil.pad_right(strutil.truncate(line, self.width), self.width))
        # Pad remaining height with blank lines
        blank = ' ' * self.width
        while len(result) < self.height:
            result.append(blank)
        return '\n'.join(result)
