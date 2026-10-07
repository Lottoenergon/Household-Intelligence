"""
deal_config.py
=======================================================================
SINGLE SOURCE OF TRUTH untuk ambang batas (threshold) klasifikasi deal.

Sebelum modul ini ada, angka -0.75 dan -1.5 ditulis ulang di 13 tempat
lintas Python, SQL, dan JavaScript. Akibatnya frontend memakai -1.2 untuk
"Deep Value" sementara pipeline dan backend memakai -1.5, sehingga 29 unit
salah label di UI (72 ditampilkan vs 43 yang sebenarnya).

ATURAN: jangan pernah menulis angka ambang ini sebagai literal di file lain.
Modul ini dipakai oleh:
  - src/market_intelligence.py   (pelatihan, scoring, ringkasan pasar)
  - backend/server.py            (endpoint /api/deals, /api/listings, /api/districts)
  - frontend/js/explorer.js      (lewat /api/telemetry -> deal_thresholds)
  - sql/schema.sql               (view_top_undervalued_deals, dijaga oleh test)

Dijaga oleh tests/test_deal_thresholds.py.
"""

# Skala: z-score residual log harga aktual vs harga wajar model.
# z = (ln(harga aktual) - ln(harga wajar)) / simpangan baku residual log
DEAL_GOOD_Z: float = -0.75      # batas "Good Deal" (di bawah estimasi wajar)
DEAL_DEEP_Z: float = -1.5       # batas "Deep Value" (jauh di bawah estimasi)

# Batas atas untuk sisi mahal (dipakai klasifikasi, bukan filter)
PREMIUM_Z: float = 0.75
OVERPRICED_Z: float = 1.5

# Label kanonik. Nilai string ini ikut tersimpan di kolom `deal_classification`
# pada dataset hasil pipeline, jadi JANGAN diubah tanpa migrasi data.
LABEL_DEEP = "Deep Value Deal (Rare Find)"
LABEL_GOOD = "Good Deal (Undervalued)"
LABEL_FAIR = "Fair Market Price"
LABEL_PREMIUM = "Premium / High Price"
LABEL_OVERPRICED = "Overpriced / Luxury Tag"

# Tier ringkas untuk API/UI
TIER_DEEP = "deep"
TIER_GOOD = "good"
TIER_ALL = "all"


def is_below_estimate(z: float) -> bool:
    """True bila unit tergolong di bawah estimasi wajar (masuk radar deal)."""
    return z <= DEAL_GOOD_Z


def is_deep_value(z: float) -> bool:
    """True bila unit tergolong deep value (diskon paling ekstrem)."""
    return z <= DEAL_DEEP_Z


def classify_deal(z: float) -> str:
    """Peta z-score -> label kanonik klasifikasi deal."""
    if z <= DEAL_DEEP_Z:
        return LABEL_DEEP
    if z <= DEAL_GOOD_Z:
        return LABEL_GOOD
    if z < PREMIUM_Z:
        return LABEL_FAIR
    if z < OVERPRICED_Z:
        return LABEL_PREMIUM
    return LABEL_OVERPRICED


def tier_of(z: float) -> str | None:
    """Peta z-score -> tier ringkas ('deep' | 'good' | None bila bukan deal)."""
    if z <= DEAL_DEEP_Z:
        return TIER_DEEP
    if z <= DEAL_GOOD_Z:
        return TIER_GOOD
    return None


def matches_tier(z: float, tier: str) -> bool:
    """True bila unit masuk tier yang diminta. tier: 'all' | 'deep' | 'good'.

    Aman untuk skalar maupun pandas.Series (dipakai untuk filter DataFrame).
    """
    if tier in (None, "", TIER_ALL):
        return is_below_estimate(z)
    if tier == TIER_DEEP:
        return is_deep_value(z)
    if tier == TIER_GOOD:
        # Operator bitwise (&, ~) dipakai agar tetap benar untuk Series;
        # `and`/`not` akan error dengan "truth value of a Series is ambiguous".
        return is_below_estimate(z) & ~is_deep_value(z)
    raise ValueError(f"tier tidak dikenal: {tier!r} (pilihan: all, deep, good)")


def as_dict() -> dict:
    """Bentuk yang dikirim ke API/UI supaya frontend tidak perlu hardcode angka."""
    return {
        "scale": "z_residual_log",
        "good_z": DEAL_GOOD_Z,
        "deep_z": DEAL_DEEP_Z,
        "premium_z": PREMIUM_Z,
        "overpriced_z": OVERPRICED_Z,
        "labels": {
            "deep": LABEL_DEEP,
            "good": LABEL_GOOD,
            "fair": LABEL_FAIR,
            "premium": LABEL_PREMIUM,
            "overpriced": LABEL_OVERPRICED,
        },
    }
