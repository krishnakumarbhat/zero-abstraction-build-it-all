# 11 - Build Your Own Claude-Code Style Agent (Python)

## Features (MVP)

- API call loop to LLM provider (OpenAI Chat Completions compatible)
- Tool schemas (`read_file`, `search_web`, `run_bash`)
- Agent loop that executes requested tools and feeds output back

## Setup

```bash
cp .env.example .env
# Edit .env and set GEMINI_API_KEY
```

## Run

```bash
python3 agent.py "Summarize README.md"
python3 agent.py --mock "Summarize README.md"
```

## Notes

- Uses OpenAI-compatible function calling format.
- `search_web` is a stub in this MVP.
- Default live provider is Gemini (`LLM_PROVIDER=gemini` in `.env`).
- If live provider key is missing, the script auto-falls back to local mock mode.
