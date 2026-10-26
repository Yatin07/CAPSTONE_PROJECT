import numpy as np
import pandas as pd
import scipy.stats as stats
from pathlib import Path
from prophet import Prophet
from sklearn.ensemble import HistGradientBoostingRegressor
import warnings, logging

logging.getLogger('cmdstanpy').setLevel(logging.ERROR)
logging.getLogger('prophet').setLevel(logging.ERROR)
warnings.filterwarnings('ignore')

def run_bias_aware_simulation():
    data_path = Path("e:/CAP/ML/data/processed/primary_items.csv")
    df = pd.read_csv(data_path)
    df['ds'] = pd.to_datetime(df['ds'])
    df = df.sort_values(['article', 'ds']).reset_index(drop=True)

    unit_prices = {}
    if 'unit_price' in df.columns:
        clean_prices = df.groupby('article')['unit_price'].first().to_dict()
        for k, v in clean_prices.items():
            try:
                unit_prices[str(k)] = float(str(v).replace('€', '').replace(',', '.').strip())
            except Exception:
                unit_prices[str(k)] = 1.15
    else:
        for k in df['article'].unique():
            unit_prices[str(k)] = 1.15

    df['day_of_week'] = df['ds'].dt.dayofweek
    df['month'] = df['ds'].dt.month
    df['is_tourist_season'] = df['month'].isin([7, 8]).astype(int)

    lookup = df.set_index(['article', 'ds'])['y'].to_dict()
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

    df['pred_snaive_cal'] = [get_snaive(a, d) for a, d in zip(df['article'], df['ds'])]
    df['pred_weekday4w_cal'] = [get_weekday4w(a, d) for a, d in zip(df['article'], df['ds'])]
    for k in [1, 2, 3, 4]:
        df[f'y_lag_{7*k}_cal'] = [lookup.get((art, d - pd.Timedelta(days=7*k)), np.nan) for art, d in zip(df['article'], df['ds'])]

    df['y_lag_1'] = df.groupby('article')['y'].shift(1)
    df['y_roll_7'] = df.groupby('article')['y'].shift(1).rolling(7, min_periods=3).mean()

    max_date = df['ds'].max()
    sim_start_date = max_date - pd.Timedelta(days=89)
    print(f"Simulation Period: {sim_start_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')} (90 days)")

    components_list = []
    for item, group in df.groupby('article'):
        train_group = group[group['ds'] < sim_start_date]
        if len(train_group) < 30:
            continue
        m = Prophet(seasonality_mode='multiplicative', yearly_seasonality=True, weekly_seasonality=True)
        m.add_country_holidays(country_name='FR')
        m.add_regressor('is_tourist_season')
        m.fit(train_group[['ds', 'y', 'is_tourist_season']])

        forecast = m.predict(group[['ds', 'is_tourist_season']])
        cols = ['ds', 'trend', 'weekly', 'yearly', 'holidays', 'is_tourist_season', 'yhat']
        for c in ['weekly', 'yearly', 'holidays', 'is_tourist_season']:
            if c not in forecast.columns:
                forecast[c] = 0.0

        res = forecast[cols].copy()
        res['article'] = item
        components_list.append(res)

    components_df = pd.concat(components_list, ignore_index=True)
    df_merged = pd.merge(df, components_df, on=['article', 'ds'], suffixes=('', '_prophet'))
    df_merged['article_cat'] = df_merged['article'].astype('category')

    train_df = df_merged[df_merged['ds'] < sim_start_date].copy()
    sim_df = df_merged[df_merged['ds'] >= sim_start_date].copy()

    lag_feats = ['day_of_week', 'month', 'is_tourist_season', 'y_lag_7_cal', 'pred_weekday4w_cal']
    prophet_cols = ['trend', 'weekly', 'yearly', 'holidays', 'is_tourist_season_prophet', 'yhat']
    features_h = ['article_cat'] + lag_feats + prophet_cols

    train_clean = train_df.dropna(subset=features_h + ['y']).copy()
    gbdt = HistGradientBoostingRegressor(categorical_features=[0], learning_rate=0.05, max_iter=200, max_depth=6, random_state=42)
    gbdt.fit(train_clean[features_h], train_clean['y'])

    train_clean['pred_hybrid'] = np.maximum(gbdt.predict(train_clean[features_h]), 0.0)
    train_clean['pred_prophet_only'] = np.maximum(train_clean['yhat'], 0.0)
    train_clean['pred_snaive'] = np.maximum(train_clean['pred_snaive_cal'], 0.0)
    train_clean['pred_ma7'] = np.maximum(train_clean['y_roll_7'], 0.0)

    # Calculate residual sigmas and training biases
    sigmas = {}
    biases = {}
    models_eval = ['pred_prophet_only', 'pred_hybrid', 'pred_ma7', 'pred_snaive']
    for m_col in models_eval:
        sigmas[m_col] = train_clean.groupby('article').apply(
            lambda x: float(np.std(x['y'] - x[m_col], ddof=1)) if len(x) > 2 else 1.0
        ).to_dict()
        biases[m_col] = train_clean.groupby('article').apply(
            lambda x: float(np.mean(x['y'] - x[m_col])) if len(x) > 2 else 0.0
        ).to_dict()

    sim_df['pred_prophet_only'] = np.maximum(sim_df['yhat'], 0.0)
    sim_df['pred_hybrid'] = np.maximum(gbdt.predict(sim_df[features_h]), 0.0)
    sim_df['pred_snaive'] = np.maximum(sim_df['pred_snaive_cal'], 0.0)
    sim_df['pred_ma7'] = np.maximum(sim_df['y_roll_7'], 0.0)

    sim_df['unit_price'] = sim_df['article'].astype(str).map(unit_prices).fillna(1.15).astype(float)
    total_demand = sim_df['y'].sum()

    policies = [
        {'name': 'Fixed z = 0.0', 'z': 0.0, 'cogs': 0.40, 'type': 'fixed'},
        {'name': 'Fixed z = 0.5', 'z': 0.5, 'cogs': 0.40, 'type': 'fixed'},
        {'name': 'Fixed z = 1.0', 'z': 1.0, 'cogs': 0.40, 'type': 'fixed'},
        {'name': 'Fixed z = 1.65', 'z': 1.65, 'cogs': 0.40, 'type': 'fixed'},
        {'name': 'Critical Ratio (COGS=40% Base)', 'z': float(stats.norm.ppf(0.60)), 'cogs': 0.40, 'type': 'critical_ratio'},
    ]

    out_records = []
    for bias_mode in [False, True]:
        for sl in [1, 2]:
            for pol in policies:
                z = pol['z']
                cogs_pct = pol['cogs']
                pol_name = pol['name']

                for m_col in models_eval:
                    sig_dict = sigmas[m_col]
                    bias_dict = biases[m_col]

                    sku_dfs = []
                    for article, sku_data in sim_df.groupby('article'):
                        sku_data = sku_data.sort_values('ds').copy()
                        sig = sig_dict.get(article, 1.0)
                        bias = bias_dict.get(article, 0.0) if bias_mode else 0.0
                        u_price = unit_prices.get(str(article), 1.15)
                        u_cogs = u_price * cogs_pct

                        orders = []
                        sales = []
                        wastes = []
                        stockouts = []
                        carryover = 0.0

                        for _, row in sku_data.iterrows():
                            demand = row['y']
                            raw_pred = row[m_col]
                            pred = max(0.0, raw_pred + bias)
                            target_order = max(0.0, np.round(pred + z * sig))

                            if sl == 1:
                                order_placed = target_order
                                sale = min(demand, order_placed)
                                waste = max(0.0, order_placed - demand)
                                stockout = max(0.0, demand - order_placed)
                                carryover = 0.0
                            else:
                                order_placed = max(0.0, target_order - carryover)
                                sold_from_carryover = min(demand, carryover)
                                rem_demand = demand - sold_from_carryover
                                waste = carryover - sold_from_carryover
                                sold_from_fresh = min(rem_demand, order_placed)
                                stockout = max(0.0, rem_demand - sold_from_fresh)
                                sale = sold_from_carryover + sold_from_fresh
                                carryover = order_placed - sold_from_fresh

                            orders.append(order_placed)
                            sales.append(sale)
                            wastes.append(waste)
                            stockouts.append(stockout)

                        sku_data['order_placed'] = orders
                        sku_data['sale'] = sales
                        sku_data['waste'] = wastes
                        sku_data['stockout'] = stockouts
                        sku_data['cogs'] = u_cogs
                        sku_dfs.append(sku_data)

                    sim_out = pd.concat(sku_dfs, ignore_index=True)
                    tot_orders = sim_out['order_placed'].sum()
                    tot_sales = sim_out['sale'].sum()
                    tot_waste = sim_out['waste'].sum()
                    tot_stockout = sim_out['stockout'].sum()
                    stockout_days = (sim_out['stockout'] > 0).sum()
                    service_level = (1.0 - (stockout_days / len(sim_out))) * 100.0
                    waste_pct = (tot_waste / max(tot_orders, 1.0)) * 100.0
                    stockout_pct = (tot_stockout / total_demand) * 100.0
                    revenue = (sim_out['sale'] * sim_out['unit_price']).sum()
                    cogs_total = (sim_out['order_placed'] * sim_out['cogs']).sum()
                    gross_profit = revenue - cogs_total

                    out_records.append({
                        'bias_adjusted': bias_mode,
                        'shelf_life_days': sl,
                        'policy_name': pol_name,
                        'safety_factor_z': round(z, 4),
                        'model_key': m_col,
                        'orders': int(tot_orders),
                        'sales': int(tot_sales),
                        'waste_units': int(tot_waste),
                        'waste_pct': round(waste_pct, 2),
                        'stockout_units': int(tot_stockout),
                        'stockout_rate_pct': round(stockout_pct, 2),
                        'service_level_pct': round(service_level, 2),
                        'gross_profit_eur': round(gross_profit, 2),
                    })

    res_df = pd.DataFrame(out_records)
    res_df.to_csv("e:/CAP/scratch/bias_aware_simulation_results.csv", index=False)
    print("Saved e:/CAP/scratch/bias_aware_simulation_results.csv")
    
    # Print comparison table for CR policy (COGS=40%)
    print("\n--- COMPARISON: Raw Simulation vs Bias-Aware Simulation (Shelf Life = 1 Day, CR Policy) ---")
    cr_comp = res_df[(res_df['shelf_life_days'] == 1) & (res_df['policy_name'] == 'Critical Ratio (COGS=40% Base)')]
    for m in models_eval:
        raw_row = cr_comp[(cr_comp['model_key'] == m) & (~cr_comp['bias_adjusted'])].iloc[0]
        adj_row = cr_comp[(cr_comp['model_key'] == m) & (cr_comp['bias_adjusted'])].iloc[0]
        print(f"Model: {m:<18}")
        print(f"  Raw:         Waste={raw_row['waste_units']:>5} ({raw_row['waste_pct']:>5.1f}%) | Stockout={raw_row['stockout_units']:>5} ({raw_row['stockout_rate_pct']:>4.1f}%) | ServLvl={raw_row['service_level_pct']:>5.1f}% | Profit=€{raw_row['gross_profit_eur']:>9.2f}")
        print(f"  Bias-Aware:  Waste={adj_row['waste_units']:>5} ({adj_row['waste_pct']:>5.1f}%) | Stockout={adj_row['stockout_units']:>5} ({adj_row['stockout_rate_pct']:>4.1f}%) | ServLvl={adj_row['service_level_pct']:>5.1f}% | Profit=€{adj_row['gross_profit_eur']:>9.2f}")
        print(f"  Delta:       Waste={adj_row['waste_units']-raw_row['waste_units']:>+5} units | Stockout={adj_row['stockout_units']-raw_row['stockout_units']:>+5} units | Profit=€{adj_row['gross_profit_eur']-raw_row['gross_profit_eur']:>+9.2f}\n")

if __name__ == '__main__':
    run_bias_aware_simulation()
