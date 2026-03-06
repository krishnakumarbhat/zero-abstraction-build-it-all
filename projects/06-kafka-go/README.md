# 06 - Build Your Own Kafka (Go)

## Features (MVP)

- TCP server (`:9092`)
- Minimal binary framing with API key routing
- API keys:
  - `18` -> ApiVersions
  - `0` -> Produce
  - `1` -> Fetch
- Append-only log file by topic
- Fetch by offset

## Protocol (simplified)

Request frame:

- int32 length
- int16 apiKey
- int16 version
- int32 correlationId
- bytes payload

## Run

```bash
go run .
```
