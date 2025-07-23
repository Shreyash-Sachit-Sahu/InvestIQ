import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
import logging
import os

import tensorflow as tf
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
from keras.callbacks import EarlyStopping

from scikeras.wrappers import KerasRegressor
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit

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

def build_lstm_model(
    input_shape=None, 
    lstm1_units=64, 
    lstm2_units=32, 
    dropout1=0.3, 
    dropout2=0.2, 
    dense_units=16, 
    learning_rate=0.001
):
    model = Sequential()
    model.add(LSTM(lstm1_units, return_sequences=True, input_shape=input_shape))
    model.add(Dropout(dropout1))
    model.add(LSTM(lstm2_units, return_sequences=False))
    model.add(Dropout(dropout2))
    model.add(Dense(dense_units, activation='relu'))
    model.add(Dense(1))
    opt = tf.keras.optimizers.Adam(learning_rate=learning_rate)
    model.compile(optimizer=opt, loss='mean_squared_error')
    return model

class LSTMModelTrainer:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.preprocessor = LSTMPreprocessor(config.lookback_window)
        self.features = [
            'Close', 'Return', 'SMA10', 'SMA20', 'EMA10', 'Volatility10', 'VolumeChange', 'RSI14'
        ]

    def train_all_models(self, stock_data, use_grid_search=True):
        models, metrics = {}, {}
        for symbol, data in stock_data.items():
            if not all(f in data.columns for f in self.features):
                continue
            X, y, scaler, y_scaler = self.preprocessor.prepare_lstm_data(data, self.features, 'Close')
            X_train, X_test, y_train, y_test = self.preprocessor.train_test_split(X, y, self.config.train_ratio)
            input_shape = (X_train.shape[1], X_train.shape[2])

            if use_grid_search:
                self.logger.info(f"[TUNE] Grid search for {symbol}...")
                param_grid = {
                    "lstm1_units": [32, 64],
                    "lstm2_units": [16, 32],
                    "dropout1": [0.2, 0.3],
                    "dropout2": [0.1, 0.2],
                    "dense_units": [8, 16],
                    "learning_rate": [0.001, 0.005],
                    "epochs": [40],
                    "batch_size": [16, 32]
                }
                reg = KerasRegressor(
                    model=build_lstm_model,
                    input_shape=input_shape,
                    lstm1_units=64,
                    lstm2_units=32,
                    dropout1=0.3,
                    dropout2=0.2,
                    dense_units=16,
                    learning_rate=0.001,
                    epochs=40,
                    batch_size=32,
                    verbose=0
                )
                cv = TimeSeriesSplit(n_splits=3)
                grid = GridSearchCV(
                    estimator=reg,
                    param_grid=param_grid,
                    scoring="neg_mean_squared_error",
                    cv=cv,
                    n_jobs=1  # You can set >1 if your hardware allows
                )
                grid.fit(X_train, y_train)
                best_model = grid.best_estimator_.model_
                self.logger.info(f"[TUNE] {symbol} best params: {grid.best_params_}")
                model_obj = best_model
            else:
                # Always available as legacy fallback
                early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
                model_obj = build_lstm_model(input_shape=input_shape)
                model_obj.fit(
                    X_train, y_train,
                    epochs=self.config.epochs,
                    batch_size=self.config.batch_size,
                    validation_data=(X_test, y_test),
                    callbacks=[early_stop],
                    verbose=1
                )

            y_pred = model_obj.predict(X_test, verbose=0).flatten()
            y_test_inv = y_scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()
            y_pred_inv = y_scaler.inverse_transform(y_pred.reshape(-1, 1)).flatten()
            mse = mean_squared_error(y_test_inv, y_pred_inv)
            mae = mean_absolute_error(y_test_inv, y_pred_inv)
            r2 = r2_score(y_test_inv, y_pred_inv)
            met = {
                "MSE": mse,
                "MAE": mae,
                "RMSE": np.sqrt(mse),
                "R²": r2
            }
            models[symbol] = {
                'model': model_obj,
                'scaler': scaler,
                'y_scaler': y_scaler
            }
            metrics[symbol] = met
            joblib.dump(scaler, f"models/{symbol}_xscaler.pkl")
            joblib.dump(y_scaler, f"models/{symbol}_yscaler.pkl")
            model_obj.save(f"models/{symbol}_lstm_model.h5")
            self.logger.info(f"{symbol}: R²={met['R²']:.2f} RMSE={met['RMSE']:.2f}")
        return models, metrics
