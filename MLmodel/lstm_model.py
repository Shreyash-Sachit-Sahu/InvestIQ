import os
import numpy as np
import joblib
from sklearn.preprocessing import MinMaxScaler

import tensorflow as tf
import keras
from tensorflow.keras.models import Model
from tensorflow.keras.layers import (
    Input, LSTM, Dense, Dropout, Bidirectional,
    BatchNormalization, LayerNormalization,
    Conv1D, GlobalAveragePooling1D,
    MultiHeadAttention, Add, Concatenate, Activation
)
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.regularizers import l2


# ── Feature list (22 features from data_collector) ────────────────────────────
FEATURES = [
    'Close', 'Return',
    'SMA10', 'SMA20', 'SMA50',
    'EMA10', 'EMA20',
    'Volatility10', 'Volatility20',
    'VolumeChange', 'OBV',
    'RSI14',
    'MACD', 'Signal', 'MACD_Hist',
    'BB_upper', 'BB_lower', 'BB_width', 'BB_pos',
    'Momentum5', 'Momentum10', 'Momentum20'
]
NUM_FEATURES = len(FEATURES)  # 22


# ── Custom Layers ──────────────────────────────────────────────────────────────
# @keras.saving.register_keras_serializable() is REQUIRED for any custom layer
# used inside a Functional Model saved with model.save().
# Without it, load_model() cannot locate the class and raises a deserialization error.

@keras.saving.register_keras_serializable(package='InvestIQ')
class TemporalAttention(tf.keras.layers.Layer):
    """
    Soft attention over the time axis.
    Learns which timesteps matter most and returns a weighted sum of hidden states.
    """
    def __init__(self, units, **kwargs):
        super().__init__(**kwargs)
        self.units = units
        self.W = Dense(units, use_bias=False)
        self.V = Dense(1,     use_bias=False)

    def call(self, hidden_states):
        score   = self.V(tf.nn.tanh(self.W(hidden_states)))  # (batch, T, 1)
        weights = tf.nn.softmax(score, axis=1)               # (batch, T, 1)
        context = tf.reduce_sum(weights * hidden_states, axis=1)  # (batch, units)
        return context

    def get_config(self):
        config = super().get_config()
        config.update({'units': self.units})
        return config


@keras.saving.register_keras_serializable(package='InvestIQ')
class ChannelAttention(tf.keras.layers.Layer):
    """
    Squeeze-and-Excitation style channel attention.
    Learns which features (channels) are most informative and rescales them.
    """
    def __init__(self, reduction_ratio=4, **kwargs):
        super().__init__(**kwargs)
        self.reduction_ratio = reduction_ratio

    def build(self, input_shape):
        channels = input_shape[-1]
        reduced  = max(1, channels // self.reduction_ratio)
        self.fc1 = Dense(reduced,   activation='relu',    use_bias=False)
        self.fc2 = Dense(channels,  activation='sigmoid', use_bias=False)
        super().build(input_shape)

    def call(self, x):
        # x: (batch, timesteps, channels)
        gap      = tf.reduce_mean(x, axis=1)        # (batch, channels)
        squeezed = self.fc2(self.fc1(gap))           # (batch, channels)
        squeezed = tf.expand_dims(squeezed, axis=1)  # (batch, 1, channels)
        return x * squeezed

    def get_config(self):
        config = super().get_config()
        config.update({'reduction_ratio': self.reduction_ratio})
        return config


# ── Helper: custom_objects dict for load_model ────────────────────────────────
CUSTOM_OBJECTS = {
    'TemporalAttention': TemporalAttention,
    'ChannelAttention':  ChannelAttention,
}


# ── Main Trainer Class ─────────────────────────────────────────────────────────

class LSTMModelTrainer:
    def __init__(self, config):
        self.config  = config
        self.scalers = {}

    # ─────────────────────────────────────────────────────────
    # DATA PREPARATION
    # ─────────────────────────────────────────────────────────
    def prepare_data(self, df, symbol=None, fit_scaler=False):
        """
        Returns:
            X        : (samples, lookback_window, NUM_FEATURES)  float32
            y_scaled : (samples, prediction_days)                float32
        fit_scaler=True  → fit a new MinMaxScaler and store in self.scalers[symbol]
        fit_scaler=False → use already-fitted scaler from self.scalers[symbol]
        """
        available = [f for f in FEATURES if f in df.columns]
        data = df[available].values.astype(np.float32)
        data = np.nan_to_num(data, nan=0.0, posinf=0.0, neginf=0.0)

        if fit_scaler:
            scaler = MinMaxScaler(feature_range=(0, 1))
            data   = scaler.fit_transform(data)
            if symbol:
                self.scalers[symbol] = scaler
        elif symbol and symbol in self.scalers:
            data = self.scalers[symbol].transform(data)

        close_idx = available.index('Close') if 'Close' in available else 0
        lw  = self.config.lookback_window
        pd_ = self.config.prediction_days

        X, y_scaled = [], []
        for i in range(lw, len(data) - pd_ + 1):
            X.append(data[i - lw:i, :])
            y_scaled.append(data[i:i + pd_, close_idx])

        return (np.array(X, dtype=np.float32),
                np.array(y_scaled, dtype=np.float32))

    # ─────────────────────────────────────────────────────────
    # MODEL ARCHITECTURE
    # ─────────────────────────────────────────────────────────
    def build_model(self, input_shape):
        """
        3-Branch Architecture:
          Branch A — CNN          : local price pattern extractor
          Branch B — BiLSTM stack : stacked Bidirectional LSTMs with
                                    ChannelAttention + residual connections
                                    → TemporalAttention context vector
          Branch C — Transformer  : Multi-Head Self-Attention block
          All branches merged → deep residual dense head → prediction_days output
        """
        reg    = l2(1e-4)
        inputs = Input(shape=input_shape, name='input')

        # ── Branch A: CNN Feature Extractor ───────────────────────────────────
        cnn = Conv1D(32,  kernel_size=3, padding='causal',
                     activation='relu', kernel_regularizer=reg)(inputs)
        cnn = BatchNormalization()(cnn)
        cnn = Conv1D(64,  kernel_size=3, padding='causal',
                     activation='relu', kernel_regularizer=reg)(cnn)
        cnn = BatchNormalization()(cnn)
        cnn = Conv1D(128, kernel_size=3, padding='causal',
                     activation='relu', kernel_regularizer=reg)(cnn)
        cnn = BatchNormalization()(cnn)
        cnn = Dropout(0.2)(cnn)
        cnn_out = GlobalAveragePooling1D()(cnn)                  # (batch, 128)

        # ── Branch B: Stacked BiLSTM + ChannelAttention + Residuals ──────────

        # Block 1
        b1  = Bidirectional(LSTM(64, return_sequences=True,
                                 kernel_regularizer=reg))(inputs)
        b1  = ChannelAttention(reduction_ratio=4)(b1)
        b1  = LayerNormalization()(b1)
        b1  = Dropout(0.3)(b1)
        r1  = Conv1D(128, kernel_size=1, padding='same')(inputs)  # project to 128
        b1  = Add()([b1, r1])

        # Block 2
        b2  = Bidirectional(LSTM(64, return_sequences=True,
                                 kernel_regularizer=reg))(b1)
        b2  = ChannelAttention(reduction_ratio=4)(b2)
        b2  = LayerNormalization()(b2)
        b2  = Dropout(0.2)(b2)
        b2  = Add()([b2, b1])                                     # same shape → direct residual

        # Block 3
        b3  = Bidirectional(LSTM(32, return_sequences=True,
                                 kernel_regularizer=reg))(b2)
        b3  = ChannelAttention(reduction_ratio=4)(b3)
        b3  = LayerNormalization()(b3)
        b3  = Dropout(0.15)(b3)
        r3  = Conv1D(64, kernel_size=1, padding='same')(b2)       # project 128 → 64
        b3  = Add()([b3, r3])

        lstm_out = TemporalAttention(64)(b3)                      # (batch, 64)

        # ── Branch C: Multi-Head Self-Attention (Transformer block) ──────────
        attn     = MultiHeadAttention(num_heads=4, key_dim=16, dropout=0.1)(inputs, inputs)
        attn     = Add()([inputs, attn])
        attn     = LayerNormalization()(attn)
        attn_out = GlobalAveragePooling1D()(attn)                 # (batch, NUM_FEATURES)

        # ── Merge all 3 branches ──────────────────────────────────────────────
        merged = Concatenate()([cnn_out, lstm_out, attn_out])
        # merged shape: (batch, 128 + 64 + NUM_FEATURES)

        # ── Deep Dense Head with residual skip connections ────────────────────
        d1    = Dense(256, kernel_regularizer=reg)(merged)
        d1    = LayerNormalization()(d1)
        d1    = Activation('relu')(d1)
        d1    = Dropout(0.3)(d1)

        d2    = Dense(128, kernel_regularizer=reg)(d1)
        d2    = LayerNormalization()(d2)
        d2    = Activation('relu')(d2)
        d2    = Dropout(0.2)(d2)
        skip2 = Dense(128)(d1)
        d2    = Add()([d2, skip2])

        d3    = Dense(64, activation='relu')(d2)
        d3    = Dropout(0.1)(d3)
        d4    = Dense(32, activation='relu')(d3)

        output = Dense(self.config.prediction_days, name='output')(d4)

        model = Model(inputs=inputs, outputs=output, name='DeepLSTM_InvestIQ')
        model.compile(
            optimizer=Adam(learning_rate=1e-3, clipnorm=1.0),
            loss='huber',
            metrics=['mae']
        )
        return model

    # ─────────────────────────────────────────────────────────
    # TRAINING
    # ─────────────────────────────────────────────────────────
    def train_all_models(self, stock_data):
        models, metrics = {}, {}

        for symbol, df in stock_data.items():
            try:
                X, y = self.prepare_data(df, symbol=symbol, fit_scaler=True)

                if len(X) < 50:
                    print(f"[{symbol}] Not enough sequences ({len(X)}), skipping.")
                    continue

                split          = int(len(X) * self.config.train_ratio)
                X_train, X_val = X[:split],  X[split:]
                y_train, y_val = y[:split],  y[split:]

                model = self.build_model(
                    input_shape=(X_train.shape[1], X_train.shape[2])
                )

                if not models:
                    model.summary()

                callbacks = [
                    EarlyStopping(
                        monitor='val_loss',
                        patience=self.config.early_stopping_patience,
                        restore_best_weights=True,
                        min_delta=1e-5
                    ),
                    ReduceLROnPlateau(
                        monitor='val_loss',
                        factor=0.5,
                        patience=self.config.lr_patience,
                        min_lr=1e-6,
                        verbose=0
                    )
                ]

                history = model.fit(
                    X_train, y_train,
                    validation_data=(X_val, y_val),
                    epochs=self.config.epochs,
                    batch_size=self.config.batch_size,
                    callbacks=callbacks,
                    verbose=0
                )

                model_path = f"{self.config.models_dir}/{symbol}_lstm_model.keras"
                model.save(model_path)
                self.save_scaler(symbol)

                models[symbol]  = model
                metrics[symbol] = {
                    'loss':     float(history.history['loss'][-1]),
                    'val_loss': float(history.history['val_loss'][-1]),
                    'mae':      float(history.history['mae'][-1])
                }
                print(f"[{symbol}] val_loss={metrics[symbol]['val_loss']:.6f}  "
                      f"mae={metrics[symbol]['mae']:.6f}")

            except Exception as ex:
                print(f"[{symbol}] Training failed: {ex}")

        return models, metrics

    # ─────────────────────────────────────────────────────────
    # SCALER PERSISTENCE
    # ─────────────────────────────────────────────────────────
    def save_scaler(self, symbol):
        if symbol in self.scalers:
            path = os.path.join(self.config.scalers_dir, f"{symbol}_scaler.pkl")
            joblib.dump(self.scalers[symbol], path)

    def load_scaler(self, symbol):
        path = os.path.join(self.config.scalers_dir, f"{symbol}_scaler.pkl")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Scaler not found for {symbol}: {path}")
        self.scalers[symbol] = joblib.load(path)
        return self.scalers[symbol]

    # ─────────────────────────────────────────────────────────
    # INVERSE TRANSFORM
    # ─────────────────────────────────────────────────────────
    def inverse_transform_close(self, symbol, scaled_values):
        """Converts scaled Close predictions back to rupee prices."""
        if symbol not in self.scalers:
            self.load_scaler(symbol)
        scaler    = self.scalers[symbol]
        flat      = np.array(scaled_values).flatten()
        dummy     = np.zeros((len(flat), scaler.n_features_in_), dtype=np.float32)
        dummy[:, 0] = flat   # Close is index 0
        return scaler.inverse_transform(dummy)[:, 0]

    # ─────────────────────────────────────────────────────────
    # LEGACY HELPERS
    # ─────────────────────────────────────────────────────────
    def create_sequences(self, values, look_back):
        X, y = [], []
        for i in range(look_back, len(values)):
            X.append(values[i - look_back:i])
            y.append(values[i])
        X = np.array(X, dtype=np.float32).reshape(-1, look_back, 1)
        y = np.array(y, dtype=np.float32)
        return X, y

    def inverse_transform(self, original, predicted):
        return predicted