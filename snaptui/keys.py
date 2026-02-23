"""Keyboard input — port of Bubble Tea's key parser.

Direct stdin reads + escape sequence lookup table.
"""

from __future__ import annotations

import os
import select
from dataclasses import dataclass


@dataclass(frozen=True, slots=True, eq=False)
class KeyMsg:
    """A key press event.

    key: Symbolic name like "enter", "ctrl+c", "up", "a"
    char: Printable character if applicable, empty string otherwise
    """
    key: str
    char: str = ''

    def __eq__(self, other):
        if isinstance(other, str):
            return self.key == other
        if isinstance(other, KeyMsg):
            return self.key == other.key and self.char == other.char
        return NotImplemented

    def __hash__(self):
        return hash((self.key, self.char))


# ── Key constants ─────────────────────────────────────────────────────────────

# Named keys
KEY_ENTER = 'enter'
KEY_TAB = 'tab'
KEY_BACKSPACE = 'backspace'
KEY_ESC = 'esc'
KEY_SPACE = 'space'
KEY_UP = 'up'
KEY_DOWN = 'down'
KEY_LEFT = 'left'
KEY_RIGHT = 'right'
KEY_HOME = 'home'
KEY_END = 'end'
KEY_PGUP = 'pgup'
KEY_PGDOWN = 'pgdown'
KEY_DELETE = 'delete'
KEY_INSERT = 'insert'

# Function keys
KEY_F1 = 'f1'
KEY_F2 = 'f2'
KEY_F3 = 'f3'
KEY_F4 = 'f4'
KEY_F5 = 'f5'
KEY_F6 = 'f6'
KEY_F7 = 'f7'
KEY_F8 = 'f8'
KEY_F9 = 'f9'
KEY_F10 = 'f10'
KEY_F11 = 'f11'
KEY_F12 = 'f12'

# Shift variants
KEY_SHIFT_TAB = 'shift+tab'

# ── Escape sequence table ────────────────────────────────────────────────────

SEQUENCES: dict[bytes, KeyMsg] = {
    # Arrow keys
    b'\x1b[A':    KeyMsg(KEY_UP),
    b'\x1b[B':    KeyMsg(KEY_DOWN),
    b'\x1b[C':    KeyMsg(KEY_RIGHT),
    b'\x1b[D':    KeyMsg(KEY_LEFT),

    # Arrow keys (application mode)
    b'\x1bOA':    KeyMsg(KEY_UP),
    b'\x1bOB':    KeyMsg(KEY_DOWN),
    b'\x1bOC':    KeyMsg(KEY_RIGHT),
    b'\x1bOD':    KeyMsg(KEY_LEFT),

    # Home/End
    b'\x1b[H':    KeyMsg(KEY_HOME),
    b'\x1b[F':    KeyMsg(KEY_END),
    b'\x1bOH':    KeyMsg(KEY_HOME),
    b'\x1bOF':    KeyMsg(KEY_END),
    b'\x1b[1~':   KeyMsg(KEY_HOME),
    b'\x1b[4~':   KeyMsg(KEY_END),

    # Insert/Delete/PgUp/PgDn
    b'\x1b[2~':   KeyMsg(KEY_INSERT),
    b'\x1b[3~':   KeyMsg(KEY_DELETE),
    b'\x1b[5~':   KeyMsg(KEY_PGUP),
    b'\x1b[6~':   KeyMsg(KEY_PGDOWN),

    # Function keys
    b'\x1bOP':    KeyMsg(KEY_F1),
    b'\x1bOQ':    KeyMsg(KEY_F2),
    b'\x1bOR':    KeyMsg(KEY_F3),
    b'\x1bOS':    KeyMsg(KEY_F4),
    b'\x1b[15~':  KeyMsg(KEY_F5),
    b'\x1b[17~':  KeyMsg(KEY_F6),
    b'\x1b[18~':  KeyMsg(KEY_F7),
    b'\x1b[19~':  KeyMsg(KEY_F8),
    b'\x1b[20~':  KeyMsg(KEY_F9),
    b'\x1b[21~':  KeyMsg(KEY_F10),
    b'\x1b[23~':  KeyMsg(KEY_F11),
    b'\x1b[24~':  KeyMsg(KEY_F12),

    # Shift+Tab
    b'\x1b[Z':    KeyMsg(KEY_SHIFT_TAB),

    # Ctrl+Arrow (common sequences)
    b'\x1b[1;5A':  KeyMsg('ctrl+up'),
    b'\x1b[1;5B':  KeyMsg('ctrl+down'),
    b'\x1b[1;5C':  KeyMsg('ctrl+right'),
    b'\x1b[1;5D':  KeyMsg('ctrl+left'),

    # Shift+Arrow
    b'\x1b[1;2A':  KeyMsg('shift+up'),
    b'\x1b[1;2B':  KeyMsg('shift+down'),
    b'\x1b[1;2C':  KeyMsg('shift+right'),
    b'\x1b[1;2D':  KeyMsg('shift+left'),

    # Alt+Arrow
    b'\x1b[1;3A':  KeyMsg('alt+up'),
    b'\x1b[1;3B':  KeyMsg('alt+down'),
    b'\x1b[1;3C':  KeyMsg('alt+right'),
    b'\x1b[1;3D':  KeyMsg('alt+left'),
}

# ── Control character map ────────────────────────────────────────────────────

CTRL_MAP: dict[int, str] = {
    0:   'ctrl+space',
    1:   'ctrl+a',
    2:   'ctrl+b',
    3:   'ctrl+c',
    4:   'ctrl+d',
    5:   'ctrl+e',
    6:   'ctrl+f',
    7:   'ctrl+g',
    8:   'backspace',  # Some terminals send 0x08 for backspace
    9:   'tab',
    10:  'ctrl+j',
    11:  'ctrl+k',
    12:  'ctrl+l',
    13:  'enter',
    14:  'ctrl+n',
    15:  'ctrl+o',
    16:  'ctrl+p',
    17:  'ctrl+q',
    18:  'ctrl+r',
    19:  'ctrl+s',
    20:  'ctrl+t',
    21:  'ctrl+u',
    22:  'ctrl+v',
    23:  'ctrl+w',
    24:  'ctrl+x',
    25:  'ctrl+y',
    26:  'ctrl+z',
    127: 'backspace',
}


# ── Key reading ───────────────────────────────────────────────────────────────

def read_key(fd: int, timeout: float = 0.05) -> KeyMsg | None:
    """Read one key event from raw stdin.

    Args:
        fd: File descriptor to read from (usually stdin)
        timeout: Seconds to wait for data (0 for non-blocking)

    Returns:
        KeyMsg or None if no data available within timeout
    """
    # Wait for data
    ready, _, _ = select.select([fd], [], [], timeout)
    if not ready:
        return None

    b = os.read(fd, 1)
    if not b:
        return None

    byte = b[0]

    # ESC — might be start of escape sequence
    if byte == 0x1b:
        return _read_escape_sequence(fd, b)

    # Control characters
    if byte in CTRL_MAP:
        return KeyMsg(CTRL_MAP[byte])

    # Printable ASCII / UTF-8
    try:
        char = _read_utf8(fd, b)
        if char == ' ':
            return KeyMsg(KEY_SPACE, ' ')
        return KeyMsg(char, char)
    except (UnicodeDecodeError, ValueError):
        return KeyMsg(f'unknown({byte})')


def _read_escape_sequence(fd: int, initial: bytes) -> KeyMsg:
    """Read an escape sequence after receiving ESC byte."""
    buf = initial  # b'\x1b'

    # Read more bytes with short timeout
    for _ in range(7):  # Max escape sequence length
        ready, _, _ = select.select([fd], [], [], 0.05)
        if not ready:
            break
        b = os.read(fd, 1)
        if not b:
            break
        buf += b

        # Check if we have a complete sequence
        if buf in SEQUENCES:
            return SEQUENCES[buf]

        # Check if we're in a CSI sequence (ESC [ ... letter)
        if len(buf) >= 3 and buf[1:2] == b'[':
            last = buf[-1]
            # CSI sequences end with a letter (0x40-0x7E)
            if 0x40 <= last <= 0x7E:
                if buf in SEQUENCES:
                    return SEQUENCES[buf]
                # Unknown CSI sequence
                return KeyMsg(f'unknown({buf!r})')

        # SS3 sequences (ESC O letter)
        if len(buf) >= 3 and buf[1:2] == b'O':
            last = buf[-1]
            if 0x40 <= last <= 0x7E:
                if buf in SEQUENCES:
                    return SEQUENCES[buf]
                return KeyMsg(f'unknown({buf!r})')

    # Check final accumulated buffer
    if buf in SEQUENCES:
        return SEQUENCES[buf]

    # Just ESC alone or Alt+key
    if len(buf) == 1:
        return KeyMsg(KEY_ESC)

    if len(buf) == 2:
        # Alt+key
        second = buf[1]
        if 32 <= second < 127:
            char = chr(second)
            return KeyMsg(f'alt+{char}', char)
        if second in CTRL_MAP:
            return KeyMsg(f'alt+{CTRL_MAP[second]}')

    return KeyMsg(f'unknown({buf!r})')


def _read_utf8(fd: int, initial: bytes) -> str:
    """Read a complete UTF-8 character given the first byte."""
    first = initial[0]

    if first < 0x80:
        return chr(first)

    # Determine expected byte count from first byte
    if first & 0xE0 == 0xC0:
        remaining = 1
    elif first & 0xF0 == 0xE0:
        remaining = 2
    elif first & 0xF8 == 0xF0:
        remaining = 3
    else:
        raise ValueError(f'Invalid UTF-8 start byte: {first:#x}')

    buf = initial
    for _ in range(remaining):
        b = os.read(fd, 1)
        if not b:
            raise ValueError('Incomplete UTF-8 sequence')
        buf += b

    return buf.decode('utf-8')
