# pytea

A zero-dependency Python TUI framework that ports the [Charm](https://charm.sh) stack's approach to terminal UIs: the Elm Architecture, raw terminal I/O, and ANSI escape sequences.

## Why this exists

Python's TUI options are either curses-based (complex, stateful, platform-dependent) or heavy frameworks like Textual (hundreds of dependencies, CSS layout engine, async runtime). The Go ecosystem solved this with the Charm stack: a set of composable libraries that render TUIs by writing ANSI escape sequences directly to stdout. This makes rendering fast and the architecture simple -- your entire UI is a function that returns a string.

pytea brings that approach to Python:

- **No curses.** Reads raw bytes from stdin, writes ANSI sequences to stdout.
- **No dependencies.** Uses only the Python standard library (termios, select, signal, fcntl).
- **Elm Architecture.** Your app is `init()`, `update(msg)`, `view()` -- nothing else.
- **Fast rendering.** A line-diff renderer only redraws what changed, just like Bubble Tea.

## How the Elm Architecture works

```python
from pytea import Model, Cmd, KeyMsg, WindowSizeMsg, quit_cmd

class Counter:
    def __init__(self):
        self.count = 0

    def init(self) -> Cmd:
        return None

    def update(self, msg) -> tuple['Counter', Cmd]:
        if isinstance(msg, KeyMsg):
            if msg.key == 'q':
                return self, quit_cmd
            elif msg.key == 'up':
                self.count += 1
            elif msg.key == 'down':
                self.count -= 1
        return self, None

    def view(self) -> str:
        return f"Count: {self.count}\n\nup/down to change, q to quit"
```

The program calls `view()` after every `update()`, diffs the output, and writes only the changed lines. There's no widget tree, no layout engine, no virtual DOM -- just a string.

## Why escape sequences make this fast

Traditional TUI frameworks (curses, Textual) maintain an internal screen buffer and compute cell-by-cell diffs. pytea skips all of that:

1. **Your `view()` returns a string** with embedded ANSI codes for colors, bold, etc.
2. **The renderer splits it into lines** and compares against the previous frame.
3. **Only changed lines get written** using cursor-movement escape sequences.
4. **One `flush()` per frame** -- the terminal handles the rest.

Because ANSI rendering is done by the terminal emulator (which is GPU-accelerated in modern terminals like Ghostty, Kitty, WezTerm), the Python side only needs to produce and diff strings. There's no pixel math, no redraw-the-whole-screen, no intermediate buffer.

## What's ported from where

pytea combines features from four Charm libraries into one package. Here's what's implemented and what's not:

### Core Framework

| Feature | Charm Source | pytea | Status |
|---------|-------------|-------|--------|
| Elm Architecture (init/update/view) | bubbletea | `Model` protocol, `Program` | Done |
| Message types (Key, WindowSize, Quit) | bubbletea | `KeyMsg`, `WindowSizeMsg`, `QuitMsg` | Done |
| Command system (async Cmd) | bubbletea | `Cmd`, `batch()`, `quit_cmd` | Done |
| Raw terminal mode (termios) | bubbletea | `terminal.make_raw()` | Done |
| Alternate screen buffer | bubbletea | `Program(alt_screen=True)` | Done |
| Line-diff renderer | bubbletea | `renderer.Renderer` | Done |
| Keyboard input parsing (70+ sequences) | bubbletea | `keys.read_key()` | Done |
| SIGWINCH resize handling | bubbletea | `terminal.listen_for_resize()` | Done |
| Mouse input events | bubbletea | -- | Not yet |
| Bracketed paste events | bubbletea | -- | Not yet |
| Focus/blur events | bubbletea v2 | -- | Not yet |
| Kitty keyboard protocol | bubbletea v2 | -- | Not yet |
| Clipboard (OSC 52) | bubbletea v2 | -- | Not yet |
| Subscriptions (long-running listeners) | bubbletea | -- | Not yet |
| Suspend/resume (Ctrl+Z) | bubbletea | -- | Not yet |

### Styling

| Feature | Charm Source | pytea | Status |
|---------|-------------|-------|--------|
| Chainable style builder | lipgloss | `Style` class | Done |
| Text attributes (bold, dim, italic, underline, reverse, strikethrough) | lipgloss | `Style.bold()`, `.dim()`, etc. | Done |
| True color (24-bit RGB) | lipgloss | `Style.fg()`, `.bg()` | Done |
| Padding (CSS shorthand) | lipgloss | `Style.padding()` | Done |
| Margin (CSS shorthand) | lipgloss | `Style.margin()` | Done |
| Width/height constraints | lipgloss | `Style.width()`, `.height()` | Done |
| Max width/height | lipgloss | `Style.max_width()`, `.max_height()` | Done |
| Auto word-wrap on `.width()` | lipgloss | `Style._apply_wrap()` | Done |
| Borders (5 types, per-side, colored) | lipgloss | `Style.border()`, `.border_fg()` | Done |
| Horizontal alignment | lipgloss | `Style.align()` | Done |
| Immutable builder pattern | lipgloss | `Style._copy()` | Done |
| ANSI 16/256 color fallback | lipgloss | -- | Not yet |
| Adaptive colors (light/dark) | lipgloss | -- | Not yet |
| Vertical alignment | lipgloss | -- | Not yet |
| Tab width | lipgloss | -- | Not yet |
| Table rendering | lipgloss/table | -- | Not yet |
| List rendering (enumerators) | lipgloss/list | -- | Not yet |
| Tree rendering | lipgloss/tree | -- | Not yet |

### Layout

| Feature | Charm Source | pytea | Status |
|---------|-------------|-------|--------|
| Join blocks horizontally | lipgloss | `join_horizontal()` | Done |
| Join blocks vertically | lipgloss | `join_vertical()` | Done |
| Place content in canvas (2D) | lipgloss | `place()` | Done |
| PlaceHorizontal / PlaceVertical | lipgloss | -- | Not yet |

### String Utilities

| Feature | Charm Source | pytea | Status |
|---------|-------------|-------|--------|
| ANSI-aware visible width | x/ansi | `strutil.visible_width()` | Done |
| ANSI stripping | x/ansi | `strutil.strip_ansi()` | Done |
| ANSI-aware truncation | x/ansi | `strutil.truncate()` | Done |
| ANSI-aware word wrap | x/ansi | `strutil.word_wrap()` | Done |
| ANSI-aware padding | x/ansi | `strutil.pad_right()` | Done |
| CJK wide character support | x/ansi | `strutil._char_width()` | Done |
| Grapheme cluster segmentation | x/ansi | -- | Not yet |
| Hard wrap (non-word-boundary) | x/ansi | -- | Not yet (hard-break exists within word_wrap) |
| Truncate with tail ("...") | x/ansi | -- | Not yet |

### Components

| Component | Charm Source | pytea | Status |
|-----------|-------------|-------|--------|
| Single-line text input | bubbles/textinput | `TextInput` | Done |
| Multi-line text area | bubbles/textarea | `TextArea` | Done |
| Scrollable viewport | bubbles/viewport | `Viewport` | Done |
| Paginated list (delegate pattern) | bubbles/list + bubbles/paginator | `List` | Done |
| Option picker (select) | bubbles/list | `Select` | Done |
| Yes/No confirmation | huh | `Confirm` | Done |
| Multi-field form | huh | `Form` | Done |
| Table | bubbles/table | -- | Not yet |
| Spinner | bubbles/spinner | -- | Not yet |
| Progress bar | bubbles/progress | -- | Not yet |
| File picker | bubbles/filepicker | -- | Not yet |
| Timer / Stopwatch | bubbles/timer, bubbles/stopwatch | -- | Not yet |
| Help (auto-generated keybinds) | bubbles/help | -- | Not yet |

### Legend

- **Done** -- Implemented and tested
- **Not yet** -- Not implemented; listed here so future apps know what to add when they need it

## Architecture

```
your_app.py
    |
    +-- pytea (framework + styling + components in one package)
            |
            +-- model.py        Elm Architecture: Model protocol, Msg, Cmd
            +-- keys.py         Keyboard input: escape sequence parser
            +-- program.py      Event loop: raw mode, resize, render cycle
            +-- terminal.py     Low-level: termios, ioctl, ANSI sequences
            +-- renderer.py     Line-diff screen updates
            +-- style.py        Lip Gloss equivalent: chainable styling
            +-- strutil.py      ANSI-aware string ops: width, wrap, truncate
            +-- layout.py       join_horizontal, join_vertical, place
            +-- components/
                    +-- textinput.py   Single-line input
                    +-- textarea.py    Multi-line editor
                    +-- viewport.py    Scrollable content
                    +-- list.py        Paginated list with delegates
                    +-- select.py      Option picker
                    +-- confirm.py     Yes/No prompt
                    +-- form.py        Multi-field form
```

In Go, these are spread across four repos (bubbletea, lipgloss, bubbles, x/ansi). pytea combines them because Python apps can just import what they need from one package.

## Running tests

```
python3 -m pytest
```
