# 08 - Build Your Own SQLite Reader (Rust)

## Features (MVP)

- Parse first 100-byte SQLite header
- Read pages by page number
- Parse B-Tree page type (interior/leaf)
- Basic info for page traversal

## Run

```bash
cargo run -- header test.db
cargo run -- page test.db 1
```
