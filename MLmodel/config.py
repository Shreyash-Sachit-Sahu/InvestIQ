import os

class Config:
    def __init__(self):
        self.indian_stocks = [
            "RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "KOTAKBANK", "HDFC", "AXISBANK", "SBIN", "LT",
            "ITC", "BAJFINANCE", "BHARTIARTL", "HINDUNILVR", "ONGC", "MARUTI", "TITAN", "ULTRACEMCO", "NESTLEIND",
            "ASIANPAINT", "DIVISLAB", "TECHM", "EICHERMOT", "JSWSTEEL", "TATASTEEL", "WIPRO", "M&M", "ADANIPORTS", "DRREDDY"
        ]
        self.selected_stocks = self.indian_stocks

        # ── Data ──────────────────────────────────────────────
        self.data_period       = "5y"
        self.train_ratio       = 0.8

        # ── Sequence ──────────────────────────────────────────
        self.lookback_window   = 120
        self.prediction_days   = 30

        # ── Training ──────────────────────────────────────────
        self.epochs                   = 55
        self.batch_size               = 16
        self.validation_split         = 0.2
        self.early_stopping_patience  = 20
        self.lr_patience              = 8

        # ── Paths ─────────────────────────────────────────────
        self.data_dir      = os.path.abspath("data")
        self.raw_dir       = os.path.join(self.data_dir, "raw")
        self.processed_dir = os.path.join(self.data_dir, "processed")
        self.models_dir    = os.path.abspath("models")
        self.scalers_dir   = os.path.abspath("scalers")
        self.logs_dir      = os.path.abspath("logs")

        # ── Recommender ───────────────────────────────────────
        self.recommender_epochs     = 40
        self.recommender_batch_size = 16
        self.risk_free_rate         = 0.05
        self.max_portfolio_stocks   = 10

        # ── Private profiles database ─────────────────────────
        # Path to the SQLite DB created by seed_database.py.
        # Override with DATABASE_URL env var for Postgres.
        self.profiles_db_path = os.path.abspath("investiq_profiles.db")

        # ── API ───────────────────────────────────────────────
        self.api_host = "0.0.0.0"
        self.api_port = 8000

        for d in [self.data_dir, self.raw_dir, self.processed_dir,
                  self.models_dir, self.scalers_dir, self.logs_dir]:
            os.makedirs(d, exist_ok=True)