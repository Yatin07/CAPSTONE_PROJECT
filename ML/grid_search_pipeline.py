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

# Disable Prophet logging
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
    print("Starting Grid Search...")
    start_time = time.time()
    
    df = pd.read_csv('E:/CAP/ML/data/processed/primary_items.csv')
    df['ds'] = pd.to_datetime(df['ds'])
    
    if 'is_tourist_season' not in df.columns:
        df['is_tourist_season'] = df['ds'].dt.month.isin([7, 8]).astype(int)
    
    folds = [
        (pd.to_datetime('2022-05-01'), pd.to_datetime('2022-06-01')),
        (pd.to_datetime('2022-06-01'), pd.to_datetime('2022-07-01'))
    ]
    
    prophet_params = list(itertools.product(
        [0.01, 0.05, 0.1, 0.3, 0.5], 
        [0.1, 1, 10], 
        ['additive', 'multiplicative']
    ))
    
    xgb_params = list(itertools.product(
        [3, 5, 7], 
        [0.01, 0.1, 0.2], 
        [50, 100, 200]
    ))
    
    df = df.sort_values(['article', 'ds']).reset_index(drop=True)
    df['lag_1'] = df.groupby('article')['y'].shift(1)
    df['lag_7'] = df.groupby('article')['y'].shift(7)
    df['rolling_7'] = df.groupby('article')['y'].transform(lambda x: x.shift(1).rolling(7).mean())
    df = df.dropna().reset_index(drop=True)
    
    articles = df['article'].unique()
    results = []
    
    pool = mp.Pool(mp.cpu_count(), initializer=worker_init)
    
    for cps, sps, sm in prophet_params:
        prophet_fold_wapes = []
        xgb_fold_wapes = {xgb_p: [] for xgb_p in xgb_params}
        
        for split_start, split_end in folds:
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
            
            # Conditionally handle 'yearly'
            p_cols = ['ds', 'article', 'yhat', 'trend', 'weekly']
            if 'yearly' in df_train_p.columns:
                p_cols.append('yearly')
            
            train_merged = pd.merge(df_train_full, df_train_p[p_cols], on=['ds', 'article'])
            val_merged = pd.merge(df_val_full, df_val_p[p_cols], on=['ds', 'article'])
            
            prophet_wape = np.sum(np.abs(val_merged['y'] - val_merged['yhat'])) / np.sum(val_merged['y'])
            prophet_fold_wapes.append(prophet_wape)
            
            features = ['lag_1', 'lag_7', 'rolling_7', 'trend', 'weekly', 'is_tourist_season']
            if 'yearly' in p_cols:
                features.append('yearly')
                
            train_merged['article'] = train_merged['article'].astype('category')
            val_merged['article'] = val_merged['article'].astype('category')
            features.append('article')
            
            X_train = train_merged[features]
            y_train = train_merged['y']
            X_val = val_merged[features]
            y_val = val_merged['y']
            
            for md, lr, mi in xgb_params:
                hgb = HistGradientBoostingRegressor(max_depth=md, learning_rate=lr, max_iter=mi, categorical_features=[features.index('article')])
                hgb.fit(X_train, y_train)
                xgb_pred = hgb.predict(X_val)
                xgb_pred = np.maximum(0, xgb_pred)
                
                wape = np.sum(np.abs(y_val - xgb_pred)) / np.sum(y_val)
                xgb_fold_wapes[(md, lr, mi)].append(wape)
                
        mean_prophet_wape = np.mean(prophet_fold_wapes)
        
        for xgb_p, wapes in xgb_fold_wapes.items():
            mean_wape = np.mean(wapes)
            results.append({
                'cps': cps, 'sps': sps, 'sm': sm,
                'md': xgb_p[0], 'lr': xgb_p[1], 'mi': xgb_p[2],
                'cv_wape': mean_wape
            })
            
    pool.close()
    pool.join()
    
    res_df = pd.DataFrame(results)
    res_df = res_df.sort_values('cv_wape').reset_index(drop=True)
    res_df.to_csv('E:/CAP/ML/grid_search_results.csv', index=False)
    
    print(f"\nGrid Search Completed in {time.time()-start_time:.1f}s")
    print("Top 10 Combinations:")
    print(res_df.head(10).to_string())
