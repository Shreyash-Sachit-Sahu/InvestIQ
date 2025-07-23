import os
import sys
import logging
from datetime import datetime

# Add 'src' to sys.path for module imports
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from config import Config
from src.data_collector import StockDataCollector
from src.lstm_model import LSTMModelTrainer
from src.portfolio_optimizer import PortfolioOptimizer
from src.predictor import FuturePredictor
from src.visualizer import Visualizer
from src.utils import setup_directories, save_results, generate_report
from src.portfolio_recommender import PortfolioRecommender
import joblib

def setup_logging():
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.FileHandler(f'logs/pipeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def main():
    logger = setup_logging()
    logger.info("==== Starting InvestIQ ML Pipeline ====")
    setup_directories()
    config = Config()

    try:
        # Phase 1: Data Collection & Feature Engineering
        logger.info("--- Data Collection & Feature Generation ---")
        collector = StockDataCollector(config)
        stock_data = collector.fetch_all_stocks()
        logger.info(f"Stock data loaded for {len(stock_data)} stocks.")

        # Phase 2: LSTM Model Training with GridSearchCV
        logger.info("--- LSTM Model Training with Grid Search ---")
        trainer = LSTMModelTrainer(config)
        models, metrics = trainer.train_all_models(stock_data, use_grid_search=True)
        logger.info(f"Trained and tuned {len(models)} models with metrics saved.")

        # Phase 3: Portfolio Optimization
        logger.info("--- Portfolio Optimization ---")
        optimizer = PortfolioOptimizer(stock_data, config)
        portfolios = optimizer.optimize_all_strategies()
        logger.info(f"Optimized {len(portfolios)} strategies.")

        # Phase 4: Future Price Prediction
        logger.info("--- Future Price Prediction ---")
        predictor = FuturePredictor(models, config)
        predictions = predictor.predict_all_stocks(stock_data)
        logger.info(f"Predicted future prices for {len(predictions)} stocks.")

        # Phase 5: Visualization
        logger.info("--- Visualization ---")
        visualizer = Visualizer(config)
        visualizer.plot_model_performance(metrics)
        visualizer.plot_portfolio_allocations(portfolios)
        visualizer.plot_future_predictions(predictions, stock_data)
        logger.info("Visualization generated.")

        # Phase 6: Save Results & Generate Report
        save_results(models, portfolios, predictions, metrics, stock_data)
        generate_report(models, portfolios, predictions, metrics, stock_data)
        logger.info("All results and reports saved.")

        # Phase 7: Portfolio Recommender Serialization
        logger.info("Saving PortfolioRecommender for backend inference.")
        recommender = PortfolioRecommender(config.models_dir, config.selected_stocks, config)
        joblib.dump(recommender, os.path.join(config.models_dir, "portfolio.pkl"))
        logger.info("PortfolioRecommender saved as portfolio.pkl.")

        logger.info("==== InvestIQ ML Pipeline Complete! ====")
    except Exception as e:
        logger.error(f"Pipeline failed due to: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
