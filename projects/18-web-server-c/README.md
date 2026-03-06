# Build your own Web Server (C, from scratch)

Raw TCP HTTP/1.1 server using POSIX sockets and manual request parsing.

## Features

- Socket setup (`socket`, `bind`, `listen`)
- Accept loop (`accept` per incoming client)
- Manual HTTP request-line parsing (`GET /path HTTP/1.1`)
- Filesystem-backed static file serving
- Manual response construction (`HTTP/1.1 200 OK ...`)

## Build

```bash
cd projects/18-web-server-c
gcc -std=c11 -O2 -Wall -Wextra -pedantic -o web-server main.c
```

## Run

```bash
./web-server
./web-server 8080
```

From another terminal:

```bash
curl -i http://127.0.0.1:8080/
curl -i http://127.0.0.1:8080/index.html
```
