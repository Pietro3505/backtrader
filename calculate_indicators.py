# Define global parameters for indicators and backtests
params = {
    # EMAVolMACDStrategy
    'emavolmacd_donchian_period': 20,
    'emavolmacd_risk_reward_ratio': 2,
    'emavolmacd_ema_period': 200,
    'emavolmacd_macd_fast': 9,
    'emavolmacd_macd_slow': 25,
    'emavolmacd_macd_signal': 10,

    # EMACrossoverStrategy
    'emacrossover_ema_fast': 100,
    'emacrossover_sma_medium': 13,
    'emacrossover_ema_slow': 200,
    'emacrossover_risk_reward': 1.5,
    'emacrossover_trail_stop': 0.03,

    # EMAMACDStrategy
    'emamacd_ema_period': 100,
    'emamacd_macd_fast': 12,
    'emamacd_macd_slow': 26,
    'emamacd_macd_signal': 9,
    'emamacd_risk_reward': 1.5,
    'emamacd_donchian_period': 10,


    # Common
    'volume_short_period': 14,
    'volume_long_period': 28
}

# 5 ema 13 sma mit 100 ema als filter 10 ema 20 sma tages kein+mit-20 40 50 100  
# 200/100 ema filter macd risk reward 1.5 mit und ohne null linie
# 3 fast 10 slow _ 16 signal 
# Standard MACD 12 26 9

import pandas as pd
import numpy as np

# Calculate indicators with consistent parameters for Backtrader

def calculate_indicators_emavolmacd(df, params=params):
    # 200 EMA
    df[f'EMA_{params["emavolmacd_ema_period"]}'] = df['Close'].ewm(span=params['emavolmacd_ema_period'], adjust=False).mean()

    # Volume Oscillator: (short MA - long MA) / long MA
    short_vol = df['Volume'].rolling(window=params['volume_short_period']).mean()
    long_vol = df['Volume'].rolling(window=params['volume_long_period']).mean()
    df['Volume_Osc'] = (short_vol - long_vol) / long_vol

    # MACD (9, 25, 10) - consistent with Backtrader strategy
    ema_fast = df['Close'].ewm(span=params['emavolmacd_macd_fast'], adjust=False).mean()
    ema_slow = df['Close'].ewm(span=params['emavolmacd_macd_slow'], adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=params['emavolmacd_macd_signal'], adjust=False).mean()
    df['MACD_Hist'] = macd_line - signal_line

    # Donchian Channel Lower Band (20 periods)
    df[f'Donchian_Lower_{params["emavolmacd_donchian_period"]}'] = df['Low'].rolling(window=params['emavolmacd_donchian_period']).min()

    return df


def calculate_indicatorsEMACrossOver(df, params=params):
    # 100 EMA filter
    df[f'EMA_{params["emacrossover_ema_fast"]}'] = df['Close'].ewm(span=params['emacrossover_ema_fast'], adjust=False).mean()

    # Short EMA and Long SMA
    df[f'SMA_long_{params["emacrossover_sma_medium"]}'] = df['Close'].rolling(window=params['emacrossover_sma_medium']).mean()

    return df


def calculate_indicatorsEMAMACD(df, params=params):
    # 200 EMA filter
    df[f'EMA_{params["emamacd_ema_period"]}'] = df['Close'].ewm(span=params['emamacd_ema_period'], adjust=False).mean()

    # MACD (12, 26, 9) standard parameters
    ema_fast = df['Close'].ewm(span=params['emamacd_macd_fast'], adjust=False).mean()
    ema_slow = df['Close'].ewm(span=params['emamacd_macd_slow'], adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=params['emamacd_macd_signal'], adjust=False).mean()
    df['MACD_Hist'] = macd_line - signal_line

    df[f'Donchian_Lower_{params["emamacd_donchian_period"]}'] = df['Low'].rolling(window=params['emavolmacd_donchian_period']).min()

    return df


# Apply to all dataframes
import os

data = {}
for file in os.listdir("data"):
    if file.endswith("_1D.csv"):
        symbol = file.split("_")[0]
        date_format = '%Y-%m-%d'
        df = pd.read_csv(f"data/{file}", index_col=0, parse_dates=True, date_format=date_format, skiprows=[1,2])
        data[symbol] = calculate_indicatorsEMAMACD(df, params=params)

# Save with indicators
for symbol, df in data.items():
    df.to_csv(f"data/{symbol}_1D_indicators.csv")

print("Indicator calculation complete.")
