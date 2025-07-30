import os
import logging
import joblib
import pandas as pd
from datetime import datetime

from config import Config
from src.data_collector import StockDataCollector
from src.lstm_model import LSTMModelTrainer
from src.portfolio_optimizer import PortfolioOptimizer
from src.predictor import FuturePredictor
from src.visualizer import Visualizer
from src.utils import setup_directories, save_results, generate_report
from src.portfolio_recommender import PortfolioRecommender


def setup_logging():
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.FileHandler(f'logs/pipeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def main():
    logger = setup_logging()
    logger.info("==== Starting InvestIQ ML Pipeline ====")

    config = Config()
    setup_directories()

    try:
        # Phase 1: Data Collection & Feature Engineering
        logger.info("--- Data Collection & Feature Engineering ---")
        collector = StockDataCollector(config)
        stock_data = collector.fetch_all_stocks()
        logger.info(f"Collected data for {len(stock_data)} stocks.")

        # Phase 2: LSTM Model Training
        logger.info("--- LSTM Model Training ---")
        trainer = LSTMModelTrainer(config)
        models, metrics = trainer.train_all_models(stock_data)
        logger.info(f"Trained {len(models)} LSTM models.")

        # Phase 3: Portfolio Optimization
        logger.info("--- Portfolio Optimization ---")
        optimizer = PortfolioOptimizer(stock_data, config)
        portfolios = optimizer.optimize_all_strategies()
        logger.info(f"Optimized portfolios for {len(portfolios)} strategies.")

        # Phase 4: Future Price Prediction
        logger.info("--- Future Price Prediction ---")
        predictor = FuturePredictor(models, config)
        predictions = predictor.predict_all_stocks(stock_data)
        logger.info(f"Predicted future prices for {len(predictions)} stocks.")

        # Prepare predictions.pkl and portfolios.pkl for backend
        last_date = max(df['Date'].max() for df in stock_data.values())
        strategy_names = list(portfolios.keys())
        symbols = list(stock_data.keys())

        predictions_for_backend = {}

        for idx, symbol in enumerate(symbols):
            data = {'Date': [last_date]}
            for strat in strategy_names:
                weights = portfolios[strat]['weights']
                if isinstance(weights, pd.Series):
                    weight = weights.get(symbol, 0.0)
                else:
                    weight = float(weights[idx])
                data[strat] = [float(weight)]
            predictions_for_backend[symbol] = pd.DataFrame(data)

        os.makedirs(config.outputs_dir, exist_ok=True)
        predictions_path = os.path.join(config.outputs_dir, 'predictions.pkl')
        joblib.dump(predictions_for_backend, predictions_path)
        logger.info(f"Saved predictions.pkl with {len(predictions_for_backend)} symbols at {predictions_path}")

        portfolios_meta = pd.DataFrame([
            {
                'strategy': strat,
                'return': float(meta['return']),
                'volatility': float(meta['volatility']),
                'sharpe_ratio': float(meta['sharpe_ratio'])
            }
            for strat, meta in portfolios.items()
        ]).set_index('strategy')

        portfolios_path = os.path.join(config.outputs_dir, 'portfolios.pkl')
        joblib.dump(portfolios_meta, portfolios_path)
        logger.info(f"Saved portfolios.pkl with strategies: {strategy_names} at {portfolios_path}")

        # Phase 5: Visualization (optional)
        logger.info("--- Visualization ---")
        visualizer = Visualizer(config)
        visualizer.plot_model_performance(metrics)
        visualizer.plot_portfolio_allocations(portfolios)
        visualizer.plot_future_predictions(predictions, stock_data)
        logger.info("Visualizations generated.")

        # Phase 6: Save other results & generate reports
        save_results(models, portfolios, predictions, metrics, stock_data)
        generate_report(models, portfolios, predictions, metrics, stock_data)
        logger.info("Results saved and reports generated.")

        # Phase 7: Save PortfolioRecommender for backend (optional)
        logger.info("--- Serializing PortfolioRecommender ---")
        recommender = PortfolioRecommender(config.models_dir, config.selected_stocks, config)
        joblib.dump(recommender, os.path.join(config.models_dir, "portfolio.pkl"))
        logger.info("PortfolioRecommender saved as portfolio.pkl.")

        logger.info("==== InvestIQ ML Pipeline Completed Successfully ====")

    except Exception as e:
        logger.error(f"Pipeline failed with exception: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
