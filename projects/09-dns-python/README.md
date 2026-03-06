# 09 - Build Your Own DNS Server (Python)

## Features (MVP)

- UDP server on configurable port (default `5353`)
- DNS header parsing
- Question name parsing
- Forwarding to upstream resolver (`8.8.8.8:53` by default)
- Relays response back to original client

## Run

```bash
python3 dns_server.py --port 5353 --upstream 8.8.8.8:53
```

Test:

```bash
dig @127.0.0.1 -p 5353 example.com A
```
