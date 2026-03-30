import yfinance as yf
import pandas as pd
import numpy as np
import logging
from pathlib import Path


class StockDataCollector:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def compute_features(df):
        df = df.copy()

        # ── Basic returns & moving averages ───────────────────
        df['Return']       = df['Close'].pct_change()
        df['SMA10']        = df['Close'].rolling(10).mean()
        df['SMA20']        = df['Close'].rolling(20).mean()
        df['SMA50']        = df['Close'].rolling(50).mean()        # NEW
        df['EMA10']        = df['Close'].ewm(span=10, adjust=False).mean()
        df['EMA20']        = df['Close'].ewm(span=20, adjust=False).mean()  # NEW

        # ── Volatility ────────────────────────────────────────
        df['Volatility10'] = df['Return'].rolling(10).std()
        df['Volatility20'] = df['Return'].rolling(20).std()        # NEW

        # ── Volume ────────────────────────────────────────────
        df['VolumeChange'] = df['Volume'].pct_change()
        df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).cumsum()  # NEW On-Balance Volume

        # ── RSI ───────────────────────────────────────────────
        delta    = df['Close'].diff()
        gain     = delta.clip(lower=0)
        loss     = -1 * delta.clip(upper=0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs       = avg_gain / (avg_loss + 1e-9)
        df['RSI14'] = 100 - (100 / (1 + rs))

        # ── MACD ─────────────────────────────────────────────  NEW
        ema12        = df['Close'].ewm(span=12, adjust=False).mean()
        ema26        = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD']   = ema12 - ema26
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['Signal']

        # ── Bollinger Bands ───────────────────────────────────  NEW
        bb_mid          = df['Close'].rolling(20).mean()
        bb_std          = df['Close'].rolling(20).std()
        df['BB_upper']  = bb_mid + 2 * bb_std
        df['BB_lower']  = bb_mid - 2 * bb_std
        df['BB_width']  = (df['BB_upper'] - df['BB_lower']) / (bb_mid + 1e-9)
        df['BB_pos']    = (df['Close'] - df['BB_lower']) / (df['BB_upper'] - df['BB_lower'] + 1e-9)

        # ── Price momentum ────────────────────────────────────  NEW
        df['Momentum5']  = df['Close'] / df['Close'].shift(5)  - 1
        df['Momentum10'] = df['Close'] / df['Close'].shift(10) - 1
        df['Momentum20'] = df['Close'] / df['Close'].shift(20) - 1

        # ── Clean up ──────────────────────────────────────────
        df = df.replace([float('inf'), -float('inf')], pd.NA)
        df = df.dropna()
        return df

    @staticmethod
    def _flatten_columns(df):
        """
        yfinance sometimes returns a MultiIndex column like ('Close', 'RELIANCE.NS').
        Flatten to single-level strings so df['Close'] always returns a Series.
        """
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]
        # Ensure every OHLCV column is a plain 1-D Series (squeeze out extra dims)
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col in df.columns and isinstance(df[col], pd.DataFrame):
                df[col] = df[col].squeeze()
        return df

    def fetch_stock_data(self, symbol):
        ticker = f"{symbol}.NS"
        self.logger.info(f"Fetching {ticker}...")
        df = yf.download(ticker, period=self.config.data_period,
                         progress=False, threads=False, auto_adjust=True)
        if df.empty:
            self.logger.warning(f"No data for {ticker}")
            return None
        df = df.reset_index()
        df = self._flatten_columns(df)   # ← fix MultiIndex before feature engineering
        df = self.compute_features(df)
        return df

    def fetch_all_stocks(self):
        results = {}
        for symbol in self.config.selected_stocks:
            df = self.fetch_stock_data(symbol)
            if df is not None and len(df) > self.config.lookback_window + 10:
                results[symbol] = df
                processed_path = Path(self.config.processed_dir) / f"{symbol}.csv"
                df.to_csv(processed_path, index=False)
        return results