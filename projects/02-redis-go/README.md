# 02 - Build Your Own Redis (Go)

## Features (MVP)

- TCP server on `:6379`
- RESP array parser
- Commands: `PING`, `SET`, `GET`
- Thread-safe in-memory map
- Concurrent client handling with goroutines
- `SET key value PX milliseconds` expiration support

## Run

```bash
go run .
```

Test with `redis-cli`:

```bash
redis-cli -p 6379 ping
redis-cli -p 6379 set name alice
redis-cli -p 6379 get name
redis-cli -p 6379 set temp x px 1000
```
