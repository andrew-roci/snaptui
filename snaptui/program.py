"""Event loop — port of Bubble Tea's Program.

Ties together terminal, keys, model, and renderer.
"""

from __future__ import annotations

import os
import signal
import sys
import threading
from queue import Empty, Queue

from . import keys
from . import terminal
from .model import Cmd, Model, Msg, QuitMsg, Sub, View, WindowSizeMsg, batch
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
        bracketed_paste: bool = False,
    ) -> None:
        self.model = model
        self._alt_screen = alt_screen
        self._mouse = mouse
        self._bracketed_paste = bracketed_paste
        self._quit = False
        self._queue: Queue[Msg] = Queue()
        self._renderer = Renderer()
        self._width = 80
        self._height = 24
        self._prev_view: View | None = None
        self._active_subs: dict[str, callable] = {}  # key -> stop()
        self._fd: int | None = None
        self._old_state: list | None = None

    def run(self) -> Model:
        """Run the program. Blocks until quit. Returns final model."""
        fd = sys.stdin.fileno()
        self._fd = fd
        old_state = terminal.make_raw(fd)
        self._old_state = old_state

        try:
            # Enter alt screen, hide cursor
            setup = ''
            if self._alt_screen:
                setup += terminal.ALT_SCREEN_ON
            setup += terminal.HIDE_CURSOR
            if self._mouse:
                setup += terminal.ENABLE_MOUSE
            if self._bracketed_paste:
                setup += terminal.ENABLE_BRACKETED_PASTE
            terminal.write(setup)

            # Get initial size
            self._width, self._height = terminal.get_size()
            self._process(WindowSizeMsg(self._width, self._height))

            # Listen for resize
            terminal.listen_for_resize(self._on_resize)

            # Handle Ctrl+Z (suspend/resume)
            self._install_suspend_handler()

            # Run init cmd
            init_cmd = self.model.init()
            self._exec_cmd(init_cmd)

            # Start initial subscriptions
            self._sync_subs()

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
            # Stop all subscriptions
            self._stop_all_subs()

            # Teardown
            teardown = terminal.SHOW_CURSOR
            if self._mouse:
                teardown += terminal.DISABLE_MOUSE
            if self._bracketed_paste:
                teardown += terminal.DISABLE_BRACKETED_PASTE
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

        # Handle Ctrl+Z: trigger SIGTSTP for suspend
        if isinstance(msg, keys.KeyMsg) and msg.key == 'ctrl+z':
            os.kill(os.getpid(), signal.SIGTSTP)
            return

        if isinstance(msg, WindowSizeMsg):
            self._width = msg.width
            self._height = msg.height
            self._renderer.repaint()

        new_model, cmd = self.model.update(msg)
        self.model = new_model
        self._exec_cmd(cmd)
        self._sync_subs()
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

    def _sync_subs(self) -> None:
        """Start/stop subscriptions to match model.subscriptions()."""
        if not hasattr(self.model, 'subscriptions'):
            return

        desired = self.model.subscriptions()
        desired_keys = {s.key for s in desired}

        # Stop removed subscriptions
        for key in list(self._active_subs):
            if key not in desired_keys:
                self._active_subs[key]()
                del self._active_subs[key]

        # Start new subscriptions
        for sub in desired:
            if sub.key not in self._active_subs:
                stop = sub.start(self.send)
                self._active_subs[sub.key] = stop

    def _stop_all_subs(self) -> None:
        """Stop all active subscriptions."""
        for stop in self._active_subs.values():
            stop()
        self._active_subs.clear()

    def _render(self) -> None:
        """Render the current model view."""
        result = self.model.view()
        if isinstance(result, View):
            view = result
        else:
            view = View(content=result, alt_screen=self._alt_screen)
        self._apply_terminal_state(view)
        self._renderer.render(view.content, self._width, self._height, cursor=view.cursor)
        self._prev_view = view

    def _apply_terminal_state(self, view: View) -> None:
        """Diff View terminal fields against previous frame and emit changes."""
        prev = self._prev_view
        buf = ''
        # Alt screen toggle
        if prev is not None and view.alt_screen != prev.alt_screen:
            buf += terminal.ALT_SCREEN_ON if view.alt_screen else terminal.ALT_SCREEN_OFF
        # Window title
        if view.window_title is not None:
            if prev is None or view.window_title != prev.window_title:
                buf += terminal.set_window_title(view.window_title)
        if buf:
            terminal.write(buf)

    def _install_suspend_handler(self) -> None:
        """Install SIGTSTP handler for Ctrl+Z suspend/resume."""
        def on_suspend(signum, frame):
            # Restore terminal to normal state
            teardown = terminal.SHOW_CURSOR
            if self._mouse:
                teardown += terminal.DISABLE_MOUSE
            if self._bracketed_paste:
                teardown += terminal.DISABLE_BRACKETED_PASTE
            if self._alt_screen:
                teardown += terminal.ALT_SCREEN_OFF
            terminal.write(teardown)
            if self._fd is not None and self._old_state is not None:
                terminal.restore(self._fd, self._old_state)

            # Reset SIGTSTP to default and re-raise to actually suspend
            signal.signal(signal.SIGTSTP, signal.SIG_DFL)
            os.kill(os.getpid(), signal.SIGTSTP)

        def on_resume(signum, frame):
            # Re-enter raw mode
            if self._fd is not None:
                self._old_state = terminal.make_raw(self._fd)

            # Restore terminal state
            setup = ''
            if self._alt_screen:
                setup += terminal.ALT_SCREEN_ON
            setup += terminal.HIDE_CURSOR
            if self._mouse:
                setup += terminal.ENABLE_MOUSE
            if self._bracketed_paste:
                setup += terminal.ENABLE_BRACKETED_PASTE
            terminal.write(setup)

            # Re-install suspend handler (was reset to SIG_DFL)
            signal.signal(signal.SIGTSTP, on_suspend)

            # Force repaint and get new size
            self._width, self._height = terminal.get_size()
            self._renderer.repaint()
            self._queue.put(WindowSizeMsg(self._width, self._height))

        signal.signal(signal.SIGTSTP, on_suspend)
        signal.signal(signal.SIGCONT, on_resume)

    def send(self, msg: Msg) -> None:
        """Send a message to the program from outside (thread-safe)."""
        self._queue.put(msg)

    def quit(self) -> None:
        """Signal the program to quit."""
        self._quit = True
