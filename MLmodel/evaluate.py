import os
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

try:
    from config import Config
    from data_collector import StockDataCollector
    from lstm_model import LSTMModelTrainer
except ImportError:
    from config import Config
    from data_collector import StockDataCollector
    from lstm_model import LSTMModelTrainer


def evaluate_predictions(actual, predicted):
    mse  = mean_squared_error(actual, predicted)
    mae  = mean_absolute_error(actual, predicted)
    rmse = np.sqrt(mse)
    r2   = r2_score(actual, predicted)
    return {
        'mse':  float(mse),
        'mae':  float(mae),
        'rmse': float(rmse),
        'r2':   float(r2)
    }


def generate_evaluation_report(symbol, actual, predicted, output_dir=None):
    metrics = evaluate_predictions(actual, predicted)
    report  = {
        'symbol':  symbol,
        'metrics': metrics,
        'samples': len(actual)
    }
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        report_path = os.path.join(output_dir, f'{symbol}_evaluation.json')
        pd.Series(report).to_json(report_path)
    return report


def run_evaluation(config=None):
    if config is None:
        config = Config()

    collector  = StockDataCollector(config)
    stock_data = collector.fetch_all_stocks()
    lstm       = LSTMModelTrainer(config)
    reports    = {}

    for symbol in config.selected_stocks:
        try:
            model_path = os.path.join(config.models_dir, f'{symbol}_lstm_model.keras')
            if not os.path.exists(model_path):
                continue
            if symbol not in stock_data:
                continue

            from tensorflow.keras.models import load_model
            from lstm_model import CUSTOM_OBJECTS
            model = load_model(model_path, custom_objects=CUSTOM_OBJECTS)

            # Load the per-stock scaler
            lstm.load_scaler(symbol)

            df     = stock_data[symbol]
            # prepare_data with fit_scaler=False — use the saved scaler
            X, y_scaled = lstm.prepare_data(df, symbol=symbol, fit_scaler=False)
            if len(X) == 0:
                continue

            # Predict in scaled space
            pred_scaled = model.predict(X, verbose=0)   # (samples, prediction_days)

            # Inverse-transform first prediction day back to rupee prices
            actual    = lstm.inverse_transform_close(symbol, y_scaled[:, 0])
            predicted = lstm.inverse_transform_close(symbol, pred_scaled[:, 0])

            reports[symbol] = generate_evaluation_report(
                symbol, actual, predicted, output_dir=config.logs_dir
            )
            r2 = reports[symbol]['metrics']['r2']
            print(f"[{symbol}] R²={r2:.4f}")

        except Exception as ex:
            print(f"Failed evaluation for {symbol}: {ex}")

    return reports


if __name__ == '__main__':
    config = Config()
    report = run_evaluation(config)
    print(report)