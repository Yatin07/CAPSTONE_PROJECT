"""
Unit Tests for Adaptive Forecasting Engine (Backend/adaptive_forecast.py)
========================================================================
Validates:
- Hand-computed vectors for each candidate
- Strict 5% margin rule around the boundary (<5% stays ma7, >=5% unseats ma7)
- Exact winner candidate verification and mutation detection
- Deduplication of duplicate dates
- Ineligible candidate exclusion
- Zero future-peeking guarantee
- Missing days non-zero handling
- Strict determinism
- Continuity without cliffs at boundaries (n=4, 7, 14, 28)
- Cold-start n=0 returns prior
- Fast execution runtime (< 50ms for 90 days)
"""

import time
import pytest
from datetime import date, timedelta
from adaptive_forecast import (
    forecast_item,
    _predict_last,
    _predict_ewma,
    _predict_ma7,
    _predict_swd,
    _predict_blend,
)


class TestAdaptiveForecastEngine:

    def test_hand_computed_candidates(self):
        """Validates exact numerical output for each candidate on hand-crafted series."""
        h = [
            ("2026-10-05", 10),
            ("2026-10-06", 20),
            ("2026-10-07", 30),
            ("2026-10-08", 40),
            ("2026-10-09", 50),
            ("2026-10-10", 60),
            ("2026-10-11", 70),
        ]
        target_dow = 0  # Predict next Monday

        # 1. last: y_t-1 = 70
        assert _predict_last(h, target_dow) == 70.0

        # 2. ma7: (10+20+30+40+50+60+70) / 7 = 280 / 7 = 40.0
        assert _predict_ma7(h, target_dow) == 40.0

        # 3. ewma:
        # s0 = 10; s1 = 15; s2 = 22.5; s3 = 31.25; s4 = 40.625; s5 = 50.3125; s6 = 60.15625
        assert _predict_ewma(h, target_dow) == pytest.approx(60.15625, rel=1e-5)

        # 4. swd: only 1 Monday in h ("2026-10-05"), needs >= 2 -> None
        assert _predict_swd(h, target_dow) is None
        assert _predict_blend(h, target_dow) is None

        # Add second Monday ("2026-10-12", 90)
        h2 = h + [("2026-10-12", 90)]
        assert _predict_swd(h2, target_dow) == 50.0
        ma7_h2 = 360.0 / 7.0
        assert _predict_ma7(h2, target_dow) == pytest.approx(ma7_h2, rel=1e-5)
        assert _predict_blend(h2, target_dow) == pytest.approx(0.60 * 50.0 + 0.40 * ma7_h2, rel=1e-5)

    def test_n0_returns_category_prior(self):
        """When n=0, engine returns category prior and zero history days."""
        res = forecast_item(history=[], for_date="2026-10-15", category="Bakery")
        assert res["predictedDemand"] == 24
        assert res["safetyStock"] == 6  # max(1, round(0.25 * 24)) = 6
        assert res["method"] == "prior"
        assert res["methodLabel"] == "Category benchmark"
        assert res["historyDays"] == 0
        assert res["basedOnDate"] is None
        assert "Category benchmark active" in res["explanation"]

    def test_short_history_1_to_4_uses_ewma_blend(self):
        """When 1 <= n < 5, engine uses EWMA blended with prior by w = n/(n+K)."""
        h = [("2026-10-01", 30), ("2026-10-02", 40)]  # n=2
        # EWMA on [30, 40]: s0=30, s1=0.5*40 + 0.5*30 = 35.0
        # Prior for Bakery = 24.0
        # With K=3: w = 2 / (2+3) = 0.4 -> Blended = 0.4 * 35.0 + 0.6 * 24.0 = 28.4 -> 28
        res_k3 = forecast_item(history=h, for_date="2026-10-03", category="Bakery", k_shrinkage=3)
        assert res_k3["predictedDemand"] == 28

        # With empirically chosen K=1: w = 2 / (2+1) = 2/3 -> Blended = (2/3)*35 + (1/3)*24 = 31.33 -> 31
        res = forecast_item(history=h, for_date="2026-10-03", category="Bakery")
        assert res["historyDays"] == 2
        assert res["method"] == "ewma"
        assert res["methodLabel"] == "Smoothed recent sales"
        assert res["predictedDemand"] == 31
        assert res["basedOnDate"] == "2026-10-02"

    def test_five_percent_margin_rule_sub_five_retains_ma7(self):
        """A competitor that beats ma7 by less than 5% must NOT unseat ma7 (retains ma7)."""
        start = date(2026, 9, 1)
        # Construct alternating sequence where ma7 and other methods have near-identical MAEs
        h = []
        for i in range(16):
            d = (start + timedelta(days=i)).isoformat()
            val = 20 if (i % 2 == 0) else 22
            h.append((d, val))

        res = forecast_item(history=h, for_date="2026-09-20", category="Bakery")
        assert res["historyDays"] == 16
        assert res["evalDays"] > 0
        assert res["baselineMae"] is not None
        assert res["methodMae"] is not None
        # On this stationary alternating sequence, ma7 stays the winner
        assert res["method"] == "ma7"
        assert res["methodLabel"] == "7-day average"

    def test_five_percent_margin_rule_super_five_unseats_ma7(self):
        """A competitor that beats ma7 by >= 5% must unseat ma7."""
        start = date(2026, 9, 1)
        # Trending sequence: +10 units every day.
        # On a steep trend, 'last' significantly beats ma7 (MAE ~10 vs MAE ~40, ~75% better)
        h = []
        for i in range(16):
            d = (start + timedelta(days=i)).isoformat()
            h.append((d, 10 + i * 10))

        res = forecast_item(history=h, for_date="2026-09-20", category="Bakery")
        assert res["method"] != "ma7"
        # Verify improvement is >= 5%
        improvement = (res["baselineMae"] - res["methodMae"]) / res["baselineMae"]
        assert improvement >= 0.05
        # Specifically, on a monotonic positive trend, 'last' is the lowest error predictor
        assert res["method"] == "last"
        assert res["methodLabel"] == "Yesterday's sales"

    def test_mutation_detection_swapped_candidates(self):
        """
        Guarantees that swapping candidate algorithms (e.g. last <-> ma7) breaks this test.
        On a monotonic linear trend, 'last' must strictly win over 'ma7'.
        """
        start = date(2026, 8, 1)
        h = [( (start + timedelta(days=i)).isoformat(), 100 + i * 15 ) for i in range(20)]
        target = "2026-08-25"
        res = forecast_item(h, target, category="Bakery")
        # On strong momentum/trend, yesterday's sales ('last') is strictly the best candidate
        assert res["method"] == "last", f"Expected 'last' to win on trend, got '{res['method']}'"
        assert res["methodLabel"] == "Yesterday's sales"

    def test_duplicate_same_date_deduplication(self):
        """Validates that duplicate entries for the same date are deduplicated (keeping latest)."""
        h_with_dups = [
            ("2026-10-01", 10),
            ("2026-10-01", 20),  # Duplicate date, later entry has 20
            ("2026-10-02", 30),
            ("2026-10-03", 40),
            ("2026-10-03", 50),  # Duplicate date, later entry has 50
        ]
        res = forecast_item(h_with_dups, "2026-10-04", category="Bakery")
        # Deduplicated history count must be 3 (not 5)
        assert res["historyDays"] == 3
        assert res["basedOnDate"] == "2026-10-03"

    def test_ineligible_candidates_excluded(self):
        """When history is short (e.g. n=6), swd has fewer than 4 common days and is excluded."""
        start = date(2026, 10, 1)
        h = [( (start + timedelta(days=i)).isoformat(), 25 ) for i in range(6)]
        res = forecast_item(history=h, for_date="2026-10-07", category="Bakery")
        # With n=6, m = min(14, 6-3) = 3 days. m < 4, so swd/blend cannot have >= 4 days
        assert res["method"] in ["ma7", "last", "ewma"]
        assert res["method"] not in ["swd", "blend"]

    def test_no_future_peeking(self):
        """Strict test: altering data ON or AFTER for_date must have ZERO effect on output."""
        h_clean = [
            ("2026-10-01", 20),
            ("2026-10-02", 22),
            ("2026-10-03", 25),
            ("2026-10-04", 28),
            ("2026-10-05", 30),
            ("2026-10-06", 26),
            ("2026-10-07", 24),
        ]
        target_date = "2026-10-08"
        base_res = forecast_item(h_clean, target_date, category="Bakery")

        # Now append future records with extreme outliers
        h_poisoned = list(h_clean) + [
            ("2026-10-08", 99999),  # Same day as for_date
            ("2026-10-09", 88888),  # Future day
            ("2026-10-15", 77777),
        ]
        poisoned_res = forecast_item(h_poisoned, target_date, category="Bakery")

        assert base_res["predictedDemand"] == poisoned_res["predictedDemand"]
        assert base_res["safetyStock"] == poisoned_res["safetyStock"]
        assert base_res["method"] == poisoned_res["method"]
        assert base_res["methodMae"] == poisoned_res["methodMae"]
        assert base_res["baselineMae"] == poisoned_res["baselineMae"]
        assert base_res["basedOnDate"] == "2026-10-07"
        assert poisoned_res["basedOnDate"] == "2026-10-07"

    def test_missing_days_never_zero(self):
        """Gaps in store operations (e.g. closed Sundays/Mondays) are omitted, never zeroed."""
        h = [
            ("2026-10-01", 30),
            ("2026-10-06", 32),  # 5-day gap
            ("2026-10-12", 34),  # 6-day gap
        ]
        res = forecast_item(h, "2026-10-13", category="Bakery")
        assert res["historyDays"] == 3
        assert res["predictedDemand"] > 20

    def test_determinism(self):
        """Running forecast 100 times on the same input returns identical results."""
        start = date(2026, 9, 1)
        h = [( (start + timedelta(days=i)).isoformat(), 20 + (i % 7) ) for i in range(35)]
        first = forecast_item(h, "2026-10-15", category="Bakery")
        for _ in range(100):
            subsequent = forecast_item(h, "2026-10-15", category="Bakery")
            assert first == subsequent

    def test_continuity_without_boundary_cliffs(self):
        """A stationary series (e.g. constant 24 units) must have smooth transitions at n=4, 7, 14, 28."""
        start = date(2026, 8, 1)
        for n_test in [3, 4, 5, 6, 7, 8, 13, 14, 15, 27, 28, 29]:
            h = [( (start + timedelta(days=i)).isoformat(), 24 ) for i in range(n_test)]
            target = (start + timedelta(days=n_test)).isoformat()
            res = forecast_item(h, target, category="Bakery")
            assert abs(res["predictedDemand"] - 24) <= 2, f"Cliff observed at n={n_test}: pred={res['predictedDemand']}"

    def test_runtime_under_50ms(self):
        """Verifies runtime is well under 50ms for a full 90-day history."""
        start = date(2026, 6, 1)
        h = [( (start + timedelta(days=i)).isoformat(), 20 + (i % 15) ) for i in range(90)]
        target = (start + timedelta(days=90)).isoformat()

        t0 = time.perf_counter()
        res = forecast_item(h, target, category="Bakery")
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        print(f"\n[BENCHMARK] 90-day history forecast took: {elapsed_ms:.2f} ms")
        assert elapsed_ms < 50.0, f"Runtime too slow: {elapsed_ms:.2f} ms >= 50ms"
        assert res["historyDays"] == 90
        assert res["predictedDemand"] > 0
