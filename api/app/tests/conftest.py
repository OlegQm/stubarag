import pytest
import requests
import httpx

import app.services.webscraper.webscraper_service as ws

@pytest.fixture(autouse=True)
def mock_webscraper_dependencies(monkeypatch, request):
    if "webscraper" in request.node.name:
        def fake_requests_get(url, timeout=5):
            class DummyResponse:
                status_code = 200
                text = "<html><body><a href='x'>link-text</a></body></html>"
                def raise_for_status(self): pass
            return DummyResponse()
        monkeypatch.setattr(requests, "get", fake_requests_get)

        def fake_httpx_get(url, *args, **kwargs):
            return httpx.Response(200, content=b"<html><body><a href='x'>link-text</a></body></html>")
        monkeypatch.setattr(httpx, "get", fake_httpx_get)

        async def fake_async_request(self, method, url, *args, **kwargs):
            return httpx.Response(200, content=b"<html><body><a href='x'>link-text</a></body></html>")
        monkeypatch.setattr(httpx.AsyncClient, "request", fake_async_request)

        monkeypatch.setattr(ws, "clean_page", lambda html: "LINK-TEXT")

        async def fake_save_to_db(*args, **kwargs):
            return None
        monkeypatch.setattr(ws, "save_to_mongo_and_update_vector_db", fake_save_to_db)
