"""Help component — auto-generated keybind display.

Equivalent to bubbles/help. Keybindings are declared once as data;
the help component renders them in short (inline) or full (overlay) mode,
adapting to terminal width.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..style import Style
from .. import strutil


@dataclass(frozen=True, slots=True)
class KeyBinding:
    """A single key binding declaration.

    Attributes:
        key: Display string for the key(s), e.g. "j/k", "ctrl+s", "?".
        description: What the binding does, e.g. "navigate", "save", "help".
        enabled: Whether this binding is currently active.
    """
    key: str
    description: str
    enabled: bool = True


@dataclass
class Help:
    """Renders a set of key bindings in short or full mode.

    Short mode: single-line "key:desc  key:desc  ..."
    Full mode: multi-column layout with section grouping.

    Attributes:
        bindings: List of KeyBinding objects to display.
        width: Available terminal width.
        separator: String between key and description in short mode.
        spacing: Spaces between binding groups in short mode.
        show_all: If True, render full mode. If False, render short mode.
        key_style: Style applied to the key portion.
        desc_style: Style applied to the description portion.
        sep_style: Style applied to the separator.
    """
    bindings: list[KeyBinding] = field(default_factory=list)
    width: int = 80
    separator: str = ":"
    spacing: int = 2
    show_all: bool = False
    key_style: Style = field(default_factory=lambda: Style().bold())
    desc_style: Style = field(default_factory=lambda: Style().dim())
    sep_style: Style = field(default_factory=lambda: Style().dim())

    def short_help(self) -> str:
        """Render a single-line help bar showing enabled bindings."""
        active = [b for b in self.bindings if b.enabled]
        if not active:
            return ""

        sep = self.sep_style.render(self.separator)
        gap = " " * self.spacing
        parts: list[str] = []
        total_width = 0

        for b in active:
            key_str = self.key_style.render(b.key)
            desc_str = self.desc_style.render(b.description)
            part = f"{key_str}{sep}{desc_str}"
            part_width = strutil.visible_width(b.key) + len(self.separator) + strutil.visible_width(b.description)

            if parts:
                part_width += self.spacing

            if self.width > 0 and total_width + part_width > self.width:
                break

            if parts:
                total_width += self.spacing
            parts.append(part)
            total_width += part_width - (self.spacing if parts and len(parts) > 1 else 0)
            total_width = sum(
                strutil.visible_width(b2.key) + len(self.separator) + strutil.visible_width(b2.description)
                for b2 in active[:len(parts)]
            ) + self.spacing * (len(parts) - 1)

        return gap.join(parts)

    def full_help(self) -> str:
        """Render a multi-line help display showing all enabled bindings."""
        active = [b for b in self.bindings if b.enabled]
        if not active:
            return ""

        # Find max key width for alignment
        max_key_w = max(strutil.visible_width(b.key) for b in active)

        lines: list[str] = []
        for b in active:
            key_str = strutil.pad_right(b.key, max_key_w)
            key_styled = self.key_style.render(key_str)
            desc_styled = self.desc_style.render(b.description)
            lines.append(f"  {key_styled}  {desc_styled}")

        return "\n".join(lines)

    def view(self) -> str:
        """Render help in current mode (short or full)."""
        if self.show_all:
            return self.full_help()
        return self.short_help()
