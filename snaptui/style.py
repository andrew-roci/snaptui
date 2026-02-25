"""Chainable style builder — Lip Gloss equivalent.

Usage:
    s = Style().bold().fg("#FAFAFA").bg("#7D56F4").padding(0, 1).width(30)
    output = s.render("Hello")
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

from . import strutil


# ── Border types ──────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class Border:
    top_left: str
    top_right: str
    bottom_left: str
    bottom_right: str
    horizontal: str
    vertical: str


ROUNDED_BORDER = Border('╭', '╮', '╰', '╯', '─', '│')
NORMAL_BORDER = Border('┌', '┐', '└', '┘', '─', '│')
DOUBLE_BORDER = Border('╔', '╗', '╚', '╝', '═', '║')
THICK_BORDER = Border('┏', '┓', '┗', '┛', '━', '┃')
HIDDEN_BORDER = Border(' ', ' ', ' ', ' ', ' ', ' ')
NO_BORDER = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert '#RRGGBB' or 'RRGGBB' to (r, g, b)."""
    h = hex_color.lstrip('#')
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _fg_code(hex_color: str) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    return f'\x1b[38;2;{r};{g};{b}m'


def _bg_code(hex_color: str) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    return f'\x1b[48;2;{r};{g};{b}m'


RESET = '\x1b[0m'
BOLD_CODE = '\x1b[1m'
DIM_CODE = '\x1b[2m'
ITALIC_CODE = '\x1b[3m'
UNDERLINE_CODE = '\x1b[4m'
REVERSE_CODE = '\x1b[7m'
STRIKETHROUGH_CODE = '\x1b[9m'


# ── Style class ───────────────────────────────────────────────────────────────

class Style:
    """Chainable style builder. Each method returns a new Style (immutable pattern)."""

    __slots__ = (
        '_fg_color', '_bg_color', '_bold', '_dim', '_italic', '_underline',
        '_reverse', '_strikethrough',
        '_padding_top', '_padding_right', '_padding_bottom', '_padding_left',
        '_margin_top', '_margin_right', '_margin_bottom', '_margin_left',
        '_width', '_max_width', '_height', '_max_height',
        '_border', '_border_fg_color',
        '_border_top', '_border_right', '_border_bottom', '_border_left',
        '_align',
    )

    def __init__(self) -> None:
        self._fg_color: str | None = None
        self._bg_color: str | None = None
        self._bold: bool = False
        self._dim: bool = False
        self._italic: bool = False
        self._underline: bool = False
        self._reverse: bool = False
        self._strikethrough: bool = False
        self._padding_top: int = 0
        self._padding_right: int = 0
        self._padding_bottom: int = 0
        self._padding_left: int = 0
        self._margin_top: int = 0
        self._margin_right: int = 0
        self._margin_bottom: int = 0
        self._margin_left: int = 0
        self._width: int = 0  # 0 = natural
        self._max_width: int = 0
        self._height: int = 0
        self._max_height: int = 0
        self._border: Border | None = None
        self._border_fg_color: str | None = None
        self._border_top: bool = True
        self._border_right: bool = True
        self._border_bottom: bool = True
        self._border_left: bool = True
        self._align: float = 0.0  # 0=left, 0.5=center, 1=right

    def _copy(self) -> Style:
        new = Style.__new__(Style)
        for slot in Style.__slots__:
            setattr(new, slot, getattr(self, slot))
        return new

    # ── Text attributes ───────────────────────────────────────────────────

    def bold(self, v: bool = True) -> Style:
        s = self._copy()
        s._bold = v
        return s

    def dim(self, v: bool = True) -> Style:
        s = self._copy()
        s._dim = v
        return s

    def italic(self, v: bool = True) -> Style:
        s = self._copy()
        s._italic = v
        return s

    def underline(self, v: bool = True) -> Style:
        s = self._copy()
        s._underline = v
        return s

    def reverse(self, v: bool = True) -> Style:
        s = self._copy()
        s._reverse = v
        return s

    def strikethrough(self, v: bool = True) -> Style:
        s = self._copy()
        s._strikethrough = v
        return s

    def fg(self, hex_color: str) -> Style:
        s = self._copy()
        s._fg_color = hex_color
        return s

    def bg(self, hex_color: str) -> Style:
        s = self._copy()
        s._bg_color = hex_color
        return s

    # ── Sizing ────────────────────────────────────────────────────────────

    def width(self, n: int) -> Style:
        s = self._copy()
        s._width = n
        return s

    def max_width(self, n: int) -> Style:
        s = self._copy()
        s._max_width = n
        return s

    def height(self, n: int) -> Style:
        s = self._copy()
        s._height = n
        return s

    def max_height(self, n: int) -> Style:
        s = self._copy()
        s._max_height = n
        return s

    # ── Alignment ─────────────────────────────────────────────────────────

    def align(self, pos: float) -> Style:
        """Set horizontal alignment: 0.0=left, 0.5=center, 1.0=right."""
        s = self._copy()
        s._align = pos
        return s

    # ── Padding (CSS shorthand: 1, 2, or 4 args) ─────────────────────────

    def padding(self, *args: int) -> Style:
        s = self._copy()
        if len(args) == 1:
            s._padding_top = s._padding_right = s._padding_bottom = s._padding_left = args[0]
        elif len(args) == 2:
            s._padding_top = s._padding_bottom = args[0]
            s._padding_right = s._padding_left = args[1]
        elif len(args) == 4:
            s._padding_top, s._padding_right, s._padding_bottom, s._padding_left = args
        else:
            raise ValueError('padding() takes 1, 2, or 4 arguments')
        return s

    def padding_top(self, n: int) -> Style:
        s = self._copy()
        s._padding_top = n
        return s

    def padding_right(self, n: int) -> Style:
        s = self._copy()
        s._padding_right = n
        return s

    def padding_bottom(self, n: int) -> Style:
        s = self._copy()
        s._padding_bottom = n
        return s

    def padding_left(self, n: int) -> Style:
        s = self._copy()
        s._padding_left = n
        return s

    # ── Margin (CSS shorthand: 1, 2, or 4 args) ──────────────────────────

    def margin(self, *args: int) -> Style:
        s = self._copy()
        if len(args) == 1:
            s._margin_top = s._margin_right = s._margin_bottom = s._margin_left = args[0]
        elif len(args) == 2:
            s._margin_top = s._margin_bottom = args[0]
            s._margin_right = s._margin_left = args[1]
        elif len(args) == 4:
            s._margin_top, s._margin_right, s._margin_bottom, s._margin_left = args
        else:
            raise ValueError('margin() takes 1, 2, or 4 arguments')
        return s

    # ── Border ────────────────────────────────────────────────────────────

    def border(self, border_type: Border, *sides: bool) -> Style:
        """Set border type. Optional sides: top, right, bottom, left."""
        s = self._copy()
        s._border = border_type
        if len(sides) == 4:
            s._border_top, s._border_right, s._border_bottom, s._border_left = sides
        elif len(sides) == 0:
            s._border_top = s._border_right = s._border_bottom = s._border_left = True
        return s

    def border_fg(self, hex_color: str) -> Style:
        s = self._copy()
        s._border_fg_color = hex_color
        return s

    # ── Render ────────────────────────────────────────────────────────────

    def render(self, content: str) -> str:
        """Apply all styling and return the final ANSI string."""
        lines = content.split('\n')

        # Wrap before padding so wrapped lines all get proper padding
        lines = self._apply_wrap(lines)

        # Apply padding (plain spaces — will be inside ANSI wrapper)
        lines = self._apply_padding(lines)

        # Apply width constraint (pad/safety-truncate; wrapping already handled)
        lines = self._apply_width(lines)

        # Apply height constraint
        lines = self._apply_height(lines)

        # Apply alignment within width
        lines = self._apply_align(lines)

        # Pad all lines to the max width so background fills uniformly
        # (matches Go lipgloss which always normalizes line widths)
        if len(lines) > 1:
            max_w = max((strutil.visible_width(l) for l in lines), default=0)
            lines = [strutil.pad_right(l, max_w) for l in lines]

        # Apply ANSI text styling AFTER padding/width/height/alignment
        # so padding spaces get the background color (matches Go lipgloss)
        prefix = self._build_prefix()
        suffix = RESET if prefix else ''
        if prefix:
            lines = [prefix + line + suffix for line in lines]

        # Apply max_height
        if self._max_height > 0 and len(lines) > self._max_height:
            lines = lines[:self._max_height]

        # Apply border
        lines = self._apply_border(lines)

        # Apply margin
        lines = self._apply_margin(lines)

        # Apply max_width (final truncation)
        if self._max_width > 0:
            lines = [strutil.truncate(line, self._max_width) for line in lines]

        return '\n'.join(lines)

    def _build_prefix(self) -> str:
        parts: list[str] = []
        if self._bold:
            parts.append(BOLD_CODE)
        if self._dim:
            parts.append(DIM_CODE)
        if self._italic:
            parts.append(ITALIC_CODE)
        if self._underline:
            parts.append(UNDERLINE_CODE)
        if self._reverse:
            parts.append(REVERSE_CODE)
        if self._strikethrough:
            parts.append(STRIKETHROUGH_CODE)
        if self._fg_color:
            parts.append(_fg_code(self._fg_color))
        if self._bg_color:
            parts.append(_bg_code(self._bg_color))
        return ''.join(parts)

    def _apply_wrap(self, lines: list[str]) -> list[str]:
        """Wrap lines to fit within width minus padding/border chrome."""
        if self._width <= 0:
            return lines
        # Content width = total width - padding - border
        content_w = self._width - self._padding_left - self._padding_right
        if self._border:
            if self._border_left:
                content_w -= 1
            if self._border_right:
                content_w -= 1
        if content_w <= 0:
            return lines
        result: list[str] = []
        for line in lines:
            wrapped = strutil.word_wrap(line, content_w)
            result.extend(wrapped.split('\n'))
        return result

    def _apply_padding(self, lines: list[str]) -> list[str]:
        result = lines
        if self._padding_left > 0 or self._padding_right > 0:
            left = ' ' * self._padding_left
            right = ' ' * self._padding_right
            result = [left + line + right for line in result]
        if self._padding_top > 0:
            # Determine line width for blank padding lines
            w = max((strutil.visible_width(l) for l in result), default=0) if result else 0
            blank = ' ' * w
            result = [blank] * self._padding_top + result
        if self._padding_bottom > 0:
            w = max((strutil.visible_width(l) for l in result), default=0) if result else 0
            blank = ' ' * w
            result = result + [blank] * self._padding_bottom
        return result

    def _apply_width(self, lines: list[str]) -> list[str]:
        if self._width <= 0:
            return lines
        # Target is the inner content width (width minus border)
        target = self._width
        if self._border:
            bw = 0
            if self._border_left:
                bw += 1
            if self._border_right:
                bw += 1
            target = max(target - bw, 0)
        result: list[str] = []
        for line in lines:
            vw = strutil.visible_width(line)
            if vw < target:
                result.append(strutil.pad_right(line, target))
            elif vw > target:
                # Safety truncate — wrapping should have handled this
                result.append(strutil.truncate(line, target))
            else:
                result.append(line)
        return result

    def _apply_height(self, lines: list[str]) -> list[str]:
        if self._height <= 0:
            return lines
        target = self._height
        if self._border:
            bh = 0
            if self._border_top:
                bh += 1
            if self._border_bottom:
                bh += 1
            target = max(target - bh, 0)
        if len(lines) < target:
            w = max((strutil.visible_width(l) for l in lines), default=0) if lines else 0
            blank = ' ' * w
            lines = lines + [blank] * (target - len(lines))
        elif len(lines) > target:
            lines = lines[:target]
        return lines

    def _apply_align(self, lines: list[str]) -> list[str]:
        if self._align == 0.0:
            return lines
        # Find max width
        max_w = max((strutil.visible_width(l) for l in lines), default=0)
        result: list[str] = []
        for line in lines:
            vw = strutil.visible_width(line)
            gap = max_w - vw
            if gap <= 0:
                result.append(line)
            else:
                left_pad = int(gap * self._align)
                result.append(' ' * left_pad + line + ' ' * (gap - left_pad))
        return result

    def _apply_border(self, lines: list[str]) -> list[str]:
        b = self._border
        if not b:
            return lines

        # Determine content width
        content_w = max((strutil.visible_width(l) for l in lines), default=0) if lines else 0

        bfg = _fg_code(self._border_fg_color) if self._border_fg_color else ''
        breset = RESET if bfg else ''

        result: list[str] = []

        # Top border
        if self._border_top:
            left = b.top_left if self._border_left else ''
            right = b.top_right if self._border_right else ''
            top_line = bfg + left + b.horizontal * content_w + right + breset
            result.append(top_line)

        # Content lines with side borders
        for line in lines:
            vw = strutil.visible_width(line)
            padded = line + ' ' * (content_w - vw)
            left = bfg + b.vertical + breset if self._border_left else ''
            right = bfg + b.vertical + breset if self._border_right else ''
            result.append(left + padded + right)

        # Bottom border
        if self._border_bottom:
            left = b.bottom_left if self._border_left else ''
            right = b.bottom_right if self._border_right else ''
            bottom_line = bfg + left + b.horizontal * content_w + right + breset
            result.append(bottom_line)

        return result

    def _apply_margin(self, lines: list[str]) -> list[str]:
        result = lines
        if self._margin_left > 0 or self._margin_right > 0:
            left = ' ' * self._margin_left
            right = ' ' * self._margin_right
            result = [left + line + right for line in result]
        if self._margin_top > 0:
            result = [''] * self._margin_top + result
        if self._margin_bottom > 0:
            result = result + [''] * self._margin_bottom
        return result
