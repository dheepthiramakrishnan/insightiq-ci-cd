import os
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
SAMPLE = os.path.join(os.path.dirname(__file__), "..", "sample_data", "sales_data.csv")


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_api_ping():
    assert client.get("/api/ping").status_code == 200


@pytest.mark.parametrize("path", ["/", "/upload", "/analytics", "/insights"])
def test_pages_load(path):
    assert client.get(path).status_code == 200


def test_upload_rejects_non_csv():
    r = client.post("/api/upload", files={"file": ("notes.txt", b"hello", "text/plain")})
    assert r.status_code in (400, 422)


def test_upload_sample_csv_and_kpis():
    with open(SAMPLE, "rb") as f:
        r = client.post("/api/upload", files={"file": ("sales_data.csv", f, "text/csv")})
    assert r.status_code == 200, r.text
    k = client.get("/api/kpis")
    assert k.status_code == 200
