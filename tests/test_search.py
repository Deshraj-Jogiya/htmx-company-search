from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_index_page_loads_and_includes_htmx():
    response = client.get("/")
    assert response.status_code == 200
    assert "htmx.org" in response.text
    assert "Acme Analytics" in response.text


def test_search_returns_only_matching_companies():
    response = client.get("/search", params={"q": "acme"})
    assert response.status_code == 200
    assert "Acme Analytics" in response.text
    assert "Northwind Foods" not in response.text


def test_search_matches_by_industry_too():
    response = client.get("/search", params={"q": "healthcare"})
    assert response.status_code == 200
    assert "BlueRiver Health" in response.text
    assert "Umbrella Biotech" in response.text
    assert "Acme Analytics" not in response.text


def test_search_with_no_matches_shows_a_real_empty_state():
    response = client.get("/search", params={"q": "nonexistent-xyz"})
    assert response.status_code == 200
    assert "No companies match" in response.text


def test_empty_query_returns_all_companies():
    response = client.get("/search", params={"q": ""})
    assert response.status_code == 200
    assert "Acme Analytics" in response.text
    assert "Umbrella Biotech" in response.text
