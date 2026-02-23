"""Smoke test — styled text, quits on 'q'.

Run: python3 examples/hello.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pytea import (
    Program, Model, Cmd, Msg, WindowSizeMsg, KeyMsg, quit_cmd,
    Style, ROUNDED_BORDER, join_vertical, place, CENTER,
)


class HelloModel:
    def __init__(self):
        self.width = 80
        self.height = 24
        self.counter = 0

    def init(self) -> Cmd:
        return None

    def update(self, msg: Msg) -> tuple['HelloModel', Cmd]:
        if isinstance(msg, KeyMsg):
            if msg.key in ('q', 'ctrl+c'):
                return self, quit_cmd
            elif msg.key == 'up' or msg.key == 'k':
                self.counter += 1
            elif msg.key == 'down' or msg.key == 'j':
                self.counter -= 1
        elif isinstance(msg, WindowSizeMsg):
            self.width = msg.width
            self.height = msg.height
        return self, None

    def view(self) -> str:
        title_style = Style().bold().fg("#FAFAFA").bg("#7D56F4").padding(0, 1)
        border_style = Style().border(ROUNDED_BORDER).border_fg("#555555").padding(1, 2)
        help_style = Style().dim()

        title = title_style.render("pytea")
        counter = f"Counter: {self.counter}"
        help_text = help_style.render("j/k: change counter  q: quit")

        content = join_vertical(CENTER, title, "", counter, "", help_text)
        box = border_style.render(content)
        return place(self.width, self.height, 0.5, 0.4, box)


if __name__ == '__main__':
    model = HelloModel()
    p = Program(model)
    p.run()
