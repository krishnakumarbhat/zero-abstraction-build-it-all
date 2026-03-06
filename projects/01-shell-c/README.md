# 01 - Build Your Own Shell (C)

## Features (MVP)

- REPL loop with `$ ` prompt
- Command parsing (space-separated)
- Built-ins: `cd`, `exit`, `echo`
- External command execution using `fork` + `execvp`
- I/O redirection: `<` and `>`
- Single pipe: `cmd1 | cmd2`

## Build & Run

```bash
gcc -Wall -Wextra -O2 shell.c -o shell
./shell
```

## Examples

```bash
echo hello
pwd
ls -la
cat < input.txt
echo hi > out.txt
cat out.txt | wc -c
```
