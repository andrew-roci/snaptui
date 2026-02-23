"""Tests for the List component — paginated list with delegate rendering."""

from pytea.components.list import List, ItemDelegate
from pytea.keys import KeyMsg


class SimpleDelegate:
    """Single-line delegate for testing."""

    def render(self, item, width, selected):
        prefix = "> " if selected else "  "
        return prefix + str(item)

    def height(self, item, width):
        return 1


class MultiLineDelegate:
    """Variable-height delegate for testing."""

    def render(self, item, width, selected):
        lines = [f"Name: {item['name']}"]
        if item.get("desc"):
            lines.append(f"  {item['desc']}")
        return "\n".join(lines)

    def height(self, item, width):
        return 2 if item.get("desc") else 1


class TestListNavigation:
    def test_move_down(self):
        lst = List(items=["a", "b", "c"], delegate=SimpleDelegate())
        assert lst.cursor == 0
        lst, _ = lst.update(KeyMsg("j"))
        assert lst.cursor == 1

    def test_move_up(self):
        lst = List(items=["a", "b", "c"], cursor=2, delegate=SimpleDelegate())
        lst, _ = lst.update(KeyMsg("k"))
        assert lst.cursor == 1

    def test_no_move_past_start(self):
        lst = List(items=["a", "b"], cursor=0, delegate=SimpleDelegate())
        lst, _ = lst.update(KeyMsg("k"))
        assert lst.cursor == 0

    def test_no_move_past_end(self):
        lst = List(items=["a", "b"], cursor=1, delegate=SimpleDelegate())
        lst, _ = lst.update(KeyMsg("j"))
        assert lst.cursor == 1

    def test_arrow_keys(self):
        lst = List(items=["a", "b", "c"], delegate=SimpleDelegate())
        lst, _ = lst.update(KeyMsg("down"))
        assert lst.cursor == 1
        lst, _ = lst.update(KeyMsg("up"))
        assert lst.cursor == 0


class TestListPagination:
    def test_single_page(self):
        lst = List(items=["a", "b", "c"], height=10, delegate=SimpleDelegate())
        assert lst.pager_view() == ""

    def test_multiple_pages(self):
        lst = List(items=list(range(10)), height=3, delegate=SimpleDelegate())
        pager = lst.pager_view()
        assert pager == "1/4"

    def test_page_advances_on_nav(self):
        lst = List(items=list(range(10)), height=3, delegate=SimpleDelegate())
        # Move to item 3 (past first page of 3 items)
        for _ in range(3):
            lst, _ = lst.update(KeyMsg("j"))
        pager = lst.pager_view()
        assert pager.startswith("2/")

    def test_page_goes_back(self):
        lst = List(items=list(range(10)), height=3, cursor=5, delegate=SimpleDelegate())
        # Move back past page start
        for _ in range(5):
            lst, _ = lst.update(KeyMsg("k"))
        assert lst.cursor == 0
        pager = lst.pager_view()
        assert pager == "" or pager.startswith("1/")


class TestListDelegateRendering:
    def test_default_delegate(self):
        lst = List(items=["hello"], height=10)
        view = lst.view()
        assert "> hello" in view

    def test_custom_delegate(self):
        lst = List(items=["a", "b"], delegate=SimpleDelegate(), height=10)
        view = lst.view()
        assert "> a" in view
        assert "  b" in view

    def test_multiline_delegate(self):
        items = [
            {"name": "Alice", "desc": "Engineer"},
            {"name": "Bob", "desc": "Designer"},
        ]
        lst = List(items=items, delegate=MultiLineDelegate(), height=10)
        view = lst.view()
        assert "Name: Alice" in view
        assert "Engineer" in view

    def test_variable_height_pagination(self):
        items = [
            {"name": f"Item {i}", "desc": f"Desc {i}"}
            for i in range(10)
        ]
        # Each item is 2 lines, height=5 fits ~2 items
        lst = List(items=items, delegate=MultiLineDelegate(), height=5)
        pager = lst.pager_view()
        assert "/" in pager  # Multiple pages


class TestListEmpty:
    def test_empty_view(self):
        lst = List(items=[], delegate=SimpleDelegate())
        assert lst.view() == ""

    def test_empty_pager(self):
        lst = List(items=[], delegate=SimpleDelegate())
        assert lst.pager_view() == ""

    def test_empty_selected_item(self):
        lst = List(items=[], delegate=SimpleDelegate())
        assert lst.selected_item() is None


class TestListSetItems:
    def test_set_items(self):
        lst = List(items=["a"], cursor=0, delegate=SimpleDelegate())
        lst.set_items(["x", "y", "z"])
        assert lst.items == ["x", "y", "z"]
        assert lst.cursor == 0

    def test_set_items_clamps_cursor(self):
        lst = List(items=["a", "b", "c"], cursor=2, delegate=SimpleDelegate())
        lst.set_items(["x"])
        assert lst.cursor == 0

    def test_selected_item(self):
        lst = List(items=["a", "b", "c"], cursor=1, delegate=SimpleDelegate())
        assert lst.selected_item() == "b"


class TestListSpacing:
    def test_spacing_between_items(self):
        lst = List(items=["a", "b", "c"], spacing=1, height=100, delegate=SimpleDelegate())
        view = lst.view()
        lines = view.split("\n")
        # With spacing=1: item, blank, item, blank, item = 5 lines
        assert len(lines) == 5
