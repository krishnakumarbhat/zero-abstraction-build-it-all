# Build your own Web Browser (Python, from scratch)

Terminal-first mini browser using only Python standard library.

## Implemented pipeline

- Raw TCP HTTP client (manual request/response)
- HTML parser (state-machine style tag/text scanning)
- CSS parser for simple selectors and declarations
- DOM style application (`tag`, `.class`, `#id`, inline style)
- Basic layout and terminal painting

## Run

```bash
cd projects/17-browser-python
python3 browser.py http://example.com
python3 browser.py http://127.0.0.1:8080/index.html --width 100
```

## Notes

- Supports `http://` only (no TLS).
- Rendering target is terminal text output (no windowing/graphics toolkit).
