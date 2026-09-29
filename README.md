# Company Search (HTMX)

A tiny live-search page using HTMX for partial-page updates instead of a JS framework --
FastAPI + Jinja2, the same real stack this author's Career Pilot CRM runs on.

## How it works

Typing in the search box fires an HTMX request (`hx-get="/search"`, debounced via
`hx-trigger="input changed delay:300ms"`) that hits a real FastAPI endpoint, which
re-renders a Jinja2 partial (`_results.html`) server-side and swaps it into the page.
No client-side JavaScript framework, no separate JSON API consumed by a SPA -- the
server renders HTML, HTMX just swaps fragments of it in.

Data is real (in-memory) SQLite now, not a hardcoded Python list -- `app/data.py`.

**Inline edit**: each row's "Sponsors H-1B" cell is a real button
(`hx-post="/companies/{id}/toggle-sponsorship"`, `hx-target="closest tr"`,
`hx-swap="outerHTML"`) that flips the value in the database and swaps just that row
in place, no full-page or full-results reload.

**Real-time updates via SSE**: `GET /events` is a real `text/event-stream` connection
(`app/events.py`). When any client toggles a company, the server broadcasts a
`refresh` event to every other connected client (`hx-ext="sse"` +
`sse-connect="/events"` in `index.html`), which re-issues its own current `/search`
request -- so a second open tab sees the change live, without polling.

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

`tests/test_inline_edit_and_events.py` covers the toggle route (persists, returns
the updated row fragment, 404s for an unknown id) and the SSE plumbing. The SSE
formatting/loop logic (`app/events.py`'s `sse_event_stream`) is decoupled from
FastAPI's `Request` specifically so it can be driven directly with a plain
`asyncio.Queue` and a fake `is_disconnected` callable in a test, rather than only
being exercisable through a full live streaming HTTP connection -- a real, live
concurrent-SSE-subscriber test (two overlapping requests through the same test
client) was tried first and reliably hung; verified live instead with the real
app running and `curl -N`, confirmed a toggle in one request genuinely pushes a
`refresh` event to an already-open `/events` connection.
