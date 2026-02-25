"""Model protocol, Msg/Cmd types — Elm Architecture core types.

Equivalent to Bubble Tea's tea.Model, tea.Msg, tea.Cmd.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol, runtime_checkable


# ── Message types ─────────────────────────────────────────────────────────────

# Msg is any object — KeyMsg, WindowSizeMsg, custom messages, etc.
# Using a type alias for documentation purposes.
Msg = Any


@dataclass(frozen=True, slots=True)
class WindowSizeMsg:
    """Sent when the terminal is resized."""
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class QuitMsg:
    """Sent to signal the program should exit."""
    pass


@dataclass(frozen=True, slots=True)
class CursorBlinkMsg:
    """Sent by TextInput to toggle cursor visibility."""
    tag: int = 0


# ── View struct ───────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class View:
    """Declarative view returned by model.view().

    Attributes:
        content: The rendered string content.
        cursor: Hardware cursor position (row, col) relative to content, or None to hide.
        alt_screen: Whether to use the alternate screen buffer.
        window_title: Terminal window title (OSC 2), or None to leave unchanged.
    """
    content: str
    cursor: tuple[int, int] | None = None
    alt_screen: bool = True
    window_title: str | None = None


# ── Command types ─────────────────────────────────────────────────────────────

# A Cmd is a callable that returns a Msg (or None).
# It runs asynchronously — the returned Msg is fed back into update().
Cmd = Callable[[], Msg | None] | None


def quit_cmd() -> Msg:
    """Command that causes the program to quit."""
    return QuitMsg()


def batch(*cmds: Cmd) -> Cmd:
    """Combine multiple commands into one. They run sequentially."""
    filtered = [c for c in cmds if c is not None]
    if not filtered:
        return None
    if len(filtered) == 1:
        return filtered[0]

    def run() -> list[Msg]:
        msgs = []
        for cmd in filtered:
            result = cmd()
            if result is not None:
                msgs.append(result)
        return msgs if msgs else None
    return run


# ── Model protocol ───────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class Sub:
    """A subscription declaration returned by Model.subscriptions().

    Attributes:
        key: Unique identifier for this subscription.
        start: Callable that starts the subscription.
               Receives a send(msg) callback; returns a stop() callable.
    """
    key: str
    start: Callable[[Callable[[Msg], None]], Callable[[], None]]


@runtime_checkable
class Model(Protocol):
    """Protocol for Bubble Tea-style models.

    Models implement the Elm Architecture:
    - init() -> Cmd: Called once at startup, returns initial command
    - update(msg) -> tuple[Model, Cmd]: Handle a message, return new state + command
    - view() -> str: Render current state as a string
    - subscriptions() -> list[Sub]: Declare background listeners (optional)
    """

    def init(self) -> Cmd:
        """Called once when the program starts. Return an initial Cmd or None."""
        ...

    def update(self, msg: Msg) -> tuple['Model', Cmd]:
        """Handle a message. Return (new_model, cmd)."""
        ...

    def view(self) -> str | View:
        """Render the current state as a string or View for display."""
        ...
