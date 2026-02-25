"""snaptui — Minimal Python Charm stack.

A zero-dependency TUI framework implementing the Elm Architecture
with raw terminal I/O, matching Bubble Tea's approach.
"""

from .model import Model, Msg, Cmd, View, WindowSizeMsg, QuitMsg, CursorBlinkMsg, Sub, quit_cmd, batch
from .keys import KeyMsg, Mod, MouseMsg, MouseAction, MouseButton, PasteMsg, FocusMsg
from .program import Program
from .style import Style, ROUNDED_BORDER, NORMAL_BORDER, DOUBLE_BORDER, THICK_BORDER, HIDDEN_BORDER, NO_BORDER, Border
from .theme import Theme, ThemeCharm, AppTheme, AppThemeCharm
from .layout import join_horizontal, join_vertical, place, LEFT, RIGHT, CENTER, TOP, BOTTOM
from . import terminal
from . import strutil

__all__ = [
    # Core
    'Model', 'Msg', 'Cmd', 'View', 'WindowSizeMsg', 'QuitMsg', 'CursorBlinkMsg', 'Sub', 'quit_cmd', 'batch',
    'KeyMsg', 'Mod', 'MouseMsg', 'MouseAction', 'MouseButton', 'PasteMsg', 'FocusMsg', 'Program',
    # Style + Theme
    'Style', 'Border',
    'ROUNDED_BORDER', 'NORMAL_BORDER', 'DOUBLE_BORDER', 'THICK_BORDER', 'HIDDEN_BORDER', 'NO_BORDER',
    'Theme', 'ThemeCharm', 'AppTheme', 'AppThemeCharm',
    # Layout
    'join_horizontal', 'join_vertical', 'place',
    'LEFT', 'RIGHT', 'CENTER', 'TOP', 'BOTTOM',
    # Modules
    'terminal', 'strutil',
]
