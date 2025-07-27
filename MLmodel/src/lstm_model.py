import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
from keras.callbacks import EarlyStopping
import joblib
import logging
import os

class LSTMPreprocessor:
    def __init__(self, lookback_window=30):
        self.lookback_window = lookback_window

    def prepare_lstm_data(self, data, features, target_column='Close'):
        scaler = MinMaxScaler()
        X_scaled = scaler.fit_transform(data[features].values)
        y = data[target_column].values.reshape(-1, 1)
        y_scaler = MinMaxScaler()
        y_scaled = y_scaler.fit_transform(y)
        X_seq, y_seq = [], []
        for i in range(self.lookback_window, len(data)):
            X_seq.append(X_scaled[i-self.lookback_window:i, :])
            y_seq.append(y_scaled[i, 0])
        X_seq, y_seq = np.array(X_seq), np.array(y_seq)
        return X_seq, y_seq, scaler, y_scaler

    def train_test_split(self, X, y, train_ratio=0.8):
        split = int(len(X) * train_ratio)
        return X[:split], X[split:], y[:split], y[split:]

class LSTMModel:
    def __init__(self, input_shape):
        self.model = self._create_model(input_shape)
        self.history = None

    def _create_model(self, input_shape):
        model = Sequential([
            LSTM(64, return_sequences=True, input_shape=input_shape),
            Dropout(0.3),
            LSTM(32, return_sequences=False),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(1)
        ])
        model.compile(optimizer='adam', loss='mean_squared_error')
        return model

    def train(self, X_train, y_train, X_val, y_val, epochs=60, batch_size=32):
        early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
        self.history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=(X_val, y_val),
            callbacks=[early_stop],
            verbose=1
        )
        return self.history

    def predict(self, X):
        return self.model.predict(X, verbose=0).flatten()

    def evaluate_model(self, y_true, y_pred):
        mse = mean_squared_error(y_true, y_pred)
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        return {"MSE": mse, "MAE": mae, "RMSE": np.sqrt(mse), "R²": r2}

class LSTMModelTrainer:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.preprocessor = LSTMPreprocessor(config.lookback_window)
        self.features = [
            'Close', 'Return', 'SMA10', 'SMA20', 'EMA10', 'Volatility10', 'VolumeChange', 'RSI14'
        ]

    def train_all_models(self, stock_data):
        models, metrics = {}, {}
        for symbol, data in stock_data.items():
            if not all(f in data.columns for f in self.features):
                continue
            X, y, scaler, y_scaler = self.preprocessor.prepare_lstm_data(data, self.features, 'Close')
            X_train, X_test, y_train, y_test = self.preprocessor.train_test_split(X, y, self.config.train_ratio)
            model = LSTMModel((X_train.shape[1], X_train.shape[2]))
            model.train(X_train, y_train, X_test, y_test, epochs=self.config.epochs, batch_size=self.config.batch_size)
            y_pred = model.predict(X_test)
            # Inverse transform predictions for metrics
            y_test_inv = y_scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()
            y_pred_inv = y_scaler.inverse_transform(y_pred.reshape(-1, 1)).flatten()
            met = model.evaluate_model(y_test_inv, y_pred_inv)
            models[symbol] = {
                'model': model.model, 
                'scaler': scaler, 
                'y_scaler': y_scaler
            }
            metrics[symbol] = met
            joblib.dump(scaler, f"models/{symbol}_xscaler.pkl")
            joblib.dump(y_scaler, f"models/{symbol}_yscaler.pkl")
            model.model.save(f"models/{symbol}_lstm_model.h5")
            self.logger.info(f"{symbol}: R²={met['R²']:.2f} RMSE={met['RMSE']:.2f}")
        return models, metrics
