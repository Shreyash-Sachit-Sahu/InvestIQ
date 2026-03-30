from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

try:
    from config import Config
    from data_collector import StockDataCollector
    from lstm_model import LSTMModelTrainer, CUSTOM_OBJECTS
    from portfolio_recommender import PortfolioRecommender, CATEGORICAL_VOCAB
    from evaluate import run_evaluation
except ImportError:
    from MLmodel.config import Config
    from MLmodel.data_collector import StockDataCollector
    from MLmodel.lstm_model import LSTMModelTrainer, CUSTOM_OBJECTS
    from MLmodel.portfolio_recommender import PortfolioRecommender, CATEGORICAL_VOCAB
    from MLmodel.evaluate import run_evaluation

app    = FastAPI(title="InvestIQ ML API", version="1.0")
logger = logging.getLogger("InvestIQML")


class PredictRequest(BaseModel):
    symbol: str
    days:   Optional[int] = None


class RecommendRequest(BaseModel):
    riskTolerance:        str
    investmentHorizon:    str
    primaryGoal:          str
    hasEmergencyFund:     str
    investmentExperience: str
    sectors:              Optional[List[str]] = []
    investmentAmount:     float
    age:                  int
    currentIncome:        float


@app.on_event("startup")
def startup_event():
    global config, collector, trainer, recommender
    config      = Config()
    collector   = StockDataCollector(config)
    trainer     = LSTMModelTrainer(config)
    recommender = PortfolioRecommender(config)
    logger.info("InvestIQ ML API started.")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/train")
def train_models():
    stock_data = collector.fetch_all_stocks()
    if not stock_data:
        raise HTTPException(status_code=500, detail="No stock data fetched")

    models, metrics = trainer.train_all_models(stock_data)

    # train() with no user_profiles → loads from private DB automatically
    recommender.train(stock_data)

    return {"trained": list(models.keys()), "metrics": metrics}


@app.post("/predict")
def predict(request: PredictRequest):
    symbol = request.symbol.upper()
    days   = request.days or config.prediction_days

    stock_data = collector.fetch_all_stocks()
    if symbol not in stock_data:
        raise HTTPException(status_code=404, detail=f"{symbol} data not available")

    model_path = f"{config.models_dir}/{symbol}_lstm_model.keras"
    try:
        from tensorflow.keras.models import load_model
        model = load_model(model_path, custom_objects=CUSTOM_OBJECTS)
    except Exception:
        raise HTTPException(status_code=500, detail="Trained model not found for symbol")

    try:
        trainer.load_scaler(symbol)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Scaler not found — retrain the model first")

    df = stock_data[symbol]
    X, y_scaled = trainer.prepare_data(df, symbol=symbol, fit_scaler=False)
    if len(X) == 0:
        raise HTTPException(status_code=400, detail="Insufficient data for prediction")

    last_sequence      = X[-1:]
    pred_scaled        = model.predict(last_sequence, verbose=0)[0]
    predictions_rupees = trainer.inverse_transform_close(symbol, pred_scaled)

    return {
        "symbol":      symbol,
        "predictions": [round(float(p), 2) for p in predictions_rupees[:days]],
    }


@app.post("/recommend")
def recommend(request: RecommendRequest):
    # Validate all categorical fields upfront with clear 422 errors
    prefs = request.dict()
    for field, valid_values in CATEGORICAL_VOCAB.items():
        value = prefs.get(field)
        if value and value not in valid_values:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid value '{value}' for '{field}'. Must be one of: {valid_values}",
            )

    stock_data = collector.fetch_all_stocks()
    if not stock_data:
        raise HTTPException(status_code=500, detail="No stock data available")

    try:
        recommender.load()
    except FileNotFoundError:
        # Model not trained yet — train now from DB
        recommender.train(stock_data)

    try:
        result = recommender.recommend(prefs, stock_data)
    except KeyError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Recommender missing mapping for: {e}. Call POST /train to retrain.",
        )
    except Exception as e:
        logger.exception("Unexpected error in /recommend")
        raise HTTPException(status_code=500, detail=str(e))

    return result


@app.get("/evaluate")
def evaluate():
    report = run_evaluation(config)
    return report