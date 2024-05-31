import numpy as np
import pandas as pd
from arch import arch_model
import lightgbm as lgb
from sklearn.preprocessing import OneHotEncoder, RobustScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV, cross_val_score
import statsmodels.api as sm
import matplotlib.pyplot as plt
import shap
import os

# os.chdir('/Users/stella/Desktop/UBS')
#print(os.getcwd())

# Read data files
market_swap_rate = pd.read_csv("market-data-swap-rates.csv")
market_swaption_vols = pd.read_csv("market-data-swaption-vols.csv")
trade_info = pd.read_csv("trade-information.csv")
trade_vega = pd.read_csv("trade-price-ir-vegas.csv")

# Data preprocessing
def preprocess_data(market_swap_rate, market_swaption_vols, trade_info, trade_vega):
    # Convert the index to datetime
    market_swap_rate.index = pd.to_datetime(market_swap_rate.index)
    market_swaption_vols.index = pd.to_datetime(market_swaption_vols.index)
    trade_vega.index = pd.to_datetime(trade_vega.index)
    #print(type(market_swap_rate.index), type (market_swaption_vols.index), type(trade_vega.index))

    #Convert the index to a more specific format
    #print(market_swap_rate.dtypes)
    market_swap_rate['Start Date'] = market_swap_rate['Start Date'].astype(object)
    market_swap_rate['Tenor'] = market_swap_rate['Tenor'].astype(object)
    market_swap_rate['Swap Rate'] = market_swap_rate['Swap Rate'].astype(float)
    #print(market_swaption_vols.dtypes)
    market_swaption_vols['Expiry'] = market_swaption_vols['Expiry'].astype(object)
    market_swaption_vols['Tenor'] = market_swaption_vols['Tenor'].astype(object)
    market_swaption_vols['Strike'] = market_swaption_vols['Strike'].astype(object)
    market_swaption_vols['Vols'] = market_swaption_vols['Vols'].astype(float)
    #print(trade_vega.dtypes)
    vega_columns_to_convert1 = ['Value Date', 'Trade Name', 'Trade Currency', 'Expiry Bucket', 'Expiry Date', 'Tenor Bucket']
    for column in vega_columns_to_convert1:
        trade_vega[column] = trade_vega[column].astype(object)
    trade_vega['TV'] = trade_vega['TV'].astype(float)
    trade_vega['Vega'] = trade_vega['Vega'].astype(float)
    trade_vega['Zero Rate Shock'] = trade_vega['Zero Rate Shock'].astype(int)

    # Handle missing values and outliers
    market_swap_rate.select_dtypes(include=[np.number]).interpolate(method='time', inplace=True)
    market_swaption_vols.select_dtypes(include=[np.number]).interpolate(method='time', inplace=True)
    trade_vega.select_dtypes(include=[np.number]).interpolate(method='time', inplace=True)
    
    # Construct market data features
    market_swap_rate['momentum'] = market_swap_rate['Swap Rate'].pct_change()
    market_swap_rate['volatility'] = market_swap_rate['Swap Rate'].rolling(window=20).std()
    market_swap_rate['skew'] = market_swap_rate['Swap Rate'].rolling(window=20).skew()
    market_swap_rate['kurt'] = market_swap_rate['Swap Rate'].rolling(window=20).kurt()
    market_swap_rate['moving_avg'] = market_swap_rate['Swap Rate'].rolling(window=20).mean()
    market_swap_rate['exp_moving_avg'] = market_swap_rate['Swap Rate'].ewm(span=20).mean()
    
    # Standardize numeric features    
    numeric_cols = market_swap_rate.select_dtypes(include=['number']).columns
    scaler = RobustScaler()
    market_swap_rate_scaled = pd.DataFrame(scaler.fit_transform(market_swap_rate[numeric_cols]), columns=numeric_cols)
    market_swap_rate_scaled = market_swap_rate_scaled.join(market_swap_rate.select_dtypes(exclude=['number']), lsuffix='_left', rsuffix='_right')

    numeric_cols = market_swaption_vols.select_dtypes(include=['number']).columns
    scaler = RobustScaler()
    market_swaption_vols_scaled = pd.DataFrame(scaler.fit_transform(market_swaption_vols[numeric_cols]), columns=numeric_cols)
    market_swaption_vols_scaled = market_swaption_vols_scaled.join(market_swaption_vols.select_dtypes(exclude=['number']), lsuffix='_left', rsuffix='_right')

    numeric_cols = trade_info.select_dtypes(include=['number']).columns
    scaler = RobustScaler()
    trade_info_scaled = pd.DataFrame(scaler.fit_transform(trade_info[numeric_cols]), columns=numeric_cols)
    trade_info_scaled = trade_info_scaled.join(trade_info.select_dtypes(exclude=['number']), lsuffix='_left', rsuffix='_right')

    numeric_cols = trade_vega.select_dtypes(include=['number']).columns
    scaler = RobustScaler()
    trade_vega_scaled = pd.DataFrame(scaler.fit_transform(trade_vega[numeric_cols]), columns=numeric_cols)
    trade_vega_scaled = trade_vega_scaled.join(trade_vega.select_dtypes(exclude=['number']), lsuffix='_left', rsuffix='_right')

    # One-hot encode categorical features
    categorical_cols = market_swap_rate_scaled.select_dtypes(include=['object']).columns
    encoder = OneHotEncoder(handle_unknown='ignore')
    market_swap_rate_encoded = pd.DataFrame(encoder.fit_transform(market_swap_rate_scaled[categorical_cols]).toarray(), columns=encoder.get_feature_names_out(categorical_cols))
    market_swap_rate_encoded = market_swap_rate_encoded.join(market_swap_rate_scaled.select_dtypes(include=['number']))

    categorical_cols = market_swaption_vols_scaled.select_dtypes(include=['object']).columns
    encoder = OneHotEncoder(handle_unknown='ignore')
    market_swaption_vols_encoded = pd.DataFrame(encoder.fit_transform(market_swaption_vols_scaled[categorical_cols]).toarray(), columns=encoder.get_feature_names_out(categorical_cols))
    market_swaption_vols_encoded = market_swaption_vols_encoded.join(market_swaption_vols_scaled.select_dtypes(include=['number']))

    categorical_cols = trade_info_scaled.select_dtypes(include=['object']).columns
    encoder = OneHotEncoder(handle_unknown='ignore')
    trade_info_encoded = pd.DataFrame(encoder.fit_transform(trade_info_scaled[categorical_cols]).toarray(), columns=encoder.get_feature_names_out(categorical_cols))
    trade_info_encoded = trade_info_encoded.join(trade_info_scaled.select_dtypes(include=['number']))

    categorical_cols = trade_vega_scaled.select_dtypes(include=['object']).columns
    encoder = OneHotEncoder(handle_unknown='ignore')
    trade_vega_encoded = pd.DataFrame(encoder.fit_transform(trade_vega_scaled[categorical_cols]).toarray(), columns=encoder.get_feature_names_out(categorical_cols))
    trade_vega_encoded = trade_vega_encoded.join(trade_vega_scaled.select_dtypes(include=['number']))
    

    # Check for missing values and duplicates
    assert not any(market_swap_rate.isnull().any()), "There are missing values in market_swap_rate."

    assert not any(market_swaption_vols.isnull().any()), "There are missing values in market_swaption_vols."
    assert not any(trade_info.isnull().any()), "There are missing values in trade_info."
    assert not any(trade_vega.isnull().any()), "There are missing values in trade_vega."

    assert not any(market_swap_rate.duplicated()), "There are duplicated rows in market_swap_rate."
    assert not any(market_swaption_vols.duplicated()), "There are duplicated rows in market_swaption_vols."
    market_swaption_vols = market_swaption_vols.drop_duplicates()
    assert not any(trade_info.duplicated()), "There are duplicated rows in trade_info."
    assert not any(trade_vega.duplicated()), "There are duplicated rows in trade_vega."

    # Check for datetime
    assert market_swap_rate.index.max() <= pd.Timestamp.today(), "There are future dates in market_swap_rate."
    assert market_swaption_vols.index.max() <= pd.Timestamp.today(), "There are future dates in market_swaption_vols."
    assert trade_vega.index.max() <= pd.Timestamp.today(), "There are future dates in trade_vega."

    return market_swap_rate_encoded, market_swaption_vols_encoded, trade_info_encoded, trade_vega_encoded