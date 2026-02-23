"""Paginated list with variable-height items and delegate rendering.

Equivalent to bubbles/list + bubbles/paginator.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from ..keys import KeyMsg
from ..model import Cmd


@runtime_checkable
class ItemDelegate(Protocol):
    """Renders list items. Equivalent to list.ItemDelegate in Bubble Tea."""

    def render(self, item: Any, width: int, selected: bool) -> str:
        """Render an item. Return a string (may contain newlines)."""
        ...

    def height(self, item: Any, width: int) -> int:
        """Return the number of lines this item occupies when rendered."""
        ...


class _DefaultDelegate:
    """Fallback delegate that renders items via str()."""

    def render(self, item: Any, width: int, selected: bool) -> str:
        prefix = "> " if selected else "  "
        return prefix + str(item)

    def height(self, item: Any, width: int) -> int:
        return 1


@dataclass
class List:
    """Paginated list component with variable-height items."""

    items: list = field(default_factory=list)
    cursor: int = 0
    delegate: ItemDelegate | None = None
    spacing: int = 0       # blank lines between items
    width: int = 80
    height: int = 24
    _page_start: int = 0

    def _get_delegate(self) -> ItemDelegate:
        return self.delegate or _DefaultDelegate()

    def set_items(self, items: list) -> None:
        """Replace the item list and clamp cursor."""
        self.items = items
        if self.cursor >= len(items):
            self.cursor = max(0, len(items) - 1)
        self._recalc_page()

    def selected_item(self) -> Any | None:
        """Return the currently selected item, or None if empty."""
        if not self.items or self.cursor < 0 or self.cursor >= len(self.items):
            return None
        return self.items[self.cursor]

    # ── Update ──

    def update(self, msg: Any) -> tuple['List', Cmd]:
        if not isinstance(msg, KeyMsg):
            return self, None

        key = msg.key
        if key in ('j', 'down'):
            if self.cursor < len(self.items) - 1:
                self.cursor += 1
                self._recalc_page()
        elif key in ('k', 'up'):
            if self.cursor > 0:
                self.cursor -= 1
                self._recalc_page()

        return self, None

    # ── View ──

    def view(self) -> str:
        """Render the visible page of items via delegate."""
        if not self.items:
            return ""

        delegate = self._get_delegate()
        self._recalc_page()

        ps = self._calc_page_size(self._page_start)
        page_end = min(self._page_start + ps, len(self.items))

        parts: list[str] = []
        for idx in range(self._page_start, page_end):
            if parts and self.spacing > 0:
                for _ in range(self.spacing):
                    parts.append("")
            item = self.items[idx]
            rendered = delegate.render(item, self.width, idx == self.cursor)
            parts.append(rendered)

        return "\n".join(parts)

    def pager_view(self) -> str:
        """Return pagination text like '1/3', or '' if only one page."""
        if not self.items:
            return ""

        pages = 0
        pos = 0
        current_page = 1
        while pos < len(self.items):
            ps = self._calc_page_size(pos)
            pages += 1
            if pos <= self._page_start < pos + ps:
                current_page = pages
            pos += ps

        if pages <= 1:
            return ""
        return f"{current_page}/{pages}"

    # ── Pagination internals ──

    def _calc_page_size(self, start: int) -> int:
        """How many items fit on one page starting at `start`."""
        delegate = self._get_delegate()
        avail = self.height
        if avail <= 0:
            return max(1, len(self.items))
        total = len(self.items)
        count = 0
        used = 0
        for i in range(start, total):
            h = delegate.height(self.items[i], self.width)
            # Add spacing between items (not before the first)
            if count > 0:
                h += self.spacing
            if used + h > avail and count > 0:
                break
            used += h
            count += 1
        return max(1, count)

    def _recalc_page(self) -> None:
        """Ensure _page_start is positioned so cursor is visible."""
        if not self.items:
            self._page_start = 0
            return

        idx = max(0, min(self.cursor, len(self.items) - 1))

        # If cursor is before current page, search forward from 0
        if idx < self._page_start:
            self._page_start = 0
            while self._page_start < idx:
                ps = self._calc_page_size(self._page_start)
                if self._page_start + ps > idx:
                    break
                self._page_start += ps

        # If cursor is past current page, advance page_start
        ps = self._calc_page_size(self._page_start)
        while idx >= self._page_start + ps:
            self._page_start += ps
            ps = self._calc_page_size(self._page_start)

        self._page_start = max(0, self._page_start)
