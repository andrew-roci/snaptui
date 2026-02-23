"""Form component — groups fields with Tab navigation.

Equivalent to huh Form. Groups TextInput, Select, Confirm fields
with Tab/Shift+Tab navigation between them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..keys import KeyMsg
from ..model import Cmd, Msg
from ..style import Style


@dataclass
class FormField:
    """Wrapper for a field in the form."""
    component: Any  # TextInput, Select, Confirm, etc.
    key: str = ''  # Identifier for retrieving values


@dataclass
class Form:
    """Tab-navigable form grouping multiple input fields.

    Attributes:
        fields: List of FormField wrappers
        focused_index: Currently focused field index
        submitted: Whether the form has been submitted
        cancelled: Whether the form was cancelled
    """
    fields: list[FormField] = field(default_factory=list)
    focused_index: int = 0
    submitted: bool = False
    cancelled: bool = False
    _title: str = ''

    # Styles
    title_style: Style | None = None

    def title(self, text: str) -> 'Form':
        self._title = text
        return self

    def add_field(self, component: Any, key: str = '') -> 'Form':
        """Add a field to the form."""
        self.fields.append(FormField(component=component, key=key))
        return self

    def focus_field(self, index: int) -> None:
        """Focus a specific field by index."""
        if self.fields:
            # Blur current
            if 0 <= self.focused_index < len(self.fields):
                self.fields[self.focused_index].component.blur()
            # Focus new
            self.focused_index = max(0, min(index, len(self.fields) - 1))
            self.fields[self.focused_index].component.focus()

    def init(self) -> None:
        """Initialize form — focus first field."""
        if self.fields:
            self.focused_index = 0
            self.fields[0].component.focus()

    def next_field(self) -> None:
        """Move focus to next field."""
        if self.focused_index < len(self.fields) - 1:
            self.focus_field(self.focused_index + 1)

    def prev_field(self) -> None:
        """Move focus to previous field."""
        if self.focused_index > 0:
            self.focus_field(self.focused_index - 1)

    def get_value(self, key: str) -> Any:
        """Get value of a field by key."""
        for f in self.fields:
            if f.key == key:
                comp = f.component
                if hasattr(comp, 'value'):
                    return comp.value
        return None

    def get_values(self) -> dict[str, Any]:
        """Get all field values as a dict."""
        result: dict[str, Any] = {}
        for f in self.fields:
            if f.key:
                comp = f.component
                if hasattr(comp, 'value'):
                    result[f.key] = comp.value
        return result

    def update(self, msg: Msg) -> tuple['Form', Cmd]:
        if self.submitted or self.cancelled:
            return self, None

        if isinstance(msg, KeyMsg):
            key = msg.key

            # Form-level navigation
            if key == 'tab':
                self.next_field()
                return self, None
            elif key == 'shift+tab':
                self.prev_field()
                return self, None
            elif key == 'ctrl+c' or key == 'esc':
                self.cancelled = True
                return self, None
            elif key == 'enter':
                # If on last field, submit
                if self.focused_index == len(self.fields) - 1:
                    self.submitted = True
                    return self, None
                # Otherwise move to next field
                self.next_field()
                return self, None

        # Delegate to focused field
        if 0 <= self.focused_index < len(self.fields):
            comp = self.fields[self.focused_index].component
            comp, cmd = comp.update(msg)
            self.fields[self.focused_index].component = comp
            return self, cmd

        return self, None

    def view(self) -> str:
        lines: list[str] = []

        if self._title:
            t = self._title
            if self.title_style:
                t = self.title_style.render(t)
            lines.append(t)
            lines.append('')

        for i, f in enumerate(self.fields):
            field_view = f.component.view()
            lines.append(field_view)
            if i < len(self.fields) - 1:
                lines.append('')  # spacing between fields

        return '\n'.join(lines)
