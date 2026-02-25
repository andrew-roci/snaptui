"""Progress bar component — visual completion indicator.

Equivalent to bubbles/progress. Renders a horizontal bar showing
completion percentage.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..style import Style
from .. import strutil


@dataclass
class Progress:
    """Visual progress bar.

    Attributes:
        percent: Completion from 0.0 to 1.0.
        width: Total width of the progress bar in characters.
        fill_char: Character for the filled portion.
        empty_char: Character for the empty portion.
        show_percent: Whether to append percentage text.
        fill_style: Style for the filled portion.
        empty_style: Style for the empty portion.
        percent_style: Style for the percentage text.
    """
    percent: float = 0.0
    width: int = 40
    fill_char: str = "█"
    empty_char: str = "░"
    show_percent: bool = True
    fill_style: Style = field(default_factory=lambda: Style().fg("#7D56F4"))
    empty_style: Style = field(default_factory=lambda: Style().dim())
    percent_style: Style = field(default_factory=lambda: Style().dim())

    def set_percent(self, percent: float) -> None:
        """Set completion percentage (clamped to 0.0-1.0)."""
        self.percent = max(0.0, min(1.0, percent))

    def view(self) -> str:
        """Render the progress bar."""
        pct = max(0.0, min(1.0, self.percent))

        # Reserve space for percentage text
        bar_width = self.width
        pct_text = ""
        if self.show_percent:
            pct_text = f" {pct * 100:.0f}%"
            bar_width = max(1, self.width - len(pct_text))

        filled = round(bar_width * pct)
        empty = bar_width - filled

        fill_str = self.fill_style.render(self.fill_char * filled)
        empty_str = self.empty_style.render(self.empty_char * empty)

        result = fill_str + empty_str
        if self.show_percent:
            result += self.percent_style.render(pct_text)

        return result
