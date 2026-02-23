"""Select component — dropdown/option picker.

Equivalent to huh Select / bubbles/list for simple option picking.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..keys import KeyMsg
from ..model import Cmd, Msg
from ..style import Style


@dataclass
class Select:
    """Option picker / dropdown component.

    Attributes:
        options: List of option strings
        cursor: Currently highlighted index
        selected: Index of selected option (or -1)
        focused: Whether this component receives key events
        height: Max visible options (0 = show all)
    """
    options: list[str] = field(default_factory=list)
    cursor: int = 0
    selected: int = -1
    focused: bool = False
    height: int = 0
    _label: str = ''
    _offset: int = 0  # scroll offset for long lists

    # Styles
    label_style: Style | None = None
    cursor_style: Style | None = None
    selected_style: Style | None = None
    normal_style: Style | None = None

    def label(self, text: str) -> 'Select':
        self._label = text
        return self

    def focus(self) -> None:
        self.focused = True

    def blur(self) -> None:
        self.focused = False

    @property
    def value(self) -> str | None:
        """Return currently selected option text, or None."""
        if 0 <= self.selected < len(self.options):
            return self.options[self.selected]
        return None

    def set_value(self, v: str) -> None:
        """Select the option matching the given string."""
        for i, opt in enumerate(self.options):
            if opt == v:
                self.selected = i
                self.cursor = i
                return

    def update(self, msg: Msg) -> tuple['Select', Cmd]:
        if not self.focused or not isinstance(msg, KeyMsg):
            return self, None

        key = msg.key

        if key in ('up', 'k'):
            if self.cursor > 0:
                self.cursor -= 1
                self._ensure_visible()
        elif key in ('down', 'j'):
            if self.cursor < len(self.options) - 1:
                self.cursor += 1
                self._ensure_visible()
        elif key in ('enter', 'space'):
            self.selected = self.cursor
        elif key == 'home':
            self.cursor = 0
            self._ensure_visible()
        elif key == 'end':
            self.cursor = len(self.options) - 1
            self._ensure_visible()

        return self, None

    def _ensure_visible(self) -> None:
        """Ensure cursor is within visible range."""
        if self.height <= 0:
            return
        if self.cursor < self._offset:
            self._offset = self.cursor
        elif self.cursor >= self._offset + self.height:
            self._offset = self.cursor - self.height + 1

    def view(self) -> str:
        lines: list[str] = []

        if self._label:
            lbl = self._label
            if self.label_style:
                lbl = self.label_style.render(lbl)
            lines.append(lbl)

        # Determine visible range
        start = self._offset
        end = len(self.options) if self.height <= 0 else min(start + self.height, len(self.options))

        for i in range(start, end):
            opt = self.options[i]
            is_cursor = i == self.cursor and self.focused
            is_selected = i == self.selected

            if is_cursor:
                prefix = '> '
                style = self.cursor_style
            elif is_selected:
                prefix = '> '
                style = self.selected_style
            else:
                prefix = '  '
                style = self.normal_style

            text = prefix + opt
            if style:
                text = style.render(text)
            lines.append(text)

        return '\n'.join(lines)
