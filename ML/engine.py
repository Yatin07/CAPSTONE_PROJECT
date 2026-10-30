"""
RestockIQ ML Shared Forecasting Engine
Supports dual-engine architecture:
- 'legacy': Prophet-derived benchmark + weekend factor / TSB credibility shrinkage (default)
- 'gbdt': HistGradientBoostingRegressor with Model (iv) features for items with >= 28 days of data
          and a trained bakery SKU; fallback to benchmark/blend path otherwise.
- Safety Stock: Newsvendor critical ratio z = norm.ppf((price - cost) / price) with COGS_RATIO default 0.40,
  sigma = per-item residual standard deviation over the last 60 training days.
"""

import os
import sys
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
try:
    from sklearn.ensemble import HistGradientBoostingRegressor
except ImportError:
    # Add ML venv site-packages if running from Backend venv
    ml_venv_pkg = Path(__file__).resolve().parent / "venv" / "Lib" / "site-packages"
    if ml_venv_pkg.exists() and str(ml_venv_pkg) not in sys.path:
        sys.path.insert(0, str(ml_venv_pkg))
    from sklearn.ensemble import HistGradientBoostingRegressor

try:
    from scipy.stats import norm
    def normal_ppf(p: float) -> float:
        return float(norm.ppf(p))
except ImportError:
    # Standard Abramowitz & Stegun / Acklam rational approximation for inverse normal CDF
    def normal_ppf(p: float) -> float:
        if p <= 0.0: return -10.0
        if p >= 1.0: return 10.0
        # Rational approximation
        a = [-3.969683028665376e+01,  2.209460984245205e+02, -2.759285104469687e+02,
              1.383577518672690e+02, -3.066479806614716e+01,  2.506628277459239e+00]
        b = [-5.447609879822406e+01,  1.615858368580409e+02, -1.556989798598866e+02,
              6.680131188771972e+01, -1.328068155288572e+01]
        c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
             -2.549732539343734e+00,  4.374664141464968e+00,  2.938163982698783e+00]
        d = [ 7.784695709041462e-03,  3.224671290700398e-01,  2.445134137142996e+00,
              3.754408661907416e+00]
        q = p - 0.5
        if abs(q) <= 0.425:
            r = 0.180625 - q * q
            return q * (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5]) / \
                        (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1.0)
        r = p if q < 0 else 1.0 - p
        r = np.sqrt(-np.log(r))
        x = (((((c[0]*r+c[1])*r+c[2])*r+c[3])*r+c[4])*r+c[5]) / \
            ((((d[0]*r+d[1])*r+d[2])*r+d[3])*r+1.0)
        return -x if q < 0 else x


# Synchronized cold-start category priors (shared with Backend/constants.py)
CATEGORY_PRIORS = {
    "Bakery": {"predictedDemand": 24, "safetyStock": 7, "norm_cat": "Breads & Baguettes"},
    "Beverage": {"predictedDemand": 18, "safetyStock": 5, "norm_cat": "Beverages"},
    "Food": {"predictedDemand": 15, "safetyStock": 5, "norm_cat": "Prepared Food"},
    "Dessert": {"predictedDemand": 12, "safetyStock": 4, "norm_cat": "Desserts & Pastries"},
    "Snack": {"predictedDemand": 10, "safetyStock": 3, "norm_cat": "Snacks"},
    "Other": {"predictedDemand": 10, "safetyStock": 3, "norm_cat": "General Merchandise"},
}

# Primary item name mapping
NAME_MAP = {
    "croissant": "CROISSANT",
    "croissants": "CROISSANT",
    "baguette": "BAGUETTE",
    "traditional baguette": "BAGUETTE",
    "pain au chocolat": "PAIN AU CHOCOLAT",
    "brioche": "BRIOCHE",
    "banette": "BANETTE",
    "cookie": "COOKIE",
    "cafe": "CAFE OU EAU",
    "coffee": "CAFE OU EAU",
    "coupe dessert": "COUPE",
    "coupe": "COUPE",
}

# Features specification for Model (iv)
LAG_FEATS_1D = ["day_of_week", "month", "is_tourist_season", "y_lag_1", "y_roll_7", "y_lag_7_cal", "pred_weekday4w_cal"]
CAL_ENHANCED_FEATS = ["is_pub_holiday", "is_pub_holiday_window", "is_bridge_day", "is_school_holiday"]
FEATS_MODEL_IV = ["article_cat"] + LAG_FEATS_1D + CAL_ENHANCED_FEATS


class MLSharedEngine:
    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            data_dir = Path(__file__).resolve().parent / "data" / "processed"
        self.data_dir = data_dir
        self.primary_csv = data_dir / "primary_items.csv"
        self.priors_json = data_dir / "category_priors_percentiles.json"
        
        self.historical_ref: Optional[pd.DataFrame] = None
        self.category_priors: Dict[str, Any] = {}
        self.gbdt_model: Optional[HistGradientBoostingRegressor] = None
        self.per_item_sigmas: Dict[str, float] = {}
        self._load_reference_data()

    def _load_reference_data(self):
        if self.primary_csv.exists():
            try:
                df = pd.read_csv(self.primary_csv)
                df["ds"] = pd.to_datetime(df["ds"])
                self.historical_ref = df.sort_values(["article", "ds"]).reset_index(drop=True)
            except Exception as e:
                print(f"[ML ENGINE WARNING] Failed to load primary_items.csv: {e}")

        if self.priors_json.exists():
            try:
                with open(self.priors_json, "r", encoding="utf-8") as f:
                    self.category_priors = json.load(f)
            except Exception as e:
                print(f"[ML ENGINE WARNING] Failed to load priors: {e}")

    @staticmethod
    def get_configured_engine() -> str:
        return os.getenv("ENGINE", "legacy").strip().lower()

    @staticmethod
    def compute_safety_stock(price: float, cost: Optional[float] = None, sigma: float = 1.0) -> Tuple[int, float, float]:
        """
        Calculates safety stock from Newsvendor critical ratio:
        CR = (price - cost) / price
        z = norm.ppf(CR)
        safety_stock = max(1, round(z * sigma)), capped at 3 * sigma
        Assumption: COGS_RATIO env var default 0.40 -> cost = price * 0.40 -> CR = 0.60
        """
        cogs_ratio = float(os.getenv("COGS_RATIO", "0.40"))
        if cost is None:
            cost = price * cogs_ratio

        if price <= 0:
            cr = 0.60
        else:
            cr = (price - cost) / price

        # Clamped critical ratio
        cr = float(np.clip(cr, 0.01, 0.99))
        z = normal_ppf(cr)

        raw_safety = z * max(0.5, sigma)
        safety_stock = max(1, int(round(raw_safety)))
        # Capped at 3 * sigma
        safety_stock = min(safety_stock, int(round(3.0 * max(1.0, sigma))))
        return safety_stock, z, cr

    @staticmethod
    def tsb_forecast(series: np.ndarray, alpha=0.2, beta=0.2) -> float:
        n = len(series)
        non_zero = series[series > 0]
        if len(non_zero) == 0:
            return 0.0

        z = np.zeros(n)
        p = np.zeros(n)
        z[0] = non_zero[0]
        p[0] = len(non_zero) / n

        for t in range(1, n):
            if series[t] > 0:
                z[t] = alpha * series[t] + (1 - alpha) * z[t - 1]
                p[t] = beta * 1 + (1 - beta) * p[t - 1]
            else:
                z[t] = z[t - 1]
                p[t] = beta * 0 + (1 - beta) * p[t - 1]

        return float(p[-1] * z[-1])

    def fit_gbdt_on_history(self):
        """Fits HistGradientBoostingRegressor on primary_items.csv with Model (iv) features."""
        if self.historical_ref is None or len(self.historical_ref) == 0:
            return

        df = self.historical_ref.copy()
        df["ds"] = pd.to_datetime(df["ds"])
        df = df.sort_values(["article", "ds"]).reset_index(drop=True)
        df["day_of_week"] = df["ds"].dt.dayofweek
        df["month"] = df["ds"].dt.month
        df["is_tourist_season"] = df["month"].isin([7, 8]).astype(int)
        df["article_cat"] = df["article"].astype("category")

        lookup = df.set_index(["article", "ds"])["y"].to_dict()
        def get_weekday4w(art, d):
            vals = []
            for k in [1, 2, 3, 4]:
                v = lookup.get((art, d - pd.Timedelta(days=7*k)))
                if v is not None and not np.isnan(v):
                    vals.append(v)
            return float(np.mean(vals)) if len(vals) > 0 else 0.0

        df["pred_weekday4w_cal"] = [get_weekday4w(a, d) for a, d in zip(df["article"], df["ds"])]
        df["y_lag_7_cal"] = [lookup.get((art, d - pd.Timedelta(days=7)), np.nan) for art, d in zip(df["article"], df["ds"])]
        df["y_lag_1"] = df.groupby("article")["y"].shift(1)
        df["y_roll_7"] = df.groupby("article")["y"].transform(lambda s: s.shift(1).rolling(7, min_periods=3).mean())

        # Holiday features (French calendar for primary bakery reference dataset)
        try:
            import holidays
            fr_public = holidays.France(years=[2021, 2022])
            pub_hols = set(pd.to_datetime(list(fr_public.keys())))
        except Exception:
            pub_hols = set()

        ponts = set(pd.to_datetime(["2021-05-14", "2022-05-27"]))
        vac_ranges = [
            ("2021-02-20", "2021-03-07"), ("2021-04-10", "2021-04-25"), ("2021-07-06", "2021-08-31"),
            ("2021-10-23", "2021-11-07"), ("2021-12-18", "2022-01-02"), ("2022-02-05", "2022-02-20"),
            ("2022-04-09", "2022-04-24"), ("2022-07-07", "2022-08-31")
        ]
        school_hols = set()
        for s, e in vac_ranges:
            for d in pd.date_range(s, e):
                school_hols.add(d)

        df["is_pub_holiday"] = df["ds"].isin(pub_hols).astype(int)
        df["is_bridge_day"] = df["ds"].isin(ponts).astype(int)
        df["is_school_holiday"] = df["ds"].isin(school_hols).astype(int)
        pub_window = set()
        for d in pub_hols:
            pub_window.add(d - pd.Timedelta(days=1))
            pub_window.add(d + pd.Timedelta(days=1))
        df["is_pub_holiday_window"] = df["ds"].isin(pub_window).astype(int)

        clean = df.dropna(subset=FEATS_MODEL_IV + ["y"]).copy()

        gbdt = HistGradientBoostingRegressor(categorical_features=[0], learning_rate=0.05, max_iter=200, max_depth=6, random_state=42)
        gbdt.fit(clean[FEATS_MODEL_IV], clean["y"])
        self.gbdt_model = gbdt

        # Compute per-item residual standard deviation over the last 60 training days
        clean["pred"] = gbdt.predict(clean[FEATS_MODEL_IV])
        clean["residual"] = clean["y"] - clean["pred"]
        for art, grp in clean.groupby("article"):
            sub_60 = grp.sort_values("ds").tail(60)
            if len(sub_60) >= 10:
                self.per_item_sigmas[art] = float(sub_60["residual"].std())
            else:
                self.per_item_sigmas[art] = float(max(1.0, grp["residual"].std()))

    def predict_item(self, item: Dict[str, Any], sales_history: List[int], as_of_date: Optional[str] = None, engine_override: Optional[str] = None) -> Dict[str, Any]:
        """
        Unified prediction dispatcher adhering to the frozen product spec:
        - If engine == 'gbdt' and days >= 28 and mapped bakery SKU:
            Uses HistGradientBoostingRegressor with Model (iv) features and Newsvendor critical ratio.
        - Otherwise (engine == 'legacy' or < 28 days or unmapped):
            Uses benchmark / blend path (TSB shrinkage if sparse/cold-start; historical mean + weekend factor if legacy primary).
        """
        engine = (engine_override or self.get_configured_engine()).lower()
        now = datetime.now(timezone.utc)
        if as_of_date:
            try:
                now = datetime.strptime(as_of_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except Exception:
                pass

        item_name = item.get("name", "")
        clean_name = item_name.strip().lower()
        ref_article = NAME_MAP.get(clean_name)
        price = float(item.get("price") or 50.0)
        current_stock = int(item.get("currentStock", 0))
        is_perishable = bool(item.get("isPerishable", True))
        days_of_data = len(sales_history)

        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        dow_idx = now.weekday()
        dow_name = day_names[dow_idx]

        # 1. GBDT MODEL (iv) PATH: Requires >= 28 days and mapped bakery SKU
        if engine == "gbdt" and days_of_data >= 28 and ref_article and self.historical_ref is not None:
            if self.gbdt_model is None:
                self.fit_gbdt_on_history()

            sigma = self.per_item_sigmas.get(ref_article, 4.0)
            safety_stock, z_val, cr_val = self.compute_safety_stock(price=price, sigma=sigma)

            # Feature construction for day-ahead forecast
            last_y = float(sales_history[-1]) if sales_history else 25.0
            r7_vals = sales_history[-7:] if len(sales_history) >= 7 else sales_history
            roll_7 = float(np.mean(r7_vals))
            lag_7 = float(sales_history[-7]) if len(sales_history) >= 7 else last_y
            
            # Same weekday 4w average
            if len(sales_history) >= 28:
                w4_vals = [sales_history[-7*k] for k in [1, 2, 3, 4] if len(sales_history) >= 7*k]
                weekday4w = float(np.mean(w4_vals)) if w4_vals else roll_7
            else:
                weekday4w = roll_7

            feat_row = pd.DataFrame([{
                "article_cat": ref_article,
                "day_of_week": dow_idx,
                "month": now.month,
                "is_tourist_season": 1 if now.month in [7, 8] else 0,
                "y_lag_1": last_y,
                "y_roll_7": roll_7,
                "y_lag_7_cal": lag_7,
                "pred_weekday4w_cal": weekday4w,
                "is_pub_holiday": 0,
                "is_pub_holiday_window": 0,
                "is_bridge_day": 0,
                "is_school_holiday": 0,
            }])
            feat_row["article_cat"] = feat_row["article_cat"].astype("category")

            pred_raw = float(self.gbdt_model.predict(feat_row[FEATS_MODEL_IV])[0])
            predicted_demand = max(1, int(round(pred_raw)))

            explanation = (
                f"GBDT Model (iv) active: {days_of_data} days observed. Day-ahead demand trained on historical seasonality and calendar features. "
                f"Safety stock derived from Newsvendor critical ratio (z={z_val:.2f}, SL={cr_val:.0%}, sigma={sigma:.2f})."
            )

            if is_perishable and current_stock > (predicted_demand * 1.6):
                risk_level = "high"
                explanation += " Warning: current stock exceeds forecast demand (waste risk)."
            elif current_stock < (predicted_demand * 0.4):
                risk_level = "medium"
                explanation += " Stock low — replenishment order advised."
            else:
                risk_level = "normal"

            historical_7d = [
                {"day": day_names[(dow_idx - 7 + i) % 7], "date": (now - timedelta(days=7 - i)).strftime("%Y-%m-%d"), "sales": int(sales_history[-7+i]) if len(sales_history) >= 7 else int(predicted_demand * 0.9)}
                for i in range(7)
            ]
            # FIX 19: Labeled indicative
            forecast_7d = [
                {"day": day_names[(dow_idx + i) % 7], "date": (now + timedelta(days=i)).strftime("%Y-%m-%d"), "predicted": max(1, int(round(predicted_demand * (1.15 if (dow_idx + i) % 7 in [4, 5, 6] else 0.95)))), "type": "indicative"}
                for i in range(7)
            ]

            return {
                "predictedDemand": predicted_demand,
                "safetyStock": safety_stock,
                "riskLevel": risk_level,
                "explanation": explanation,
                "tier": "gbdt_model_iv",
                "historical_7d": historical_7d,
                "forecast_7d": forecast_7d,
            }

        # 2. BENCHMARK / BLEND PATH (Sparse Cold-Start or Legacy Primary)
        raw_cat = item.get("category", "Bakery")
        norm_cat = "Breads & Baguettes"
        for k in ["viennoiserie", "croissant"]:
            if k in raw_cat.lower(): norm_cat = "Viennoiserie"; break
        for k in ["patisserie", "dessert", "cookie"]:
            if k in raw_cat.lower(): norm_cat = "Patisserie / Desserts"; break
        for k in ["beverage", "drink", "coffee", "dairy", "milk"]:
            if k in raw_cat.lower(): norm_cat = "Beverages & Sweets"; break

        # Category p90 prior
        dow_str = str(dow_idx)
        cat_data = self.category_priors.get(norm_cat, {})
        p90_prior = float(cat_data.get(dow_str, {}).get("p90", 2.0))

        # FIX 17: Own-data path for real-store items (never reads French reference if not replayed)
        is_replayed = bool(item.get("replayed_dataset") or item.get("source") == "replayed_dataset")

        if not is_replayed and days_of_data >= 28:
            # FIX 17: Real store >= 28 days uses own-data blend (mean of last 4 same weekdays + 7-day rolling mean)
            w4_vals = [sales_history[-7*k] for k in [1, 2, 3, 4] if len(sales_history) >= 7*k]
            weekday4w = float(np.mean(w4_vals)) if w4_vals else float(np.mean(sales_history[-7:]))
            roll_7 = float(np.mean(sales_history[-7:]))
            predicted_demand = max(1, int(round(0.60 * weekday4w + 0.40 * roll_7)))
            own_sigma = float(np.std(sales_history[-28:])) if len(sales_history) >= 28 else 3.0
            safety_stock, z_val, cr_val = self.compute_safety_stock(price=price, sigma=max(1.0, own_sigma))
            explanation = f"Own-data blend active ({days_of_data} days observed). Blended 4-week weekday ({weekday4w:.1f}) and 7-day pace ({roll_7:.1f}). Safety stock derived from Newsvendor critical ratio (SL={cr_val:.0%}, sigma={own_sigma:.1f})."
            tier = "own_data_blend"
        elif days_of_data < 28 or not ref_article:
            # Credibility shrinkage W = n / (n + 14)
            n = days_of_data
            k = 14.0
            W = n / (n + k)

            if n == 0:
                # Synchronized cold-start prior
                cat_prior = CATEGORY_PRIORS.get(raw_cat, CATEGORY_PRIORS.get("Other", {"predictedDemand": 20, "safetyStock": 4}))
                predicted_demand = cat_prior["predictedDemand"]
                safety_stock = cat_prior["safetyStock"]
                explanation = f"Cold start active: initialized to {raw_cat} prior ({predicted_demand} units, {safety_stock} safety stock)."
            else:
                series = np.array(sales_history, dtype=float)
                tsb_val = self.tsb_forecast(series)
                blended = (W * tsb_val) + ((1 - W) * p90_prior)
                predicted_demand = max(1, int(round(blended)))
                safety_stock = max(1, int(round(predicted_demand * 0.25)))
                explanation = f"Sparse TSB model active: {n} days observed. Blended {W:.0%} item pace with {norm_cat} prior."

            tier = "sparse_cold_start"
        else:
            # Replayed store legacy primary benchmark (historical mean + weekend factor)
            art_df = self.historical_ref[self.historical_ref["article"] == ref_article].sort_values("ds")
            last_30 = art_df.tail(30)["y"]
            base_demand = int(last_30.mean()) if len(last_30) > 0 else 25
            daily_std = float(last_30.std()) if len(last_30) > 0 else 4.5

            is_weekend = dow_idx in [4, 5, 6]
            dow_mean = art_df[art_df["ds"].dt.dayofweek == dow_idx]["y"].mean()
            overall_mean = art_df["y"].mean()
            trend_factor = (dow_mean / overall_mean) if overall_mean > 0 else 1.05

            predicted_demand = max(5, int(round(base_demand * trend_factor)))
            safety_stock = max(2, int(round(1.65 * daily_std)))
            explanation = f"Legacy benchmark active for {item_name}: {'weekend surge pattern' if is_weekend else 'weekday baseline'}."
            tier = "legacy_primary"

        if is_perishable and current_stock > (predicted_demand * 1.6):
            risk_level = "high"
            explanation += " Warning: current stock exceeds demand."
        elif current_stock < (predicted_demand * 0.4):
            risk_level = "medium"
            explanation += " Stock low — restock recommended."
        else:
            risk_level = "normal"

        historical_7d = [
            {"day": day_names[(dow_idx - 7 + i) % 7], "date": (now - timedelta(days=7 - i)).strftime("%Y-%m-%d"), "sales": int(sales_history[-7+i]) if len(sales_history) >= 7 else int(predicted_demand * 0.8)}
            for i in range(7)
        ]
        # FIX 19: Labeled indicative
        forecast_7d = [
            {"day": day_names[(dow_idx + i) % 7], "date": (now + timedelta(days=i)).strftime("%Y-%m-%d"), "predicted": max(1, int(round(predicted_demand * (1.15 if (dow_idx + i) % 7 in [4, 5, 6] else 0.95)))), "type": "indicative"}
            for i in range(7)
        ]

        return {
            "predictedDemand": predicted_demand,
            "safetyStock": safety_stock,
            "riskLevel": risk_level,
            "explanation": explanation,
            "tier": tier,
            "historical_7d": historical_7d,
            "forecast_7d": forecast_7d,
        }
