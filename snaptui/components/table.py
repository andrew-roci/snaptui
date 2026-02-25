"""Table component — column-aligned data display.

Equivalent to bubbles/table. Renders data in aligned columns with
optional headers, row selection, and scrolling.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..keys import KeyMsg
from ..model import Cmd, Msg
from ..style import Style
from .. import strutil


@dataclass(frozen=True, slots=True)
class Column:
    """Column definition for a table.

    Attributes:
        title: Column header text.
        width: Fixed width (0 = auto-fit to content).
    """
    title: str
    width: int = 0


@dataclass
class Table:
    """Column-aligned data table with optional selection and scrolling.

    Attributes:
        columns: Column definitions.
        rows: List of rows, each row is a list of strings matching columns.
        cursor: Currently selected row index (-1 = no selection).
        height: Max visible rows (0 = show all).
        y_offset: Scroll offset for tall tables.
        focused: Whether the table accepts keyboard input.
        header_style: Style for the header row.
        selected_style: Style for the selected row.
        cell_style: Style for normal cells.
    """
    columns: list[Column] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    cursor: int = -1
    height: int = 0
    y_offset: int = 0
    focused: bool = False
    header_style: Style = field(default_factory=lambda: Style().bold())
    selected_style: Style = field(default_factory=lambda: Style().reverse())
    cell_style: Style = field(default_factory=Style)

    def _col_widths(self) -> list[int]:
        """Compute effective column widths."""
        widths: list[int] = []
        for i, col in enumerate(self.columns):
            if col.width > 0:
                widths.append(col.width)
            else:
                # Auto-fit: max of header and all row values
                w = strutil.visible_width(col.title)
                for row in self.rows:
                    if i < len(row):
                        w = max(w, strutil.visible_width(row[i]))
                widths.append(w)
        return widths

    def selected_row(self) -> list[str] | None:
        """Return the currently selected row, or None."""
        if 0 <= self.cursor < len(self.rows):
            return self.rows[self.cursor]
        return None

    def focus(self) -> None:
        self.focused = True
        if self.cursor < 0 and self.rows:
            self.cursor = 0

    def blur(self) -> None:
        self.focused = False

    def update(self, msg: Msg) -> tuple['Table', Cmd]:
        if not self.focused or not isinstance(msg, KeyMsg):
            return self, None

        key = msg.key
        if key in ('j', 'down'):
            if self.cursor < len(self.rows) - 1:
                self.cursor += 1
                self._ensure_visible()
        elif key in ('k', 'up'):
            if self.cursor > 0:
                self.cursor -= 1
                self._ensure_visible()

        return self, None

    def _ensure_visible(self) -> None:
        """Scroll so cursor is visible."""
        if self.height <= 0:
            return
        if self.cursor < self.y_offset:
            self.y_offset = self.cursor
        elif self.cursor >= self.y_offset + self.height:
            self.y_offset = self.cursor - self.height + 1

    def view(self) -> str:
        if not self.columns:
            return ""

        widths = self._col_widths()
        gap = "  "

        lines: list[str] = []

        # Header
        header_cells: list[str] = []
        for i, col in enumerate(self.columns):
            cell = strutil.pad_right(col.title, widths[i])
            header_cells.append(cell)
        header_line = gap.join(header_cells)
        lines.append(self.header_style.render(header_line))

        # Separator
        sep_parts = ["\u2500" * w for w in widths]
        lines.append(gap.join(sep_parts))

        # Rows (with scrolling)
        visible_rows = self.rows
        start = 0
        if self.height > 0 and len(self.rows) > self.height:
            start = self.y_offset
            visible_rows = self.rows[start:start + self.height]

        for row_idx, row in enumerate(visible_rows):
            actual_idx = start + row_idx
            cells: list[str] = []
            for i in range(len(self.columns)):
                val = row[i] if i < len(row) else ""
                cell = strutil.pad_right(strutil.truncate(val, widths[i]), widths[i])
                cells.append(cell)
            line = gap.join(cells)
            if actual_idx == self.cursor:
                lines.append(self.selected_style.render(line))
            else:
                lines.append(self.cell_style.render(line))

        return "\n".join(lines)
