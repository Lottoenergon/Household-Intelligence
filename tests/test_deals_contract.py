"""Kontrak /api/deals: resolver field harus ada, null = unresolved (bukan NaN, bukan nama karangan)."""
import json
import pandas as pd
from fastapi.testclient import TestClient

from backend.server import app, df

client = TestClient(app)


def test_deals_payload_is_valid_json_and_has_resolver_fields():
    resp = client.get("/api/deals?tier=all&limit=100000")
    assert resp.status_code == 200
    data = resp.json()["deals"]
    assert data, "deals kosong"
    for row in data:
        assert "canonical_apartment" in row
        assert "resolution_confidence" in row
        assert row["resolution_confidence"] in {"exact", "fuzzy", "unresolved"}
        if row["resolution_confidence"] == "unresolved":
            assert row["canonical_apartment"] is None


def test_unresolved_rows_never_get_invented_name():
    unresolved = df[df["resolution_confidence"] == "unresolved"]
    assert len(unresolved) > 0
    assert unresolved["canonical_apartment"].isna().all()
    assert unresolved["title"].str.startswith("Unresolved •").all()
