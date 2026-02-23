"""ANSI-aware string utilities — equivalent to x/ansi width functions + Lip Gloss helpers."""

from __future__ import annotations

import re
import unicodedata

# Matches any ANSI escape sequence (CSI, OSC, etc.)
_ANSI_RE = re.compile(r'\x1b\[[0-9;]*[A-Za-z]|\x1b\][^\x07]*\x07|\x1b[()][AB012]|\x1b\[[\d;]*m')


def strip_ansi(s: str) -> str:
    """Remove all ANSI escape sequences from a string."""
    return _ANSI_RE.sub('', s)


def _char_width(ch: str) -> int:
    """Width of a single character (2 for CJK wide, 0 for combining, 1 otherwise)."""
    cat = unicodedata.category(ch)
    if cat.startswith('M'):  # combining marks
        return 0
    ea = unicodedata.east_asian_width(ch)
    if ea in ('F', 'W'):
        return 2
    return 1


def visible_width(s: str) -> int:
    """Visible width of a string after stripping ANSI escapes, handling CJK."""
    plain = strip_ansi(s)
    return sum(_char_width(ch) for ch in plain)


def pad_right(s: str, width: int) -> str:
    """Pad string with spaces to reach target visible width."""
    vw = visible_width(s)
    if vw >= width:
        return s
    return s + ' ' * (width - vw)


def truncate(s: str, width: int) -> str:
    """Truncate string to fit within visible width, preserving ANSI sequences.

    Walks through the string character by character, tracking visible width.
    ANSI sequences are passed through without counting toward width.
    """
    if width <= 0:
        return ''

    result: list[str] = []
    current_width = 0
    i = 0
    n = len(s)

    while i < n:
        # Check for ANSI escape sequence
        m = _ANSI_RE.match(s, i)
        if m:
            result.append(m.group())
            i = m.end()
            continue

        ch = s[i]
        cw = _char_width(ch)
        if current_width + cw > width:
            break
        result.append(ch)
        current_width += cw
        i += 1

    return ''.join(result)


def word_wrap(s: str, width: int) -> str:
    """Wrap text at word boundaries to fit within width. ANSI-aware.

    Preserves existing newlines. Breaks long words if necessary.
    """
    if width <= 0:
        return s

    lines = s.split('\n')
    wrapped: list[str] = []

    for line in lines:
        if visible_width(line) <= width:
            wrapped.append(line)
            continue

        # Walk through, tracking words and ANSI sequences
        current_line: list[str] = []
        current_width = 0
        # Track active ANSI styling to reapply after wraps
        active_ansi: list[str] = []

        words = _split_words_ansi(line)
        for word in words:
            ww = visible_width(word)

            if current_width == 0:
                # Start of line — always take the word
                if ww > width:
                    # Word itself is too long, hard-break it
                    pieces = _hard_break(word, width)
                    for j, piece in enumerate(pieces):
                        if j > 0:
                            wrapped.append(''.join(current_line))
                            current_line = list(active_ansi)
                        current_line.append(piece)
                    # Drop trailing whitespace-only piece (avoids blank lines)
                    if pieces and strip_ansi(pieces[-1]).strip() == '':
                        current_line = list(active_ansi)
                        current_width = 0
                    else:
                        current_width = visible_width(pieces[-1]) if pieces else 0
                else:
                    current_line.append(word)
                    current_width = ww
                # Track ANSI in this word
                for m in _ANSI_RE.finditer(word):
                    seq = m.group()
                    if seq == '\x1b[0m':
                        active_ansi.clear()
                    else:
                        active_ansi.append(seq)
            elif current_width + ww <= width:
                current_line.append(word)
                current_width += ww
                for m in _ANSI_RE.finditer(word):
                    seq = m.group()
                    if seq == '\x1b[0m':
                        active_ansi.clear()
                    else:
                        active_ansi.append(seq)
            else:
                # Wrap
                wrapped.append(''.join(current_line))
                current_line = list(active_ansi)
                if ww > width:
                    pieces = _hard_break(word, width)
                    for j, piece in enumerate(pieces):
                        if j > 0:
                            wrapped.append(''.join(current_line))
                            current_line = list(active_ansi)
                        current_line.append(piece)
                    # Drop trailing whitespace-only piece
                    if pieces and strip_ansi(pieces[-1]).strip() == '':
                        current_line = list(active_ansi)
                        current_width = 0
                    else:
                        current_width = visible_width(pieces[-1]) if pieces else 0
                else:
                    # Skip leading space on new line
                    stripped = word.lstrip(' ')
                    current_line.append(stripped)
                    current_width = visible_width(stripped)
                for m in _ANSI_RE.finditer(word):
                    seq = m.group()
                    if seq == '\x1b[0m':
                        active_ansi.clear()
                    else:
                        active_ansi.append(seq)

        if current_line:
            wrapped.append(''.join(current_line))

    return '\n'.join(wrapped)


def _split_words_ansi(s: str) -> list[str]:
    """Split string into words preserving spaces and ANSI sequences attached to words."""
    tokens: list[str] = []
    current: list[str] = []
    i = 0
    n = len(s)

    while i < n:
        m = _ANSI_RE.match(s, i)
        if m:
            current.append(m.group())
            i = m.end()
            continue

        ch = s[i]
        if ch == ' ':
            current.append(ch)
            # Space is part of "word" boundary — if next char is non-space, flush
            if i + 1 < n:
                m2 = _ANSI_RE.match(s, i + 1)
                next_ch = s[m2.end()] if m2 and m2.end() < n else (s[i + 1] if i + 1 < n else ' ')
                if next_ch != ' ':
                    tokens.append(''.join(current))
                    current = []
            i += 1
        else:
            current.append(ch)
            i += 1

    if current:
        tokens.append(''.join(current))
    return tokens


def _hard_break(word: str, width: int) -> list[str]:
    """Break a single word that exceeds width into pieces."""
    pieces: list[str] = []
    current: list[str] = []
    current_width = 0
    i = 0
    n = len(word)

    while i < n:
        m = _ANSI_RE.match(word, i)
        if m:
            current.append(m.group())
            i = m.end()
            continue

        ch = word[i]
        cw = _char_width(ch)
        if current_width + cw > width and current:
            pieces.append(''.join(current))
            current = []
            current_width = 0
        current.append(ch)
        current_width += cw
        i += 1

    if current:
        pieces.append(''.join(current))
    return pieces
