import os
import joblib
import numpy as np


class PortfolioRecommender:
    def __init__(self, models_dir, symbols, config):
        self.symbols = symbols
        self.lookback_window = config.lookback_window
        self.prediction_days = config.prediction_days
        self.models = {}
        self.xscalers = {}
        self.yscalers = {}
        from keras.models import load_model
        for symbol in self.symbols:
            try:
                model_path = os.path.join(models_dir, f"{symbol}_lstm_model.h5")
                xscaler_path = os.path.join(models_dir, f"{symbol}_xscaler.pkl")
                yscaler_path = os.path.join(models_dir, f"{symbol}_yscaler.pkl")
                self.models[symbol] = load_model(model_path)
                self.xscalers[symbol] = joblib.load(xscaler_path)
                self.yscalers[symbol] = joblib.load(yscaler_path)
            except Exception:
                # Could log here for debugging if needed
                continue

    def predict(self, preferences):
        results = []
        for h in preferences.get("holdings", []):
            symbol = h["symbol"]
            if symbol not in self.models:
                continue
            stock_data = preferences.get("stock_data", {}).get(symbol)
            if stock_data is None:
                continue
            df = stock_data
            last_seq = df[self.features].values[-self.lookback_window:]
            xscaler = self.xscalers[symbol]
            yscaler = self.yscalers[symbol]
            last_seq_scaled = xscaler.transform(last_seq)
            model = self.models[symbol]
            cur_seq = last_seq_scaled.copy()
            future = []
            for _ in range(self.prediction_days):
                pred_scaled = model.predict(cur_seq[np.newaxis, :, :], verbose=0)[0, 0]
                cur_seq = np.roll(cur_seq, -1, axis=0)
                cur_seq[-1, 0] = pred_scaled
                future.append(pred_scaled)
            future_np = np.array(future).reshape(-1, 1)
            close_preds = yscaler.inverse_transform(future_np).flatten()
            results.append({
                "symbol": symbol,
                "quantity": h["quantity"],
                "average_buy_price": h.get("average_buy_price"),
                "prediction": close_preds.tolist(),
            })
        return {"predictions": results}
