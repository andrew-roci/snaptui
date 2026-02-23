"""Layout utilities — join_horizontal, join_vertical, place.

Equivalent to Lip Gloss's join functions and place helper.
"""

from __future__ import annotations

from . import strutil

# Alignment constants
LEFT = TOP = 0.0
CENTER = 0.5
RIGHT = BOTTOM = 1.0


def join_horizontal(align: float, *blocks: str) -> str:
    """Merge multi-line blocks side-by-side.

    Args:
        align: Vertical alignment (0.0=top, 0.5=center, 1.0=bottom)
        *blocks: Multi-line strings to join horizontally
    """
    if not blocks:
        return ''
    if len(blocks) == 1:
        return blocks[0]

    # Split each block into lines, determine dimensions
    block_lines: list[list[str]] = []
    widths: list[int] = []
    heights: list[int] = []

    for block in blocks:
        lines = block.split('\n')
        block_lines.append(lines)
        w = max((strutil.visible_width(l) for l in lines), default=0)
        widths.append(w)
        heights.append(len(lines))

    max_height = max(heights)

    # Pad each block to max_height based on alignment
    padded: list[list[str]] = []
    for lines, w, h in zip(block_lines, widths, heights):
        if h < max_height:
            gap = max_height - h
            top_pad = int(gap * align)
            bottom_pad = gap - top_pad
            blank = ' ' * w
            lines = [blank] * top_pad + lines + [blank] * bottom_pad
        # Ensure all lines are same width
        lines = [strutil.pad_right(l, w) for l in lines]
        padded.append(lines)

    # Merge line by line
    result: list[str] = []
    for row in range(max_height):
        parts: list[str] = []
        for col, lines in enumerate(padded):
            parts.append(lines[row])
        result.append(''.join(parts))

    return '\n'.join(result)


def join_vertical(align: float, *blocks: str) -> str:
    """Stack blocks vertically with horizontal alignment.

    Args:
        align: Horizontal alignment (0.0=left, 0.5=center, 1.0=right)
        *blocks: Multi-line strings to stack
    """
    if not blocks:
        return ''
    if len(blocks) == 1:
        return blocks[0]

    # Find max width across all blocks
    all_lines: list[str] = []
    for block in blocks:
        all_lines.extend(block.split('\n'))
    max_width = max((strutil.visible_width(l) for l in all_lines), default=0)

    # Align each line
    result: list[str] = []
    for line in all_lines:
        vw = strutil.visible_width(line)
        gap = max_width - vw
        if gap <= 0 or align == 0.0:
            result.append(line)
        else:
            left_pad = int(gap * align)
            result.append(' ' * left_pad + line)

    return '\n'.join(result)


def place(width: int, height: int, h_align: float, v_align: float, content: str) -> str:
    """Place content within a canvas of given dimensions.

    Args:
        width: Canvas width
        height: Canvas height
        h_align: Horizontal alignment (0.0=left, 0.5=center, 1.0=right)
        v_align: Vertical alignment (0.0=top, 0.5=center, 1.0=bottom)
        content: Multi-line string to place
    """
    lines = content.split('\n')

    # Horizontal alignment: pad each line to canvas width
    aligned_lines: list[str] = []
    for line in lines:
        vw = strutil.visible_width(line)
        gap = width - vw
        if gap <= 0:
            aligned_lines.append(strutil.truncate(line, width))
        else:
            left_pad = int(gap * h_align)
            right_pad = gap - left_pad
            aligned_lines.append(' ' * left_pad + line + ' ' * right_pad)

    # Vertical alignment: pad with blank lines
    content_height = len(aligned_lines)
    if content_height < height:
        gap = height - content_height
        top_pad = int(gap * v_align)
        bottom_pad = gap - top_pad
        blank = ' ' * width
        aligned_lines = [blank] * top_pad + aligned_lines + [blank] * bottom_pad
    elif content_height > height:
        aligned_lines = aligned_lines[:height]

    return '\n'.join(aligned_lines)
