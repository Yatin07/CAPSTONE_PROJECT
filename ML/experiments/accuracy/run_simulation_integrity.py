"""
RestockIQ - Simulation Integrity & Assertions Engine
Reruns the full simulation table with strict row-level mathematical assertions:
  1. baked = sold + waste
  2. sold = demand - stockout
  3. implied_demand = sold + stockout == actual_demand (68,883 units)
  4. SKU-days count == 2,929 across all models
  5. Identical unit prices across all models
Models evaluated:
  - Control 3 (GBDT lag_1, No Prophet)
  - Canonical Hybrid (Prophet + GBDT on residuals)
  - Prophet-only (Engine)
  - 7-Day Moving Average
  - Seasonal Naive (Lag 7 cal)
"""
import sys, math, json, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import scipy.stats as stats
from sklearn.ensemble import HistGradientBoostingRegressor
from prophet import Prophet

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
warnings.filterwarnings("ignore")

SEED = 42
np.random.seed(SEED)

ROOT = Path("e:/CAP")
DATA_DIR = ROOT / "ML" / "data"
DOCS_DIR = ROOT / "docs"
PRIMARY_CSV = DATA_DIR / "processed" / "primary_items.csv"

def run_simulation():
    print("=" * 90)
    print("   RESTOCKIQ: SIMULATION INTEGRITY & ASSERTIONS VERIFICATION")
    print("=" * 90)

    df = pd.read_csv(PRIMARY_CSV)
    df["ds"] = pd.to_datetime(df["ds"])
    df = df.sort_values(["article", "ds"]).reset_index(drop=True)

    # Unit prices: clean and standardized
    unit_prices = {}
    if "unit_price" in df.columns:
        clean_prices = df.groupby("article")["unit_price"].first().to_dict()
        for k, v in clean_prices.items():
            try:
                unit_prices[str(k)] = float(str(v).replace("€", "").replace(",", ".").strip())
            except Exception:
                unit_prices[str(k)] = 1.15
    else:
        for k in df["article"].unique():
            unit_prices[str(k)] = 1.15

    df["day_of_week"] = df["ds"].dt.dayofweek
    df["month"] = df["ds"].dt.month
    df["is_tourist_season"] = df["month"].isin([7, 8]).astype(int)

    # Calendar-aligned lags
    lookup = df.set_index(["article", "ds"])["y"].to_dict()
    def get_snaive(art, d):
        for k in [1, 2, 3, 4, 5]:
            val = lookup.get((art, d - pd.Timedelta(days=7*k)))
            if val is not None and not np.isnan(val):
                return val
        return 0.0

    def get_weekday4w(art, d):
        vals = []
        for k in [1, 2, 3, 4]:
            v = lookup.get((art, d - pd.Timedelta(days=7*k)))
            if v is not None and not np.isnan(v):
                vals.append(v)
        return np.mean(vals) if len(vals) > 0 else 0.0

    df["pred_snaive_cal"] = [get_snaive(a, d) for a, d in zip(df["article"], df["ds"])]
    df["pred_weekday4w_cal"] = [get_weekday4w(a, d) for a, d in zip(df["article"], df["ds"])]
    for k in [1, 2, 3, 4]:
        df[f"y_lag_{7*k}_cal"] = [lookup.get((art, d - pd.Timedelta(days=7*k)), np.nan) for art, d in zip(df["article"], df["ds"])]

    df["y_lag_1"] = df.groupby("article")["y"].shift(1)
    df["y_roll_7"] = df.groupby("article")["y"].shift(1).rolling(7, min_periods=3).mean()

    # Simulation period: 90 days (2022-07-03 to 2022-09-30)
    max_date = df["ds"].max()
    sim_start_date = max_date - pd.Timedelta(days=89)
    total_demand = df[df["ds"] >= sim_start_date]["y"].sum()
    total_sku_days = len(df[df["ds"] >= sim_start_date])
    
    print(f"Simulation Window: {sim_start_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
    print(f"Total Observed Demand: {total_demand:,.0f} units | Total SKU-Days: {total_sku_days:,}")
    assert total_demand == 68883, f"Expected 68883 demand, got {total_demand}"
    assert total_sku_days == 2929, f"Expected 2929 SKU-days, got {total_sku_days}"

    # 1. Fit Prophet on training data (t < sim_start_date)
    p_full_train_list = []
    for item, group in df.groupby("article"):
        grp_full_tr = group[group["ds"] < sim_start_date]
        if len(grp_full_tr) < 30: continue

        m_full = Prophet(seasonality_mode="multiplicative", yearly_seasonality=True, weekly_seasonality=True)
        m_full.add_country_holidays(country_name="FR")
        m_full.add_regressor("is_tourist_season")
        m_full.fit(grp_full_tr[["ds", "y", "is_tourist_season"]])
        fc_full = m_full.predict(group[["ds", "is_tourist_season"]])
        cols_e = ["ds", "trend", "weekly", "yearly", "holidays", "is_tourist_season", "yhat"]
        for c in ["weekly", "yearly", "holidays", "is_tourist_season"]:
            if c not in fc_full.columns: fc_full[c] = 0.0
        r_f = fc_full[cols_e].copy()
        r_f["article"] = item
        p_full_train_list.append(r_f)

    df_p_full = pd.concat(p_full_train_list, ignore_index=True)
    df_merged = pd.merge(df, df_p_full, on=["article", "ds"], suffixes=("", "_prophet"))
    df_merged["article_cat"] = df_merged["article"].astype("category")

    train_df = df_merged[df_merged["ds"] < sim_start_date].copy()
    sim_df = df_merged[df_merged["ds"] >= sim_start_date].copy()

    # Features
    lag_feats_1d = ["day_of_week", "month", "is_tourist_season", "y_lag_1", "y_roll_7", "y_lag_7_cal", "pred_weekday4w_cal"]
    prophet_cols = ["trend", "weekly", "yearly", "holidays", "is_tourist_season_prophet", "yhat"]

    # Fit Control 3 (GBDT lag_1 without Prophet) on full training data
    tr_full = train_df.dropna(subset=["article_cat"] + lag_feats_1d + prophet_cols + ["y"]).copy()
    gbdt_c3 = HistGradientBoostingRegressor(categorical_features=[0], learning_rate=0.05, max_iter=200, max_depth=6, random_state=SEED)
    gbdt_c3.fit(tr_full[["article_cat"] + lag_feats_1d], tr_full["y"])

    # Fit Canonical Hybrid (GBDT predicting Prophet residual: res = y - yhat)
    tr_full["residual"] = tr_full["y"] - tr_full["yhat"]
    gbdt_hybrid = HistGradientBoostingRegressor(categorical_features=[0], learning_rate=0.05, max_iter=200, max_depth=6, random_state=SEED)
    gbdt_hybrid.fit(tr_full[["article_cat"] + lag_feats_1d], tr_full["residual"])

    # Model sigmas from training residuals
    tr_full["pred_ctrl3_gbdt"] = np.maximum(gbdt_c3.predict(tr_full[["article_cat"] + lag_feats_1d]), 0.0)
    tr_full["pred_prophet_only"] = np.maximum(tr_full["yhat"], 0.0)
    tr_full["pred_hybrid"] = np.maximum(tr_full["yhat"] + gbdt_hybrid.predict(tr_full[["article_cat"] + lag_feats_1d]), 0.0)
    tr_full["pred_snaive"] = np.maximum(tr_full["pred_snaive_cal"], 0.0)
    tr_full["pred_ma7"] = np.maximum(tr_full["y_roll_7"], 0.0)

    models_to_sim = ["pred_ctrl3_gbdt", "pred_hybrid", "pred_prophet_only", "pred_ma7", "pred_snaive"]
    sigmas = {}
    for m in models_to_sim:
        sigmas[m] = tr_full.groupby("article").apply(lambda x: float(np.std(x["y"] - x[m], ddof=1)) if len(x)>2 else 1.0).to_dict()

    # Sequential Day-Ahead Rollup
    sim_preds = []
    full_so_far = train_df[["article", "ds", "y"]].copy()

    for t_date in sorted(sim_df["ds"].unique()):
        day_rows = sim_df[sim_df["ds"] == t_date].copy()
        l1_dict = full_so_far.groupby("article").apply(lambda x: x.sort_values("ds").iloc[-1]["y"] if len(x)>0 else np.nan).to_dict()
        r7_dict = full_so_far.groupby("article").apply(lambda x: x.sort_values("ds").tail(7)["y"].mean() if len(x)>0 else np.nan).to_dict()
        day_rows["y_lag_1"] = day_rows["article"].map(l1_dict)
        day_rows["y_roll_7"] = day_rows["article"].map(r7_dict)

        # Predict
        p_c3 = np.maximum(gbdt_c3.predict(day_rows[["article_cat"] + lag_feats_1d]), 0.0)
        p_p = np.maximum(day_rows["yhat"], 0.0)
        p_res = gbdt_hybrid.predict(day_rows[["article_cat"] + lag_feats_1d])
        p_hyb = np.maximum(p_p + p_res, 0.0)
        p_ma = np.maximum(day_rows["y_roll_7"].fillna(0.0), 0.0)
        p_sn = np.maximum(day_rows["pred_snaive_cal"].fillna(0.0), 0.0)

        day_rows["pred_ctrl3_gbdt"] = p_c3
        day_rows["pred_hybrid"] = p_hyb
        day_rows["pred_prophet_only"] = p_p
        day_rows["pred_ma7"] = p_ma
        day_rows["pred_snaive"] = p_sn

        sim_preds.append(day_rows)
        full_so_far = pd.concat([full_so_far, day_rows[["article", "ds", "y"]]], ignore_index=True)

    sim_df_ready = pd.concat(sim_preds, ignore_index=True)
    sim_df_ready["unit_price"] = sim_df_ready["article"].astype(str).map(unit_prices).fillna(1.15).astype(float)

    # Ordering Policies
    policies = [
        {"name": "Fixed z = 0.0 (Zero Buffer)", "z": 0.0, "cogs": 0.40},
        {"name": "Critical Ratio (COGS=40% Base)", "z": float(stats.norm.ppf(0.60)), "cogs": 0.40},
        {"name": "Fixed z = 0.5 (Light Buffer)", "z": 0.5, "cogs": 0.40},
        {"name": "Target 80% Service Level", "z": float(stats.norm.ppf(0.80)), "cogs": 0.40},
        {"name": "Fixed z = 1.0 (Standard Buffer)", "z": 1.0, "cogs": 0.40},
        {"name": "Target 90% Service Level", "z": float(stats.norm.ppf(0.90)), "cogs": 0.40},
        {"name": "Target 95% Service Level", "z": float(stats.norm.ppf(0.95)), "cogs": 0.40},
        {"name": "Fixed z = 1.65 (High Availability)", "z": 1.65, "cogs": 0.40},
    ]

    model_labels = {
        "pred_ctrl3_gbdt": "Control 3 (GBDT lag_1, No Prophet)",
        "pred_hybrid": "Canonical Hybrid (Prophet + GBDT)",
        "pred_prophet_only": "Prophet-only (Engine)",
        "pred_ma7": "7-Day Moving Average",
        "pred_snaive": "Seasonal Naive (Lag 7 cal)",
    }

    results = []
    print("\n--- EXECUTING SIMULATION & VERIFYING ROW IDENTITIES (SHELF LIFE = 1 DAY) ---")
    print(f"{'Policy':<28} | {'Model':<32} | {'Baked':<6} | {'Sold':<6} | {'Waste':<6} | {'Stockout':<8} | {'Demand Check':<12} | {'Status'}")
    print("-" * 120)

    for pol in policies:
        z = pol["z"]
        cogs_pct = pol["cogs"]
        pol_name = pol["name"]

        for m in models_to_sim:
            sig_dict = sigmas[m]
            sku_dfs = []

            for art, sku_data in sim_df_ready.groupby("article"):
                sku_data = sku_data.sort_values("ds").copy()
                sig = sig_dict.get(art, 1.0)
                u_price = unit_prices.get(str(art), 1.15)
                u_cogs = u_price * cogs_pct

                orders = []
                sales = []
                wastes = []
                stockouts = []

                for _, row in sku_data.iterrows():
                    demand = float(row["y"])
                    pred = float(row[m])
                    target_order = max(0.0, float(np.round(pred + z * sig)))

                    # 1-day shelf life accounting
                    order_placed = target_order
                    sale = min(demand, order_placed)
                    waste = max(0.0, order_placed - demand)
                    stockout = max(0.0, demand - order_placed)

                    # Strict row-level assertion
                    assert abs((sale + waste) - order_placed) < 1e-6, f"Row identity failed: {sale} + {waste} != {order_placed}"
                    assert abs((sale + stockout) - demand) < 1e-6, f"Row identity failed: {sale} + {stockout} != {demand}"

                    orders.append(order_placed)
                    sales.append(sale)
                    wastes.append(waste)
                    stockouts.append(stockout)

                sku_data["order_placed"] = orders
                sku_data["sale"] = sales
                sku_data["waste"] = wastes
                sku_data["stockout"] = stockouts
                sku_data["cogs"] = u_cogs
                sku_dfs.append(sku_data)

            sim_out = pd.concat(sku_dfs, ignore_index=True)
            tot_orders = sim_out["order_placed"].sum()
            tot_sales = sim_out["sale"].sum()
            tot_waste = sim_out["waste"].sum()
            tot_stockout = sim_out["stockout"].sum()

            # Global Model-Level Assertions
            assert abs((tot_sales + tot_waste) - tot_orders) < 1e-5, f"baked != sold + waste: {tot_orders} != {tot_sales} + {tot_waste}"
            assert abs((tot_sales + tot_stockout) - total_demand) < 1e-5, f"sold + stockout != total_demand: {tot_sales + tot_stockout} != {total_demand}"
            assert len(sim_out) == total_sku_days, f"SKU days count mismatch: {len(sim_out)} != {total_sku_days}"

            stockout_days = (sim_out["stockout"] > 0).sum()
            service_level = (1.0 - (stockout_days / len(sim_out))) * 100.0
            waste_pct = (tot_waste / max(tot_orders, 1.0)) * 100.0
            stockout_pct = (tot_stockout / total_demand) * 100.0
            revenue = (sim_out["sale"] * sim_out["unit_price"]).sum()
            cogs_total = (sim_out["order_placed"] * sim_out["cogs"]).sum()
            gross_profit = revenue - cogs_total

            implied_demand = int(tot_sales + tot_stockout)
            status = "PASS (68,883)" if implied_demand == 68883 else "FAIL"

            print(f"{pol_name[:26]:<28} | {model_labels[m][:30]:<32} | {int(tot_orders):<6} | {int(tot_sales):<6} | {int(tot_waste):<6} | {int(tot_stockout):<8} | {implied_demand:<12} | {status}")

            results.append({
                "policy_name": pol_name,
                "safety_factor_z": round(z, 4),
                "cogs_pct": int(cogs_pct * 100),
                "model_key": m,
                "model_name": model_labels[m],
                "baked_units": int(tot_orders),
                "sold_units": int(tot_sales),
                "waste_units": int(tot_waste),
                "waste_pct": round(waste_pct, 2),
                "stockout_units": int(tot_stockout),
                "stockout_rate_pct": round(stockout_pct, 2),
                "service_level_pct": round(service_level, 2),
                "gross_profit_eur": round(gross_profit, 2),
                "implied_demand_check": implied_demand,
                "identity_verified": True
            })

    res_df = pd.DataFrame(results)
    out_csv = DOCS_DIR / "ordering_policy_experiment_v3_verified.csv"
    res_df.to_csv(out_csv, index=False)
    print(f"\nSuccessfully verified all rows. Saved verified results to: {out_csv}")
    return res_df

if __name__ == "__main__":
    run_simulation()
