import os
import pickle
import pandas as pd


def setup_directories():
    directories = [
        'data/raw', 'data/processed', 'data/predictions',
        'models', 'outputs/plots', 'outputs/reports', 'logs'
    ]
    for d in directories:
        os.makedirs(d, exist_ok=True)


def save_results(models, portfolios, predictions, metrics, stock_data):
    with open('models/models.pkl', 'wb') as f:
        pickle.dump(models, f)
    with open('outputs/portfolios.pkl', 'wb') as f:
        pickle.dump(portfolios, f)
    with open('outputs/predictions.pkl', 'wb') as f:
        pickle.dump(predictions, f)
    pd.DataFrame([dict(Stock=k, **v) for k, v in metrics.items()]).to_csv(
        "outputs/model_performance.csv", index=False)


def generate_report(models, portfolios, predictions, metrics, stock_data):
    with open('outputs/reports/comprehensive_report.txt', 'w') as f:
        f.write("InvestIQ ML Pipeline - Model Performance Report\n")
        for symbol, met in metrics.items():
            f.write(f"{symbol}: R²: {met['R²']:.3f}  RMSE: {met['RMSE']:.2f}\n")
