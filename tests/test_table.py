"""Tests for the Table component."""

from snaptui.components.table import Table, Column
from snaptui.keys import KeyMsg
from snaptui.strutil import visible_width, strip_ansi


class TestTableView:
    def test_empty_columns(self):
        t = Table(columns=[], rows=[])
        assert t.view() == ""

    def test_header_only(self):
        t = Table(columns=[Column("Name"), Column("Value")], rows=[])
        result = t.view()
        lines = result.split("\n")
        assert len(lines) == 2  # header + separator
        assert "Name" in strip_ansi(lines[0])
        assert "Value" in strip_ansi(lines[0])

    def test_with_rows(self):
        t = Table(
            columns=[Column("Key"), Column("Value")],
            rows=[["foo", "bar"], ["baz", "qux"]],
        )
        result = t.view()
        lines = result.split("\n")
        assert len(lines) == 4  # header + sep + 2 rows
        assert "foo" in strip_ansi(lines[2])
        assert "bar" in strip_ansi(lines[2])

    def test_column_alignment(self):
        t = Table(
            columns=[Column("K"), Column("V")],
            rows=[["short", "AAA"], ["longer_key", "BBB"]],
        )
        result = t.view()
        lines = result.split("\n")
        # All rows should have consistent column alignment
        plain_lines = [strip_ansi(l) for l in lines]
        # Values in column 2 should be at the same position
        val_positions = []
        for line in plain_lines[2:]:
            if "AAA" in line:
                val_positions.append(line.index("AAA"))
            elif "BBB" in line:
                val_positions.append(line.index("BBB"))
        assert len(val_positions) == 2
        assert len(set(val_positions)) == 1  # Same position

    def test_fixed_width_columns(self):
        t = Table(
            columns=[Column("Name", width=10), Column("Value", width=5)],
            rows=[["hello world this is long", "ok"]],
        )
        result = t.view()
        # Should not crash, long values get truncated
        assert "hello" in strip_ansi(result)


class TestTableNavigation:
    def test_move_down(self):
        t = Table(
            columns=[Column("A")],
            rows=[["1"], ["2"], ["3"]],
            cursor=0,
            focused=True,
        )
        t, _ = t.update(KeyMsg("j"))
        assert t.cursor == 1

    def test_move_up(self):
        t = Table(
            columns=[Column("A")],
            rows=[["1"], ["2"], ["3"]],
            cursor=1,
            focused=True,
        )
        t, _ = t.update(KeyMsg("k"))
        assert t.cursor == 0

    def test_no_move_past_end(self):
        t = Table(
            columns=[Column("A")],
            rows=[["1"], ["2"]],
            cursor=1,
            focused=True,
        )
        t, _ = t.update(KeyMsg("j"))
        assert t.cursor == 1

    def test_no_move_past_start(self):
        t = Table(
            columns=[Column("A")],
            rows=[["1"], ["2"]],
            cursor=0,
            focused=True,
        )
        t, _ = t.update(KeyMsg("k"))
        assert t.cursor == 0

    def test_unfocused_ignores_keys(self):
        t = Table(
            columns=[Column("A")],
            rows=[["1"], ["2"]],
            cursor=0,
            focused=False,
        )
        t, _ = t.update(KeyMsg("j"))
        assert t.cursor == 0

    def test_selected_row(self):
        t = Table(
            columns=[Column("A")],
            rows=[["1"], ["2"]],
            cursor=1,
        )
        assert t.selected_row() == ["2"]

    def test_selected_row_none(self):
        t = Table(columns=[Column("A")], rows=[])
        assert t.selected_row() is None


class TestTableScrolling:
    def test_scroll_when_height_set(self):
        t = Table(
            columns=[Column("A")],
            rows=[["1"], ["2"], ["3"], ["4"], ["5"]],
            cursor=0,
            height=2,
            focused=True,
        )
        # Move to last item
        for _ in range(4):
            t, _ = t.update(KeyMsg("j"))
        assert t.cursor == 4
        assert t.y_offset > 0
