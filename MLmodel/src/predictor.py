import numpy as np
import pandas as pd
import logging

class FuturePredictor:
    def __init__(self, models, config):
        self.models = models
        self.config = config
        self.logger = logging.getLogger(__name__)

    def predict_single_stock(self, symbol, data, scaler, y_scaler, model, features, lookback=30, days=30):
        last_seq = data[features].values[-lookback:]
        last_seq_scaled = scaler.transform(last_seq)
        future = []
        cur_seq = last_seq_scaled.copy()
        for _ in range(days):
            pred_scaled = model.predict(cur_seq[np.newaxis, :, :])[0, 0]
            cur_seq = np.roll(cur_seq, -1, axis=0)
            cur_seq[-1, 0] = pred_scaled
            future.append(pred_scaled)
        future_np = np.array(future).reshape(-1, 1)
        close_preds = y_scaler.inverse_transform(future_np).flatten()
        return close_preds

    def predict_all_stocks(self, stock_data):
        predictions = {}
        features = ['Close', 'Return', 'SMA10', 'SMA20', 'EMA10', 'Volatility10', 'VolumeChange', 'RSI14']
        for symbol, model_dict in self.models.items():
            data = stock_data[symbol]
            scaler = model_dict['scaler']
            y_scaler = model_dict['y_scaler']
            model = model_dict['model']
            preds = self.predict_single_stock(
                symbol, data, scaler, y_scaler, model, features,
                lookback=self.config.lookback_window,
                days=self.config.prediction_days
            )
            last_date = data['Date'].iloc[-1]
            future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=self.config.prediction_days, freq='B')
            predictions[symbol] = pd.DataFrame({'Date': future_dates, 'Predicted_Close': preds})
        return predictions
