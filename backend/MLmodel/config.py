import os


class Config:
    def __init__(self):
        self.indian_stocks = [
            "RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "KOTAKBANK", "HDFC", "AXISBANK", "SBIN", "LT",
            "ITC", "BAJFINANCE", "BAJAJFINSV", "BHARTIARTL", "HINDUNILVR", "ONGC", "MARUTI", "TITAN", "ULTRACEMCO", "NESTLEIND",
            "ASIANPAINT", "DIVISLAB", "TECHM", "EICHERMOT", "JSWSTEEL", "TATASTEEL", "WIPRO", "M&M", "ADANIPORTS", "DRREDDY",
            "HCLTECH", "POWERGRID", "SBILIFE", "COALINDIA", "BRITANNIA", "BAJAJ-AUTO", "SUNPHARMA", "ADANIENT", "IOC", "NTPC",
            "UPL", "CIPLA", "TATAMOTORS", "INDUSINDBK", "SHREECEM", "HAVELLS", "HDFCLIFE", "MINDTREE", "VOLTAS", "PAGEIND",
            "APOLLOHOSP", "COLPAL", "ICICIPRULI", "BANDHANBNK", "MUTHOOTFIN", "AMBUJACEM", "HDFCAMC", "SIEMENS", "PGHH", "DMART",
            "FEDERALBNK", "ICICIGI", "CROMPTON", "ZOMATO", "IRCTC", "MGL", "BANKBARODA", "AUROPHARMA", "PEL", "SRF",
            "GODREJCP", "GRASIM", "SHRIRAMFIN", "ADANITRANS", "HINDALCO", "ADANIGREEN", "PIDILITIND", "DABUR", "TATAELXSI", "NAVINFLUOR",
            "LTI", "GAIL", "ALKEM", "TORNTPHARM", "ABBOTINDIA", "UBL", "INDIGO", "BIOCON", "LICHSGFIN", "RECLTD",
            "NMDC", "IDFCFIRSTB", "CHOLAFIN", "INDHOTEL", "BERGEPAINT", "TATAPOWER", "GLAND", "LTIM", "TRENT", "VBL"
        ]
        self.selected_stocks = self.indian_stocks
        self.data_period = "3y"
        self.train_ratio = 0.85
        self.lookback_window = 17
        self.epochs = 40
        self.batch_size = 24
        self.validation_split = 0.2
        self.early_stopping_patience = 15
        self.risk_free_rate = 0.068
        self.portfolio_methods = ['max_sharpe', 'min_variance', 'risk_parity', 'equal_weight']
        self.prediction_days = 2
        self.data_dir = "data"
        self.models_dir = "models"
        self.outputs_dir = "outputs"
        self.logs_dir = "logs"
        for d in [
            self.data_dir, self.models_dir, self.outputs_dir, self.logs_dir,
            os.path.join(self.data_dir, "raw"),
            os.path.join(self.data_dir, "processed"),
            os.path.join(self.data_dir, "predictions"),
            os.path.join(self.outputs_dir, "plots"),
            os.path.join(self.outputs_dir, "reports")
        ]:
            os.makedirs(d, exist_ok=True)
