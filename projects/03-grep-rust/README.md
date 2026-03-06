# 03 - Build Your Own grep (Rust)

## Features (MVP)

- Read from file or stdin
- Literal and pattern matching line-by-line
- Supports classes and anchors via regex syntax (`\\d`, `\\w`, `[abc]`, `^`, `$`, `+`, `?`)

## Run

```bash
cargo run -- "hello" sample.txt
cat sample.txt | cargo run -- "^foo\\d+$"
```
