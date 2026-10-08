"""Entity resolution: safety rules. Each test encodes a real false-merge we hit during development."""
import importlib.util
import os

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location("er", os.path.join(BASE, "src", "entity_resolution.py"))
er = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(er)


def pid(*texts):
    return er.resolve(*texts)["project_id"]


def test_exact_building_name_resolves():
    r = er.resolve("For Rent 2 Bedrooms Apartment At Denpasar Residence In Prime Kuningan")
    assert r["project_id"] == "denpasar-residence"
    assert r["confidence"] == "exact"


def test_longer_alias_beats_shorter_prefix():
    # 'Menara Marina Condominium' must not fall through to a shorter sibling.
    assert pid("Sewa Apartemen Menara Marina Condominium Jakarta Utara") == "menara-marina-condominium"


def test_generic_city_word_does_not_resolve():
    # 'Jakarta' alone must never map to 'Menara Jakarta' (false merge seen in dry-run).
    assert pid("113m2 full furnish ready to use, Jakarta") is None


def test_generic_park_does_not_resolve():
    # 'Park' alone must not claim a building.
    assert pid("Apartemen Studio Satu Menit Ke Gerbang Tol, near Park") is None


def test_marketing_alias_does_not_match_everything():
    # The long alias 'golf view apartment for lease near jis' used to fuzzy-match half the dataset.
    assert pid("Apartemen Baru 2 Kamar Siap Huni Dekat Pusat Perbelanjaan") is None


def test_typo_recidence_resolves_fuzzy_or_stays_unresolved_never_wrong():
    r = er.resolve("Siap Huni Studio Apartemen U Recidence Tower 2 Dekat dengan Uph Karawaci")
    assert r["project_id"] in (None, "u-residence-karawaci")
    assert r["confidence"] in ("fuzzy", "unresolved")


def test_unknown_building_is_unresolved_not_invented():
    r = er.resolve("Disewakan apartemen murah dekat stasiun, siap huni")
    assert r == {"project_id": None, "name": None, "confidence": "unresolved", "matched_alias": None}


def test_registry_has_unique_ids_and_names():
    import json
    d = json.load(open(os.path.join(BASE, "data", "property_registry.json"), encoding="utf-8"))
    ids = [p["id"] for p in d["projects"]]
    assert len(ids) == len(set(ids))
    assert all(p["aliases"] for p in d["projects"])
