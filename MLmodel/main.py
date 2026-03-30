"""
main.py
-------
CLI entry point for the InvestIQ ML pipeline.

Run order:
    1. python seed_database.py       # one-time DB seeding
    2. python main.py                # train LSTM + recommender, then evaluate
"""

import logging
import os
from datetime import datetime

from config import Config
from data_collector import StockDataCollector
from lstm_model import LSTMModelTrainer
from portfolio_recommender import PortfolioRecommender
from evaluate import run_evaluation


def setup_logging():
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(
                f"logs/pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
                encoding="utf-8",
            ),
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger(__name__)


def main():
    logger = setup_logging()
    logger.info("==== Starting InvestIQ ML Pipeline ====")

    config      = Config()
    collector   = StockDataCollector(config)
    trainer     = LSTMModelTrainer(config)
    recommender = PortfolioRecommender(config)

    # ── 1. Fetch market data ───────────────────────────────────────────────────
    logger.info("Fetching stock data...")
    stock_data = collector.fetch_all_stocks()
    logger.info("Stock data loaded for %d stocks.", len(stock_data))

    # ── 2. Train LSTM models ───────────────────────────────────────────────────
    logger.info("Training LSTM models...")
    models, metrics = trainer.train_all_models(stock_data)
    logger.info("Trained %d models.", len(models))

    # ── 3. Train recommender from private DB ───────────────────────────────────
    # seed_database.py must be run first to populate investiq_profiles.db.
    # If the DB is missing, train() will raise FileNotFoundError with a clear message.
    logger.info("Training recommender from synthetic profiles database...")
    recommender.train(stock_data)   # user_profiles=None → loads from DB
    logger.info("Recommender training complete.")

    # ── 4. Evaluate ───────────────────────────────────────────────────────────
    logger.info("Evaluating LSTM models...")
    eval_report = run_evaluation(config)
    logger.info("Evaluation complete: %s", eval_report)

    logger.info("==== InvestIQ ML Pipeline Complete! ====")


if __name__ == "__main__":
    main()