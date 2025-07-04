import alpaca_trade_api as tradeapi
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

# --- Alpaca credentials ---
API_KEY = "YOUR_API_KEY"
API_SECRET = "YOUR_SECRET_KEY"
BASE_URL = "https://paper-api.alpaca.markets"

api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')

symbol = "AAPL"
timeframe = "1H"

def fetch_data():
    now = datetime.now()
    start = (now - timedelta(days=30)).isoformat()
    barset = api.get_bars(symbol, timeframe, start=start).df
    barset = barset[barset['symbol'] == symbol].copy()
    barset.rename(columns={"t": "timestamp"}, inplace=True)
    return barset

def compute_indicators(df):
    df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean()
    vol_short = df['volume'].rolling(window=14).mean()
    vol_long = df['volume'].rolling(window=28).mean()
    df['Volume_Osc'] = (vol_short - vol_long) / vol_long

    ema_fast = df['close'].ewm(span=9, adjust=False).mean()
    ema_slow = df['close'].ewm(span=25, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=10, adjust=False).mean()
    df['MACD_Hist'] = macd_line - signal_line
    df['MACD_Hist_prev'] = df['MACD_Hist'].shift(1)

    df['Donchian_Lower'] = df['low'].rolling(window=20).min()

    return df

def evaluate_trade(df):
    latest = df.iloc[-1]
    if (
        latest['close'] > latest['EMA_200'] and
        latest['Volume_Osc'] > 0 and
        latest['MACD_Hist'] > 0 and
        df.iloc[-2]['MACD_Hist'] < 0
    ):
        return True, latest
    return False, None

def place_trade(latest):
    account = api.get_account()
    equity = float(account.cash)
    qty = int(equity / latest['close'])

    entry = latest['close']
    stop = latest['Donchian_Lower']
    risk = entry - stop
    take = entry + 1.5 * risk

    api.submit_order(
        symbol=symbol,
        qty=qty,
        side='buy',
        type='market',
        time_in_force='gtc',
        order_class='bracket',
        stop_loss={'stop_price': round(stop, 2)},
        take_profit={'limit_price': round(take, 2)}
    )
    print(f"Trade placed: Buy {qty} {symbol} @ {entry}, SL: {stop}, TP: {take}")

# Main loop (run hourly via scheduler or loop)
def run_bot():
    df = fetch_data()
    df = compute_indicators(df)
    signal, latest = evaluate_trade(df)
    if signal:
        place_trade(latest)

# --- Trigger the strategy (or call run_bot() every hour) ---
run_bot()
