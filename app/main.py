from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates

from . import data
from .events import broadcaster, sse_event_stream

app = FastAPI(title="Company Search (HTMX)")
templates = Jinja2Templates(directory="app/templates")

data.init_db()


@app.get("/")
def index(request: Request):
    results = data.search_companies("")
    return templates.TemplateResponse(request, "index.html", {"results": results, "query": ""})


@app.get("/search")
def search(request: Request, q: str = ""):
    results = data.search_companies(q)
    return templates.TemplateResponse(request, "_results.html", {"results": results, "query": q})


@app.post("/companies/{company_id}/toggle-sponsorship")
async def toggle_sponsorship(company_id: int, request: Request):
    company = data.toggle_sponsorship(company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    # The clicking tab gets its own row back instantly below; every OTHER
    # connected tab learns about the change via this broadcast instead.
    await broadcaster.publish(f"company {company_id} updated")

    return templates.TemplateResponse(request, "_row.html", {"c": company})


@app.get("/events")
async def events(request: Request):
    queue = broadcaster.subscribe()
    return StreamingResponse(
        sse_event_stream(queue, request.is_disconnected),
        media_type="text/event-stream",
    )
