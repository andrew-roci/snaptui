"""Theme system — huh-style automatic component styling.

Provides a Theme dataclass that Form applies to components on add_field(),
so fields get styled automatically without manual overrides.
"""

from __future__ import annotations

from dataclasses import dataclass

from .style import HIDDEN_BORDER, THICK_BORDER, Style


@dataclass
class Theme:
    """Style configuration applied automatically to form components."""
    title: Style | None = None            # Field labels
    cursor: Style | None = None           # TextInput cursor block
    prompt: Style | None = None           # TextInput "> " style
    placeholder: Style | None = None      # TextInput placeholder
    cursor_blink: bool = True             # TextInput blink enabled
    select_cursor: Style | None = None    # Select cursor ">" line style
    selected_option: Style | None = None  # Select selected option style
    focused_button: Style | None = None   # Confirm selected button
    blurred_button: Style | None = None   # Confirm unselected button
    focused_base: Style | None = None     # Container style for focused field
    blurred_base: Style | None = None     # Container style for blurred field


def ThemeCharm() -> Theme:
    """Return a Theme matching huh's ThemeCharm dark-mode palette."""
    return Theme(
        title=Style().bold().fg("#7571F9"),
        cursor=Style().fg("#02BF87"),
        prompt=Style().fg("#F780E2"),
        placeholder=Style().fg("#444444"),
        cursor_blink=True,
        select_cursor=Style().fg("#F780E2"),
        selected_option=Style().fg("#02BF87"),
        focused_button=Style().fg("#FFFDF5").bg("#F780E2"),
        blurred_button=Style().fg("#D0D0D0").bg("#303030"),
        focused_base=Style().border(THICK_BORDER, False, False, False, True).border_fg("#444444").padding_left(1),
        blurred_base=Style().border(HIDDEN_BORDER, False, False, False, True).padding_left(1),
    )
