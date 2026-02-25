"""Theme system — form component styling + app-level palette.

Theme: applied automatically to Form components on add_field().
AppTheme: app-level palette for titles, sections, borders, list items, etc.
"""

from __future__ import annotations

from dataclasses import dataclass

from .style import HIDDEN_BORDER, THICK_BORDER, ROUNDED_BORDER, DOUBLE_BORDER, Style


# ── Form theme (huh-equivalent) ─────────────────────────────────────────────

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


# ── App theme (snaptui-original) ─────────────────────────────────────────────

@dataclass
class AppTheme:
    """App-level palette for screen layout, sections, borders, and list items.

    Provides named styles that apps destructure into their own styles module,
    so switching themes is a one-line change.
    """
    # Form component theme
    form: Theme

    # App-level palette
    title: Style             # Screen titles / header bars
    subtitle: Style          # Secondary text next to titles
    help: Style              # Help bar at bottom of screens
    error: Style             # Error messages

    # Sections (detail views)
    section_focused: Style   # Active section header
    section_blurred: Style   # Inactive section header
    field_label: Style       # Key in key:value pairs

    # Borders
    border_active: Style     # Focused panel border
    border_inactive: Style   # Unfocused panel border

    # Overlay
    overlay: Style           # Modal/picker container

    # List items
    item_selected: Style     # Selected list item
    item_normal: Style       # Unselected list item
    item_description: Style  # Secondary line under item


def AppThemeCharm() -> AppTheme:
    """Dark-mode palette used by gig_crm and parrhesia viewer."""
    return AppTheme(
        form=ThemeCharm(),

        title=Style().bold().fg("#FAFAFA").bg("#7D56F4").padding(0, 1),
        subtitle=Style().fg("#AFAFAF"),
        help=Style().fg("#626262"),
        error=Style().bold().fg("#FF0000"),

        section_focused=Style().bold().fg("#1A1A2E").bg("#56D6D6"),
        section_blurred=Style().bold().fg("#FAFAFA").bg("#555555"),
        field_label=Style().bold().fg("#7D56F4"),

        border_active=Style().border(ROUNDED_BORDER).border_fg("#7D56F4"),
        border_inactive=Style().border(ROUNDED_BORDER).border_fg("#555555"),

        overlay=Style().border(DOUBLE_BORDER).border_fg("#7D56F4").bg("#1A1A2E").fg("#FAFAFA").padding(1, 2),

        item_selected=Style().bold().fg("#FAFAFA").bg("#7D56F4").padding(0, 1),
        item_normal=Style().fg("#FAFAFA").padding(0, 1),
        item_description=Style().fg("#BBBBBB"),
    )
