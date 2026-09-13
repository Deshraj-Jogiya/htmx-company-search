from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

from .data import search_companies

app = FastAPI(title="Company Search (HTMX)")
templates = Jinja2Templates(directory="app/templates")


@app.get("/")
def index(request: Request):
    results = search_companies("")
    return templates.TemplateResponse(request, "index.html", {"results": results, "query": ""})


@app.get("/search")
def search(request: Request, q: str = ""):
    results = search_companies(q)
    return templates.TemplateResponse(request, "_results.html", {"results": results, "query": q})
