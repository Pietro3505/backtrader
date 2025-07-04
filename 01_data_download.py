import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Define target symbols
#microsoft, tesla, palantir
symbols = ["TSLA", "MSFT", "PLTR"]
# Define date range
end_date = datetime.today()
start_date = end_date - timedelta(days=5 * 365)

# Download and resample data
data = {}
for symbol in symbols:
    df = yf.download(symbol, start=start_date.strftime('%Y-%m-%d'), interval="1D", progress=False)
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    df.dropna(inplace=True)
    data[symbol] = df

# Save to disk or cache for next steps
import os
os.makedirs("data", exist_ok=True)
for symbol, df in data.items():
    df.to_csv(f"data/{symbol}_1D.csv")

print("Data download complete.")
