import yfinance as yf
import pandas as pd
import numpy as np
import logging
import time


class StockDataCollector:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.data = {}

    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['Return'] = df['Close'].pct_change()
        df['SMA10'] = df['Close'].rolling(10).mean()
        df['SMA20'] = df['Close'].rolling(20).mean()
        df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
        df['Volatility10'] = df['Return'].rolling(10).std()
        df['VolumeChange'] = df['Volume'].pct_change()
        df['RSI14'] = self.rsi(df['Close'], 14)
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.dropna()
        return df

    def rsi(self, series, period=14):
        delta = series.diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        ma_up = up.rolling(window=period, min_periods=1).mean()
        ma_down = down.rolling(window=period, min_periods=1).mean()
        rsi = 100 - (100 / (1 + ma_up / ma_down))
        return rsi

    def fetch_stock_data(self, symbol: str, period: str = "2y") -> pd.DataFrame:
        try:
            data = yf.download(f"{symbol}.NS", period=period, progress=False, threads=False)
            if data.empty:
                data = yf.download(symbol, period=period, progress=False, threads=False)
            if not data.empty:
                data.reset_index(inplace=True)
                self.logger.info(f"✓ Fetched {len(data)} days for {symbol}")
                return data
            else:
                self.logger.warning(f"✗ No data for {symbol}")
                return None
        except Exception as e:
            self.logger.error(f"✗ Error fetching {symbol}: {e}")
            return None

    def fetch_all_stocks(self):
        stock_data = {}
        for i, symbol in enumerate(self.config.selected_stocks):
            self.logger.info(f"[{i+1}/{len(self.config.selected_stocks)}] {symbol}")
            data = self.fetch_stock_data(symbol, self.config.data_period)
            if data is not None:
                data_feat = self.create_features(data)
                stock_data[symbol] = data_feat
            time.sleep(0.1)
        self.data = stock_data
        self.logger.info(f"Finished: {len(stock_data)} stocks")
        pd.to_pickle(stock_data, f"{self.config.data_dir}/raw/stock_data.pkl")
        for symbol, df in stock_data.items():
            df.to_csv(f"{self.config.data_dir}/raw/{symbol}_data.csv", index=False)
        return stock_data
