"""Kunci aturan "satu sumber kebenaran" untuk ambang klasifikasi deal.

Latar belakang: angka -0.75 (batas "good deal") dan -1.5 (batas "deep value")
dulu ditulis ulang di 13 tempat lintas Python, SQL, dan JavaScript. Akibatnya
frontend memakai -1.2 sehingga 29 unit salah label sebagai "Deep Value"
(UI menampilkan 72, pipeline sebenarnya 43).

Test ini GAGAL kalau ada yang menulis ulang angka itu di luar src/deal_config.py,
sehingga bug yang sama tidak bisa masuk lagi tanpa ketahuan.

Jalankan: python -m pytest tests -q
"""
import os
import re
import sys

import pandas as pd
import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "src"))

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

import deal_config  # noqa: E402
from deal_config import DEAL_DEEP_Z, DEAL_GOOD_Z, matches_tier  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from backend import server  # noqa: E402

client = TestClient(server.app)

CSV_PATH = os.path.join(BASE, "data", "processed", "jabodetabek_rental_evaluated.csv")

# File yang BOLEH memuat angka ambang: modul sumber + SQL (lihat test di bawah
# yang memastikan SQL-nya tetap sinkron dengan modul).
ALLOWED_THRESHOLD_FILES = {"deal_config.py", "schema.sql"}

# File yang tidak boleh lagi memuat literal ambang.
SCANNED_FILES = [
    os.path.join("backend", "server.py"),
    os.path.join("src", "market_intelligence.py"),
    os.path.join("frontend", "js", "explorer.js"),
    os.path.join("frontend", "js", "app.js"),
    os.path.join("frontend", "js", "simulator.js"),
    os.path.join("frontend", "js", "state.js"),
]


def _strip_comments(line: str, is_python: bool) -> str:
    """Buang komentar supaya dokumentasi yang menyebut angka lama tidak dianggap pelanggaran."""
    if is_python:
        idx = line.find("#")
        return line[:idx] if idx >= 0 else line
    idx = line.find("//")
    return line[:idx] if idx >= 0 else line


def test_no_stray_threshold_literals_outside_deal_config():
    offenders = []
    for rel_path in SCANNED_FILES:
        full = os.path.join(BASE, rel_path)
        if not os.path.exists(full):
            continue
        is_python = rel_path.endswith(".py")
        with open(full, encoding="utf-8") as fh:
            for lineno, raw in enumerate(fh, start=1):
                code = _strip_comments(raw, is_python)
                for literal in ("-0.75", "-1.5", "-1.2"):
                    if literal in code:
                        offenders.append(f"{rel_path}:{lineno} -> {literal} | {raw.strip()[:90]}")
    assert not offenders, (
        "Ambang deal ditulis ulang di luar src/deal_config.py. Pakai "
        "deal_config.matches_tier()/is_below_estimate()/is_deep_value():\n  "
        + "\n  ".join(offenders)
    )


def test_schema_sql_view_matches_deal_config():
    """View SQL memakai literal (agar file tetap bisa dijalankan sendiri) — pastikan sinkron."""
    sql_path = os.path.join(BASE, "sql", "schema.sql")
    sql = open(sql_path, encoding="utf-8").read()

    # View top deals: WHERE f.deal_score_z <= <angka>
    matches = re.findall(r"deal_score_z\s*<=\s*(-?\d+(?:\.\d+)?)", sql)
    assert matches, "Tidak menemukan ambang deal di sql/schema.sql"
    sql_threshold = float(matches[-1])
    assert sql_threshold == DEAL_GOOD_Z, (
        f"sql/schema.sql memakai {sql_threshold} sedangkan deal_config.DEAL_GOOD_Z "
        f"= {DEAL_GOOD_Z}. Samakan keduanya."
    )


def test_telemetry_exposes_thresholds_from_single_source():
    t = client.get("/api/telemetry").json()
    assert "deal_thresholds" in t, "Frontend butuh /api/telemetry -> deal_thresholds"
    assert t["deal_thresholds"]["good_z"] == DEAL_GOOD_Z
    assert t["deal_thresholds"]["deep_z"] == DEAL_DEEP_Z

    # Bila ringkasan pasar sudah punya deal_thresholds, nilainya harus sama.
    summary = server.SUMMARY
    if "deal_thresholds" in summary:
        assert summary["deal_thresholds"]["good_z"] == DEAL_GOOD_Z
        assert summary["deal_thresholds"]["deep_z"] == DEAL_DEEP_Z


def test_api_deal_tiers_match_dataset_counts():
    """Jumlah per tier dari API harus sama dengan hitungan langsung dari dataset."""
    df = pd.read_csv(CSV_PATH)
    z = df["deal_score_z"]
    expected = {
        "all": int(matches_tier(z, "all").sum()),
        "deep": int(matches_tier(z, "deep").sum()),
        "good": int(matches_tier(z, "good").sum()),
    }
    assert expected["all"] == expected["deep"] + expected["good"]

    for tier, count in expected.items():
        resp = client.get(f"/api/deals?tier={tier}&limit=100000")
        assert resp.status_code == 200
        assert resp.json()["total_deals"] == count, f"tier={tier} tidak cocok dataset"


def test_api_deal_tier_rejects_unknown_value():
    assert client.get("/api/deals?tier=bogus").status_code == 400


def test_matches_tier_is_series_safe():
    """matches_tier dipakai untuk memfilter DataFrame -> harus aman untuk Series."""
    z = pd.Series([-2.0, -1.2, -0.9, -0.7, 0.0, 2.0])
    assert list(matches_tier(z, "all")) == [True, True, True, False, False, False]
    assert list(matches_tier(z, "deep")) == [True, False, False, False, False, False]
    assert list(matches_tier(z, "good")) == [False, True, True, False, False, False]
    # Batas harus inklusif pada nilai ambang persis.
    assert bool(matches_tier(pd.Series([DEAL_DEEP_Z]), "deep")[0]) is True
    assert bool(matches_tier(pd.Series([DEAL_GOOD_Z]), "good")[0]) is True


def test_frontend_no_longer_hardcodes_deal_thresholds():
    explorer = open(os.path.join(BASE, "frontend", "js", "explorer.js"), encoding="utf-8").read()
    assert "AppState.dealThresholds" in explorer, "Frontend harus memakai ambang dari telemetry"
    assert "deal_tier ===" not in explorer, (
        "explorer.js masih membaca field `deal_tier` yang tidak ada di dataset; "
        "dataset memakai `deal_classification`."
    )

    state = open(os.path.join(BASE, "frontend", "js", "state.js"), encoding="utf-8").read()
    assert "dealThresholds" in state, "state.js harus punya wadah dealThresholds"


def test_sanitize_js_loaded_before_consumers():
    html = open(os.path.join(BASE, "frontend", "index.html"), encoding="utf-8").read()
    pos_sanitize = html.find("sanitize.js")
    pos_explorer = html.find("explorer.js")
    pos_simulator = html.find("simulator.js")
    assert pos_sanitize != -1, "index.html belum memuat sanitize.js"
    assert pos_sanitize < pos_explorer, "sanitize.js harus dimuat sebelum explorer.js"
    assert pos_sanitize < pos_simulator, "sanitize.js harus dimuat sebelum simulator.js"


def test_theme_js_is_not_loaded_twice():
    html = open(os.path.join(BASE, "frontend", "index.html"), encoding="utf-8").read()
    assert html.count("theme.js") == 1, "theme.js dimuat lebih dari sekali (boros unduhan)"
