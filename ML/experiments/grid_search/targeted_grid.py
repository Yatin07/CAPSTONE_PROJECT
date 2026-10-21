import pandas as pd
import numpy as np
import itertools
from prophet import Prophet
from sklearn.ensemble import HistGradientBoostingRegressor
import multiprocessing as mp
import time
import warnings
import logging
warnings.filterwarnings('ignore')

logging.getLogger('cmdstanpy').setLevel(logging.ERROR)
logging.getLogger('prophet').setLevel(logging.ERROR)

def fit_predict_prophet(args):
    df_train, df_val, cps, sps, sm = args
    m = Prophet(changepoint_prior_scale=cps, seasonality_prior_scale=sps, seasonality_mode=sm)
    m.add_regressor('is_tourist_season')
    if 'holiday' in df_train.columns:
         m.add_country_holidays(country_name='FR')
         
    m.fit(df_train)
    pred_train = m.predict(df_train)
    pred_val = m.predict(df_val)
    return pred_train, pred_val

def worker_init():
    import warnings
    warnings.filterwarnings('ignore')

if __name__ == '__main__':
    print("Starting Targeted Grid Search with Corrected Features...")
    start_time = time.time()
    
    df = pd.read_csv('E:/CAP/ML/data/processed/primary_items.csv')
    df['ds'] = pd.to_datetime(df['ds'])
    df['day_of_week'] = df['ds'].dt.dayofweek
    df['month'] = df['ds'].dt.month
    
    if 'is_tourist_season' not in df.columns:
        df['is_tourist_season'] = df['ds'].dt.month.isin([7, 8]).astype(int)
    
    folds = [
        (pd.to_datetime('2022-05-01'), pd.to_datetime('2022-06-01')),
        (pd.to_datetime('2022-06-01'), pd.to_datetime('2022-07-01'))
    ]
    
    # The top 10 from flawed grid, plus the manual baseline
    configs = [
        # cps, sps, sm, max_depth, lr, max_iter
        (0.05, 0.1, 'multiplicative', None, 0.1, 100), # MANUAL BASELINE (Control)
        (0.01, 10.0, 'additive', 5, 0.1, 200),
        (0.01, 1.0, 'multiplicative', 5, 0.2, 50),
        (0.05, 10.0, 'additive', 5, 0.1, 50),
        (0.01, 1.0, 'multiplicative', 5, 0.1, 100),
        (0.01, 0.1, 'additive', 5, 0.2, 50),
        (0.10, 10.0, 'additive', 7, 0.2, 200),
        (0.10, 0.1, 'multiplicative', 7, 0.1, 50),
        (0.05, 1.0, 'multiplicative', 5, 0.2, 50),
        (0.10, 10.0, 'multiplicative', 7, 0.1, 200),
        (0.01, 10.0, 'multiplicative', 5, 0.1, 50),
        # Also test top grid config but with unrestricted tree
        (0.01, 10.0, 'additive', None, 0.1, 200)
    ]
    
    # Unique Prophet configs
    prophet_configs = list(set([(c[0], c[1], c[2]) for c in configs]))
    
    df = df.sort_values(['article', 'ds']).reset_index(drop=True)
    df['lag_1'] = df.groupby('article')['y'].shift(1)
    df['lag_7'] = df.groupby('article')['y'].shift(7)
    df['rolling_7'] = df.groupby('article')['y'].transform(lambda x: x.shift(1).rolling(7).mean())
    df = df.dropna().reset_index(drop=True)
    
    articles = df['article'].unique()
    results = []
    
    pool = mp.Pool(mp.cpu_count(), initializer=worker_init)
    
    # Store prophet results for reuse
    fold_prophet_preds = {0: {}, 1: {}}
    
    for cps, sps, sm in prophet_configs:
        for f_idx, (split_start, split_end) in enumerate(folds):
            df_train_full = df[df['ds'] < split_start].copy()
            df_val_full = df[(df['ds'] >= split_start) & (df['ds'] < split_end)].copy()
            
            tasks = []
            for art in articles:
                df_train_art = df_train_full[df_train_full['article'] == art][['ds', 'y', 'is_tourist_season']]
                df_val_art = df_val_full[df_val_full['article'] == art][['ds', 'y', 'is_tourist_season']]
                tasks.append((df_train_art, df_val_art, cps, sps, sm))
            
            prophet_res = pool.map(fit_predict_prophet, tasks)
            
            train_preds = []
            val_preds = []
            for i, (p_tr, p_va) in enumerate(prophet_res):
                art = articles[i]
                p_tr['article'] = art
                p_va['article'] = art
                train_preds.append(p_tr)
                val_preds.append(p_va)
                
            df_train_p = pd.concat(train_preds)
            df_val_p = pd.concat(val_preds)
            
            fold_prophet_preds[f_idx][(cps, sps, sm)] = (df_train_p, df_val_p)

    for cfg in configs:
        cps, sps, sm, md, lr, mi = cfg
        wapes = []
        for f_idx, (split_start, split_end) in enumerate(folds):
            df_train_full = df[df['ds'] < split_start].copy()
            df_val_full = df[(df['ds'] >= split_start) & (df['ds'] < split_end)].copy()
            
            df_train_p, df_val_p = fold_prophet_preds[f_idx][(cps, sps, sm)]
            
            p_cols = ['ds', 'article', 'yhat', 'trend', 'weekly']
            if 'yearly' in df_train_p.columns:
                p_cols.append('yearly')
                
            train_merged = pd.merge(df_train_full, df_train_p[p_cols], on=['ds', 'article'])
            val_merged = pd.merge(df_val_full, df_val_p[p_cols], on=['ds', 'article'])
            
            # CORRECTED FEATURES
            features = ['lag_1', 'lag_7', 'rolling_7', 'trend', 'weekly', 'is_tourist_season', 'day_of_week', 'month']
            if 'yearly' in p_cols:
                features.append('yearly')
                
            train_merged['article'] = train_merged['article'].astype('category')
            val_merged['article'] = val_merged['article'].astype('category')
            features.append('article')
            
            X_train = train_merged[features]
            y_train = train_merged['y']
            X_val = val_merged[features]
            y_val = val_merged['y']
            
            hgb = HistGradientBoostingRegressor(max_depth=md, learning_rate=lr, max_iter=mi, categorical_features=[features.index('article')])
            hgb.fit(X_train, y_train)
            xgb_pred = hgb.predict(X_val)
            xgb_pred = np.maximum(0, xgb_pred)
            
            wape = np.sum(np.abs(y_val - xgb_pred)) / np.sum(y_val)
            wapes.append(wape)
            
        mean_wape = np.mean(wapes)
        is_baseline = (cfg == (0.05, 0.1, 'multiplicative', None, 0.1, 100))
        results.append({
            'Config': 'BASELINE' if is_baseline else 'GRID',
            'Prophet': f"CPS={cps}, SPS={sps}, SM={sm}",
            'XGB': f"MD={md}, LR={lr}, Iter={mi}",
            'CV WAPE': round(mean_wape * 100, 2),
            'Split WAPEs': str([round(w * 100, 2) for w in wapes])
        })
            
    pool.close()
    pool.join()
    
    res_df = pd.DataFrame(results).sort_values('CV WAPE')
    print("\nTargeted Test Results (Corrected Features):")
    print(res_df.to_string(index=False))
