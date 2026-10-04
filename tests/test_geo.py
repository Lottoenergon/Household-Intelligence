"""Unit test untuk validasi & imputasi koordinat (jalankan: python -m pytest tests -q)."""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from transformation import is_valid_jabodetabek_coord, clean_and_impute_coordinates


def test_valid_coord_inside_bbox():
    assert is_valid_jabodetabek_coord(-6.2088, 106.82)


def test_rejects_lon_copied_from_lat():
    # bug nyata di data portal: longitude == latitude
    assert not is_valid_jabodetabek_coord(-6.23168, -6.23168)


def test_rejects_nan_and_none():
    assert not is_valid_jabodetabek_coord(np.nan, 106.8)
    assert not is_valid_jabodetabek_coord(None, None)


def test_rejects_outside_jabodetabek():
    assert not is_valid_jabodetabek_coord(-7.25, 112.75)  # Surabaya


def _frame():
    return pd.DataFrame({
        "target_city": ["Tangerang Selatan"] * 4 + ["Depok"],
        "subdistrict": ["BSD", "BSD", "BSD", "Serpong", "Margonda"],
        "latitude": [-6.30, -6.32, np.nan, np.nan, -6.38],
        "longitude": [106.65, 106.67, np.nan, np.nan, -6.38],  # baris terakhir: lon==lat
    })


def test_imputes_from_subdistrict_then_city_never_cbd():
    out = clean_and_impute_coordinates(_frame())
    assert out.loc[2, "geo_source"] == "subdistrict_centroid"
    assert abs(out.loc[2, "latitude"] - (-6.31)) < 1e-9
    assert out.loc[3, "geo_source"] == "city_centroid"      # Serpong tidak punya data valid
    assert not ((out["latitude"] == -6.2088) & (out["longitude"] == 106.82)).any()


def test_unfixable_rows_stay_nan_not_invented():
    out = clean_and_impute_coordinates(_frame())
    # Depok hanya punya 1 baris & koordinatnya rusak -> tidak ada sumber imputasi
    assert np.isnan(out.loc[4, "latitude"])
    assert out.loc[4, "geo_is_imputed"] == 1
