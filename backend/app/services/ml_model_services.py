import os
import joblib
from flask import current_app
from datetime import datetime
import pickle

class PredictionModelWrapper:
    """
    Wraps the predictions DataFrame and produces recommendations
    based on user risk tolerance and primary investment goals,
    coordinating with portfolio strategies (Max Sharpe, Min Variance, etc.).
    """

    def __init__(self, predictions_df):
        self.pred_df = predictions_df  # DataFrame with portfolio strategies as columns and symbols as index

    def predict(self, preferences):
        risk_tolerance = preferences.get("risk_tolerance", "").lower()
        investment_goals = preferences.get("investment_goals", [])

        # Map primary investment goals to portfolio strategies
        goal_to_portfolios = {
            "capital growth": ["Max Sharpe", "Risk Parity"],
            "regular income": ["Min Variance"],
            "balanced growth and income": ["Max Sharpe", "Min Variance"],
            "capital preservation": ["Min Variance"],
            "retirement planning": ["Risk Parity", "Max Sharpe"],
            "elss": ["Max Sharpe"],
        }

        # Collect relevant portfolio strategies for the user's goals
        relevant_portfolios = set()
        for goal in investment_goals:
            strategies = goal_to_portfolios.get(goal.lower())
            if strategies:
                relevant_portfolios.update(strategies)
        if not relevant_portfolios:
            # Default fallback portfolio
            relevant_portfolios = {"Max Sharpe"}

        # Attempt to filter predictions for latest date
        try:
            last_date = self.pred_df['Date'].max()
            latest_preds = self.pred_df[self.pred_df['Date'] == last_date]
        except Exception as e:
            return {"error": f"Error processing prediction dates: {str(e)}"}

        # Aggregate recommendations from relevant portfolios
        recommendations = []

        for portfolio_name in relevant_portfolios:
            if portfolio_name not in latest_preds.columns:
                # Skip if a portfolio strategy column not present
                continue

            try:
                portfolio_weights = latest_preds[latest_preds[portfolio_name] > 0][[portfolio_name]]
                for symbol, row in portfolio_weights.iterrows():
                    weight = row[portfolio_name]
                    recommendations.append({
                        "symbol": symbol,
                        "portfolio_strategy": portfolio_name,
                        "weight": float(weight),
                        "reasoning": f"Selected from {portfolio_name} portfolio matching your investment goals.",
                        "confidence": 90  # example confidence
                    })
            except Exception:
                # Continue if error occurs for this portfolio
                continue

        # Combine recommendations with same symbols by summing weights
        aggregated_recs = {}
        for rec in recommendations:
            sym = rec["symbol"]
            if sym in aggregated_recs:
                aggregated_recs[sym]["weight"] += rec["weight"]
                # Optional: Combine reasoning or confidence if desired
            else:
                aggregated_recs[sym] = rec

        # Sort by descending combined weight
        sorted_recs = sorted(aggregated_recs.values(), key=lambda x: x["weight"], reverse=True)

        # Limit to top 10 recommendations
        top_recommendations = sorted_recs[:10]

        return {
            "portfolio": top_recommendations,
            "summary": {
                "risk_tolerance": risk_tolerance,
                "investment_goals": investment_goals,
                "selected_portfolios": list(relevant_portfolios),
                "total_recommendations": len(top_recommendations),
            },
            "insights": [
                "Recommendations are aggregated from portfolio strategies aligned to your goals.",
                "Weights indicate relative significance per portfolio strategy.",
                "Refine your preferences for more personalized results."
            ],
        }


def get_ai_recommendations(preferences):
    """
    Loads predictions.pkl and returns AI recommendations based on user preferences.
    Returns fallback mock data if the file is missing.
    """
    model_dir = current_app.config.get("MODEL_DIR", "../MLmodel/models/")
    model_path = os.path.join(model_dir, "predictions.pkl")

    if not os.path.exists(model_path):
        # Fallback: mock data for demo/testing
        return {
            "portfolio": [
                {
                    "symbol": "TCS",
                    "name": "Tata Consultancy Services",
                    "allocation": 25,
                    "confidence": 90,
                    "reasoning": "Strong growth in IT sector.",
                    "sector": "Information Technology",
                    "expectedReturn": 15.2,
                    "riskScore": 6
                },
                {
                    "symbol": "RELIANCE",
                    "name": "Reliance Industries",
                    "allocation": 20,
                    "confidence": 85,
                    "reasoning": "Diversified business, market leader.",
                    "sector": "Oil & Gas",
                    "expectedReturn": 12.5,
                    "riskScore": 5
                }
            ],
            "summary": {
                "totalExpectedReturn": 13.8,
                "portfolioRiskScore": 5.5,
                "diversificationScore": 8.0,
                "alignmentScore": 95
            },
            "insights": [
                "Consider increasing exposure to renewable energy stocks.",
                "Mid-cap IT stocks show strong potential for the next quarter."
            ]
        }

    predictions_df = joblib.load(model_path)
    recommender = PredictionModelWrapper(predictions_df)
    return recommender.predict(preferences)
