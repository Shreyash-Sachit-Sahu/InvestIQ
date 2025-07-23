import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

class Visualizer:
    def __init__(self, config):
        self.config = config
        os.makedirs(os.path.join(self.config.outputs_dir, "plots"), exist_ok=True)

    def plot_model_performance(self, metrics):
        if not metrics:
            return
        d = pd.DataFrame([dict(Stock=k, **v) for k, v in metrics.items()])
        d = d.sort_values('R²', ascending=False)
        fig, ax = plt.subplots(figsize=(16,6))
        ax.bar(d['Stock'], d['R²'], color='steelblue')
        ax.set_xticklabels(d['Stock'], rotation=90)
        ax.set_title("Test R² by Stock")
        plt.tight_layout()
        plt.savefig(os.path.join(self.config.outputs_dir, "plots", "model_r2.png"))
        plt.close()

    def plot_portfolio_allocations(self, portfolios):
        fig, ax = plt.subplots(figsize=(8,8))
        for name, port in portfolios.items():
            w = port['weights']
            ax.plot(np.sort(w)[::-1], label=name)
        ax.set_ylabel("Weight")
        ax.set_title("Portfolio Weight Distribution")
        ax.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(self.config.outputs_dir, "plots", "portfolio_allocations.png"))
        plt.close()

    def plot_future_predictions(self, predictions, stock_data):
        outdir = os.path.join(self.config.outputs_dir, "plots")
        for symbol, pred_df in predictions.items():
            plt.figure(figsize=(10,4))
            plt.plot(stock_data[symbol]['Date'], stock_data[symbol]['Close'], label='History')
            plt.plot(pred_df['Date'], pred_df['Predicted_Close'], 'r--', label='Predicted')
            plt.title(symbol)
            plt.legend()
            plt.savefig(f"{outdir}/{symbol}_future_pred.png")
            plt.close()
