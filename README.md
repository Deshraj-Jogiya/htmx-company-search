# Company Search (HTMX)

A tiny live-search page using HTMX for partial-page updates instead of a JS framework --
FastAPI + Jinja2, the same real stack this author's Career Pilot CRM runs on.

## How it works

Typing in the search box fires an HTMX request (`hx-get="/search"`, debounced via
`hx-trigger="keyup changed delay:300ms"`) that hits a real FastAPI endpoint, which
re-renders a Jinja2 partial (`_results.html`) server-side and swaps it into the page.
No client-side JavaScript framework, no separate JSON API consumed by a SPA -- the
server renders HTML, HTMX just swaps fragments of it in.

## Running it

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://localhost:8000` and type in the search box.

## Testing

```bash
python -m pytest tests/ -v
```

Real tests (FastAPI `TestClient`) against the actual rendered HTML -- checking the
full page includes the htmx script tag, that `/search` filters by name and by
industry, and that a no-match query renders a real empty state rather than an
empty table.

The `TestClient` tests hit `/search` directly, so they can't catch a real HTMX
wiring bug in the page itself. This was actually caught by driving a real headless
browser against the live app: `hx-trigger` was initially `keyup changed`, which
never fires for a value set via autofill or a paste-then-click-elsewhere -- only
real keystrokes. Switched to `input changed`, which fires for typing, pasting, and
autofill alike, and re-verified both paths live.
