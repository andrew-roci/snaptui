"""Event loop — port of Bubble Tea's Program.

Ties together terminal, keys, model, and renderer.
"""

from __future__ import annotations

import os
import sys
import threading
from queue import Empty, Queue

from . import keys
from . import terminal
from .model import Cmd, Model, Msg, QuitMsg, WindowSizeMsg, batch
from .renderer import Renderer


class Program:
    """Runs a Bubble Tea-style application.

    Usage:
        model = MyModel()
        p = Program(model)
        final_model = p.run()
    """

    def __init__(
        self,
        model: Model,
        *,
        alt_screen: bool = True,
        mouse: bool = False,
    ) -> None:
        self.model = model
        self._alt_screen = alt_screen
        self._mouse = mouse
        self._quit = False
        self._queue: Queue[Msg] = Queue()
        self._renderer = Renderer()
        self._width = 80
        self._height = 24

    def run(self) -> Model:
        """Run the program. Blocks until quit. Returns final model."""
        fd = sys.stdin.fileno()
        old_state = terminal.make_raw(fd)

        try:
            # Enter alt screen, hide cursor
            setup = ''
            if self._alt_screen:
                setup += terminal.ALT_SCREEN_ON
            setup += terminal.HIDE_CURSOR
            if self._mouse:
                setup += terminal.ENABLE_MOUSE
            terminal.write(setup)

            # Get initial size
            self._width, self._height = terminal.get_size()
            self._process(WindowSizeMsg(self._width, self._height))

            # Listen for resize
            terminal.listen_for_resize(self._on_resize)

            # Run init cmd
            init_cmd = self.model.init()
            self._exec_cmd(init_cmd)

            # Initial render
            self._render()

            # Main loop
            while not self._quit:
                # Read keyboard (with timeout for queue checking)
                key_msg = keys.read_key(fd, timeout=0.02)
                if key_msg:
                    self._process(key_msg)

                # Drain async message queue
                self._drain_queue()

        finally:
            # Teardown
            teardown = terminal.SHOW_CURSOR
            if self._mouse:
                teardown += terminal.DISABLE_MOUSE
            if self._alt_screen:
                teardown += terminal.ALT_SCREEN_OFF
            terminal.write(teardown)
            terminal.restore(fd, old_state)

        return self.model

    def _on_resize(self, width: int, height: int) -> None:
        """Called from SIGWINCH handler."""
        self._queue.put(WindowSizeMsg(width, height))

    def _process(self, msg: Msg) -> None:
        """Send a message through update, handle result."""
        if isinstance(msg, QuitMsg):
            self._quit = True
            return

        if isinstance(msg, WindowSizeMsg):
            self._width = msg.width
            self._height = msg.height
            self._renderer.repaint()

        new_model, cmd = self.model.update(msg)
        self.model = new_model
        self._exec_cmd(cmd)
        self._render()

    def _exec_cmd(self, cmd: Cmd) -> None:
        """Execute a command, feeding result back as a message."""
        if cmd is None:
            return

        def run():
            result = cmd()
            if result is not None:
                if isinstance(result, list):
                    # batch() returns a list of messages
                    for msg in result:
                        self._queue.put(msg)
                else:
                    self._queue.put(result)

        t = threading.Thread(target=run, daemon=True)
        t.start()

    def _drain_queue(self) -> None:
        """Process all pending messages from the async queue."""
        while True:
            try:
                msg = self._queue.get_nowait()
                self._process(msg)
            except Empty:
                break

    def _render(self) -> None:
        """Render the current model view."""
        output = self.model.view()
        self._renderer.render(output, self._width, self._height)

    def send(self, msg: Msg) -> None:
        """Send a message to the program from outside (thread-safe)."""
        self._queue.put(msg)

    def quit(self) -> None:
        """Signal the program to quit."""
        self._quit = True
