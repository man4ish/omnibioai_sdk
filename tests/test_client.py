from __future__ import annotations

import os

import pytest
import responses
import requests

from omnibioai_sdk import OmniClient


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch):
    # Make tests deterministic: clear env that might affect defaults.
    monkeypatch.delenv("OMNIBIOAI_BASE_URL", raising=False)
    monkeypatch.delenv("OMNIBIOAI_TOKEN", raising=False)


def test_client_defaults_from_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OMNIBIOAI_BASE_URL", "http://127.0.0.1:8001")
    monkeypatch.setenv("OMNIBIOAI_TOKEN", "dev")

    c = OmniClient()
    assert c.base_url == "http://127.0.0.1:8001"
    assert c.headers["Authorization"] == "Bearer dev"


@responses.activate
def test_objects_list_success():
    base = "http://127.0.0.1:8001"
    c = OmniClient(base_url=base, token="dev", timeout=3)

    responses.add(
        method=responses.GET,
        url=f"{base}/api/dev/objects/",
        json={"count": 2, "items": [{"object_id": "a"}, {"object_id": "b"}]},
        status=200,
    )

    out = c.objects_list()
    assert out["count"] == 2
    assert len(out["items"]) == 2

    # Verify request headers
    req = responses.calls[0].request
    assert req.headers.get("Authorization") == "Bearer dev"


@responses.activate
def test_object_get_success():
    base = "http://127.0.0.1:8001"
    c = OmniClient(base_url=base, token="dev")

    oid = "56d3fc3a-709b-4ed0-bf17-8cb73c6746b0"
    responses.add(
        method=responses.GET,
        url=f"{base}/api/dev/objects/{oid}/",
        json={"object_type": "LiteratureStudy", "metadata": {"study": "X"}},
        status=200,
    )

    obj = c.object_get(oid)
    assert obj["object_type"] == "LiteratureStudy"
    assert obj["metadata"]["study"] == "X"


@responses.activate
def test_object_get_404_raises_http_error():
    base = "http://127.0.0.1:8001"
    c = OmniClient(base_url=base, token="dev")

    oid = "missing"
    responses.add(
        method=responses.GET,
        url=f"{base}/api/dev/objects/{oid}/",
        json={"detail": "Not found"},
        status=404,
    )

    with pytest.raises(requests.HTTPError):
        c.object_get(oid)


@responses.activate
def test_objects_list_401_raises_http_error():
    base = "http://127.0.0.1:8001"
    c = OmniClient(base_url=base, token="bad")

    responses.add(
        method=responses.GET,
        url=f"{base}/api/dev/objects/",
        json={"error": "unauthorized"},
        status=401,
    )

    with pytest.raises(requests.HTTPError):
        c.objects_list()
