import asyncio

import pytest
from fastapi.testclient import TestClient

from app import data
from app.events import broadcaster, sse_event_stream
from app.main import app

client = TestClient(app)


def _company_id(name: str) -> int:
    (company,) = [c for c in data.search_companies("") if c["name"] == name]
    return company["id"]


def test_toggling_sponsorship_persists_and_returns_the_updated_row():
    company_id = _company_id("Northwind Foods")
    assert data.get_company(company_id)["sponsors_h1b"] == 0

    response = client.post(f"/companies/{company_id}/toggle-sponsorship")

    assert response.status_code == 200
    assert f'id="company-row-{company_id}"' in response.text
    assert ">Yes<" in response.text
    # The real, persisted state, not just the returned fragment.
    assert data.get_company(company_id)["sponsors_h1b"] == 1


def test_toggling_twice_returns_to_the_original_value():
    company_id = _company_id("Acme Analytics")
    assert data.get_company(company_id)["sponsors_h1b"] == 1

    client.post(f"/companies/{company_id}/toggle-sponsorship")
    client.post(f"/companies/{company_id}/toggle-sponsorship")

    assert data.get_company(company_id)["sponsors_h1b"] == 1


def test_toggling_an_unknown_company_is_a_real_404():
    response = client.post("/companies/999999/toggle-sponsorship")
    assert response.status_code == 404


def test_index_page_wires_up_the_sse_connection():
    response = client.get("/")
    assert response.status_code == 200
    assert 'sse-connect="/events"' in response.text
    assert "htmx-ext-sse" in response.text


def test_toggling_sponsorship_publishes_a_real_broadcast_message(monkeypatch):
    # Tests the actual wiring in main.py -- the toggle route really does
    # call the shared broadcaster, with the right message -- without
    # needing a full live streaming HTTP connection to observe it.
    published = []

    async def fake_publish(message):
        published.append(message)

    monkeypatch.setattr(broadcaster, "publish", fake_publish)

    company_id = _company_id("Contoso Cloud")
    client.post(f"/companies/{company_id}/toggle-sponsorship")

    assert published == [f"company {company_id} updated"]


def test_sse_event_stream_formats_a_published_message_as_a_real_sse_event():
    # Drives the real generator directly (a plain asyncio.Queue plus a
    # fake is_disconnected callable) rather than through a live streaming
    # HTTP connection -- this is the actual SSE formatting/loop logic
    # main.py's /events route uses, just decoupled from FastAPI's Request
    # so it's directly, deterministically testable.
    async def run():
        queue: asyncio.Queue = asyncio.Queue()
        disconnected = False

        async def is_disconnected():
            return disconnected

        stream = sse_event_stream(queue, is_disconnected)

        await queue.put("company 7 updated")
        first_event = await asyncio.wait_for(stream.__anext__(), timeout=2)
        assert first_event == "event: refresh\ndata: company 7 updated\n\n"

        await stream.aclose()

    asyncio.run(run())


def test_sse_event_stream_unsubscribes_on_cleanup():
    async def run():
        queue = broadcaster.subscribe()

        async def is_disconnected():
            return True  # ends the loop on the very first check

        stream = sse_event_stream(queue, is_disconnected)
        with pytest.raises(StopAsyncIteration):
            await stream.__anext__()

        # The generator's own finally block should have unsubscribed it.
        await broadcaster.publish("should not reach an unsubscribed queue")
        assert queue.empty()

    asyncio.run(run())
