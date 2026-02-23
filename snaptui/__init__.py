"""snaptui — Minimal Python Charm stack.

A zero-dependency TUI framework implementing the Elm Architecture
with raw terminal I/O, matching Bubble Tea's approach.
"""

from .model import Model, Msg, Cmd, WindowSizeMsg, QuitMsg, CursorBlinkMsg, quit_cmd, batch
from .keys import KeyMsg
from .program import Program
from .style import Style, ROUNDED_BORDER, NORMAL_BORDER, DOUBLE_BORDER, THICK_BORDER, HIDDEN_BORDER, NO_BORDER, Border
from .theme import Theme, ThemeCharm
from .layout import join_horizontal, join_vertical, place, LEFT, RIGHT, CENTER, TOP, BOTTOM
from . import terminal
from . import strutil

__all__ = [
    # Core
    'Model', 'Msg', 'Cmd', 'WindowSizeMsg', 'QuitMsg', 'CursorBlinkMsg', 'quit_cmd', 'batch',
    'KeyMsg', 'Program',
    # Style + Theme
    'Style', 'Border',
    'ROUNDED_BORDER', 'NORMAL_BORDER', 'DOUBLE_BORDER', 'THICK_BORDER', 'HIDDEN_BORDER', 'NO_BORDER',
    'Theme', 'ThemeCharm',
    # Layout
    'join_horizontal', 'join_vertical', 'place',
    'LEFT', 'RIGHT', 'CENTER', 'TOP', 'BOTTOM',
    # Modules
    'terminal', 'strutil',
]
