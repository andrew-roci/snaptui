"""Raw terminal interface — port of termenv + x/term.

No curses. Direct termios/ioctl, matching Bubble Tea's approach.
"""

from __future__ import annotations

import fcntl
import os
import signal
import struct
import sys
import termios
import tty


# ── Alternate screen ─────────────────────────────────────────────────────────

ALT_SCREEN_ON = '\x1b[?1049h'
ALT_SCREEN_OFF = '\x1b[?1049l'

# ── Cursor ────────────────────────────────────────────────────────────────────

HIDE_CURSOR = '\x1b[?25l'
SHOW_CURSOR = '\x1b[?25h'
CURSOR_HOME = '\x1b[H'

# ── Clearing ──────────────────────────────────────────────────────────────────

ERASE_LINE_RIGHT = '\x1b[K'
ERASE_SCREEN_BELOW = '\x1b[J'
ERASE_ENTIRE_SCREEN = '\x1b[2J'

# ── Synchronized output (DEC mode 2026) ─────────────────────────────────────

SYNC_BEGIN = '\x1b[?2026h'
SYNC_END = '\x1b[?2026l'

# ── Reset ─────────────────────────────────────────────────────────────────────

RESET = '\x1b[0m'
BOLD = '\x1b[1m'


# ── Cursor movement ──────────────────────────────────────────────────────────

def cursor_up(n: int) -> str:
    return f'\x1b[{n}A'


def cursor_down(n: int) -> str:
    return f'\x1b[{n}B'


def cursor_forward(n: int) -> str:
    return f'\x1b[{n}C'


def cursor_back(n: int) -> str:
    return f'\x1b[{n}D'


def cursor_to(row: int, col: int) -> str:
    """Move cursor to row, col (1-based)."""
    return f'\x1b[{row};{col}H'


# ── Window title ─────────────────────────────────────────────────────────────

def set_window_title(title: str) -> str:
    """OSC 2 — set terminal window title."""
    return f'\x1b]2;{title}\x07'


# ── Colors (24-bit true color) ───────────────────────────────────────────────

def fg(r: int, g: int, b: int) -> str:
    return f'\x1b[38;2;{r};{g};{b}m'


def bg(r: int, g: int, b: int) -> str:
    return f'\x1b[48;2;{r};{g};{b}m'


# ── Mouse ─────────────────────────────────────────────────────────────────────

ENABLE_MOUSE = '\x1b[?1000h\x1b[?1006h'
DISABLE_MOUSE = '\x1b[?1000l\x1b[?1006l'

# ── Bracketed paste ──────────────────────────────────────────────────────────

ENABLE_BRACKETED_PASTE = '\x1b[?2004h'
DISABLE_BRACKETED_PASTE = '\x1b[?2004l'


# ── Raw mode ──────────────────────────────────────────────────────────────────

def make_raw(fd: int) -> list:
    """Enter raw mode. Returns old termios state for restore."""
    old = termios.tcgetattr(fd)
    tty.setraw(fd)
    # Set VMIN=1, VTIME=0 for blocking single-char reads
    new = termios.tcgetattr(fd)
    new[6][termios.VMIN] = 1
    new[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSAFLUSH, new)
    return old


def restore(fd: int, old_state: list) -> None:
    """Restore terminal to previous state."""
    termios.tcsetattr(fd, termios.TCSAFLUSH, old_state)


# ── Terminal size ─────────────────────────────────────────────────────────────

def get_size(fd: int | None = None) -> tuple[int, int]:
    """Returns (width, height) via TIOCGWINSZ ioctl."""
    if fd is None:
        fd = sys.stdout.fileno()
    try:
        buf = fcntl.ioctl(fd, termios.TIOCGWINSZ, b'\x00' * 8)
        rows, cols = struct.unpack('HHHH', buf)[:2]
        return cols, rows
    except OSError:
        return 80, 24  # fallback


# ── Resize detection ─────────────────────────────────────────────────────────

def listen_for_resize(callback) -> None:
    """Register SIGWINCH handler that calls callback(width, height)."""
    def handler(signum, frame):
        w, h = get_size()
        callback(w, h)
    signal.signal(signal.SIGWINCH, handler)


# ── Output helpers ────────────────────────────────────────────────────────────

def write(s: str) -> None:
    """Write string to stdout and flush."""
    sys.stdout.write(s)
    sys.stdout.flush()


def write_bytes(b: bytes) -> None:
    """Write bytes to stdout fd."""
    os.write(sys.stdout.fileno(), b)
