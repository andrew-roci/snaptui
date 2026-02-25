"""Spinner component — animated loading indicator.

Equivalent to bubbles/spinner. Driven by TickMsg through the Elm
architecture command loop.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from ..model import Cmd, Msg


@dataclass(frozen=True, slots=True)
class SpinnerTickMsg:
    """Sent by the spinner's tick command to advance the frame."""
    tag: int = 0


# ── Built-in spinner styles ──

SPINNER_LINE = ["|", "/", "-", "\\"]
SPINNER_DOTS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
SPINNER_ELLIPSIS = ["   ", ".  ", ".. ", "..."]
SPINNER_JUMP = ["⢄", "⢂", "⢁", "⡁", "⡈", "⡐", "⡠"]
SPINNER_PULSE = ["█", "▓", "▒", "░", "▒", "▓"]
SPINNER_POINTS = ["∙∙∙", "●∙∙", "∙●∙", "∙∙●"]
SPINNER_METER = ["▱▱▱", "▰▱▱", "▰▰▱", "▰▰▰", "▰▰▱", "▰▱▱"]
SPINNER_MINI_DOT = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


@dataclass
class Spinner:
    """Animated spinner component.

    Usage:
        spinner = Spinner()
        # In your init(), return spinner.tick() to start animation.
        # In your update(), handle SpinnerTickMsg to advance frames.

    Attributes:
        frames: Animation frame characters.
        fps: Frames per second (controls tick interval).
        frame: Current frame index.
        tag: Unique tag to distinguish multiple spinners.
    """
    frames: list[str] = field(default_factory=lambda: list(SPINNER_DOTS))
    fps: float = 10.0
    frame: int = 0
    tag: int = 0

    def tick(self) -> Cmd:
        """Return a command that sleeps then sends a SpinnerTickMsg."""
        interval = 1.0 / self.fps if self.fps > 0 else 0.1
        tag = self.tag

        def _tick() -> SpinnerTickMsg:
            time.sleep(interval)
            return SpinnerTickMsg(tag=tag)

        return _tick

    def update(self, msg: Msg) -> tuple['Spinner', Cmd]:
        """Handle SpinnerTickMsg to advance the frame."""
        if isinstance(msg, SpinnerTickMsg) and msg.tag == self.tag:
            self.frame = (self.frame + 1) % len(self.frames)
            return self, self.tick()
        return self, None

    def view(self) -> str:
        """Render the current spinner frame."""
        if not self.frames:
            return ""
        return self.frames[self.frame % len(self.frames)]
