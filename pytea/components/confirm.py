"""Confirm component — Yes/No prompt.

Equivalent to huh Confirm.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..keys import KeyMsg
from ..model import Cmd, Msg
from ..style import Style


@dataclass
class Confirm:
    """Yes/No confirmation prompt.

    Attributes:
        prompt: Question to display
        value: Current selection (True = yes, False = no)
        focused: Whether this component receives key events
        affirmative: Text for "yes" option
        negative: Text for "no" option
    """
    prompt: str = 'Are you sure?'
    value: bool = False
    focused: bool = False
    affirmative: str = 'Yes'
    negative: str = 'No'

    # Styles
    prompt_style: Style | None = None
    selected_style: Style | None = None

    def focus(self) -> None:
        self.focused = True

    def blur(self) -> None:
        self.focused = False

    def update(self, msg: Msg) -> tuple['Confirm', Cmd]:
        if not self.focused or not isinstance(msg, KeyMsg):
            return self, None

        key = msg.key

        if key in ('left', 'h', 'right', 'l', 'tab'):
            self.value = not self.value
        elif key == 'y':
            self.value = True
        elif key == 'n':
            self.value = False
        elif key == 'enter':
            pass  # Confirm current selection — handled by parent form

        return self, None

    def view(self) -> str:
        lines: list[str] = []

        p = self.prompt
        if self.prompt_style:
            p = self.prompt_style.render(p)
        lines.append(p)

        ss = self.selected_style or Style().bold().reverse()
        ns = Style()

        yes_text = f' {self.affirmative} '
        no_text = f' {self.negative} '

        if self.value:
            yes_display = ss.render(yes_text)
            no_display = ns.render(no_text)
        else:
            yes_display = ns.render(yes_text)
            no_display = ss.render(no_text)

        lines.append(yes_display + '  ' + no_display)

        return '\n'.join(lines)
