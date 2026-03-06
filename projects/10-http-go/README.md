# 10 - Build Your Own HTTP Server (Go)

## Features (MVP)

- TCP listener on `:8080`
- Parse request line (method, path, version)
- Parse headers into map
- Basic routing
- Response formatting with status line, headers, and body

## Routes

- `GET /` -> Hello
- `GET /health` -> OK
- others -> 404

## Run

```bash
go run .
curl -i http://127.0.0.1:8080/
curl -i http://127.0.0.1:8080/health
```
