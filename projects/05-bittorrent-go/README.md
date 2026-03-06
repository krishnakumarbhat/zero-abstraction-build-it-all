# 05 - Build Your Own BitTorrent (Go)

## Features (MVP)

- Bencode parser
- `.torrent` metadata parsing
- Tracker request (HTTP GET)
- Peer list extraction from compact peer format

## Run

```bash
go run . parse sample.torrent
go run . peers sample.torrent
```
