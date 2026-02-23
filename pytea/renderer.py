"""Line-diff renderer — port of Bubble Tea's standard_renderer.

Cursor home, walk lines, skip unchanged, write changed with erase-to-EOL.
"""

from __future__ import annotations

import sys

from . import terminal
from . import strutil


class Renderer:
    """Efficient line-diff renderer that only updates changed lines."""

    def __init__(self) -> None:
        self._prev_lines: list[str] = []
        self._out = sys.stdout
        self._repaint = False

    def repaint(self) -> None:
        """Force full repaint on next render (no screen clear)."""
        self._repaint = True

    def render(self, output: str, width: int, height: int) -> None:
        """Render output string to terminal, only updating changed lines."""
        new_lines = output.split('\n')

        # Truncate to terminal height
        if len(new_lines) > height:
            new_lines = new_lines[:height]

        buf: list[str] = [terminal.CURSOR_HOME]

        max_lines = max(len(new_lines), len(self._prev_lines))
        repaint = self._repaint
        self._repaint = False

        for i in range(max_lines):
            if i >= height:
                break

            new = new_lines[i] if i < len(new_lines) else ''
            old = self._prev_lines[i] if i < len(self._prev_lines) else None

            if not repaint and old is not None and old == new:
                # Line unchanged — just move cursor down
                if i < max_lines - 1:
                    buf.append('\r\n')
                continue

            # Truncate line to terminal width
            truncated = strutil.truncate(new, width)
            buf.append(truncated + terminal.ERASE_LINE_RIGHT)
            if i < max_lines - 1:
                buf.append('\r\n')

        # Clear any leftover lines from previous render
        if len(self._prev_lines) > len(new_lines):
            buf.append(terminal.ERASE_SCREEN_BELOW)

        frame = ''.join(buf)
        self._out.write(
            terminal.SYNC_BEGIN + frame + terminal.SYNC_END
        )
        self._out.flush()

        self._prev_lines = new_lines

    def clear(self) -> None:
        """Clear the screen and reset state."""
        self._prev_lines = []
        self._out.write(terminal.ERASE_ENTIRE_SCREEN + terminal.CURSOR_HOME)
        self._out.flush()
