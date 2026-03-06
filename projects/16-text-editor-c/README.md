# Build your own Text Editor (C, from scratch)

Minimal terminal text editor using POSIX raw mode and ANSI rendering.

## Features

- Raw terminal mode via `termios`
- Byte-level key input (arrows, page keys, backspace, delete)
- In-memory text rows with insert/delete/newline editing
- Full-screen redraw loop using ANSI escapes
- Open file on startup and save with `Ctrl-S`

## Build

```bash
cd projects/16-text-editor-c
gcc -std=c11 -O2 -Wall -Wextra -pedantic -o text-editor main.c
```

## Run

```bash
./text-editor
./text-editor notes.txt
```

## Controls

- `Ctrl-S`: save
- `Ctrl-Q`: quit
- Arrow keys, Home/End, PageUp/PageDown
- Enter, Backspace, Delete
