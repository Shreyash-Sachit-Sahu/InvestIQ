from flask import Flask, request, jsonify, current_app
import joblib
import os

app = Flask(__name__)

# Configure your model directory here
app.config['MODEL_DIR'] = "../MLmodel/outputs/"  # Adjust to your path


class PredictionModelWrapper:
    """
    Wraps the predictions DataFrame and portfolios metadata,
    and produces recommendations based on user investment goal and risk tolerance.
    """

    def __init__(self, predictions_df, portfolios_df):
        self.pred_df = predictions_df
        self.portfolios_df = portfolios_df

    def predict(self, investment_goal, risk_tolerance=None):
        goal_to_portfolios = {
            "capital growth": ["Max Sharpe", "Risk Parity"],
            "regular income": ["Min Variance"],
            "balanced growth and income": ["Max Sharpe", "Min Variance"],
            "capital preservation": ["Min Variance"],
            "retirement planning": ["Risk Parity", "Max Sharpe"],
            "elss": ["Max Sharpe"],
        }

        investment_goal = investment_goal.lower() if investment_goal else ""
        strategies = goal_to_portfolios.get(investment_goal, ["Max Sharpe"])

        if risk_tolerance:
            risk_tolerance = risk_tolerance.lower()
            allowed_strategies = []
            for strat in strategies:
                if strat in self.portfolios_df.index:
                    vol = self.portfolios_df.loc[strat].get("volatility") or self.portfolios_df.loc[strat].get("risk_score")
                    if vol is not None:
                        if risk_tolerance == "low" and vol <= 0.1:
                            allowed_strategies.append(strat)
                        elif risk_tolerance == "medium" and vol <= 0.2:
                            allowed_strategies.append(strat)
                        elif risk_tolerance == "high":
                            allowed_strategies.append(strat)
                    else:
                        allowed_strategies.append(strat)
                else:
                    allowed_strategies.append(strat)
            if allowed_strategies:
                strategies = allowed_strategies

        try:
            last_date = self.pred_df["Date"].max()
            latest_preds = self.pred_df[self.pred_df["Date"] == last_date]
        except Exception as e:
            return {"error": f"Error processing prediction dates: {str(e)}"}

        recommendations = []

        for portfolio_name in strategies:
            if portfolio_name not in latest_preds.columns:
                continue
            try:
                portfolio_weights = latest_preds[latest_preds[portfolio_name] > 0][[portfolio_name]]
                for symbol, row in portfolio_weights.iterrows():
                    weight = row[portfolio_name]
                    portfolio_metrics = self.portfolios_df.loc[portfolio_name].to_dict() if portfolio_name in self.portfolios_df.index else {}
                    recommendations.append({
                        "symbol": symbol,
                        "portfolio_strategy": portfolio_name,
                        "weight": float(weight),
                        "reasoning": f"Selected from {portfolio_name} portfolio matching your investment goal.",
                        "confidence": 90,
                        "portfolio_metrics": portfolio_metrics
                    })
            except Exception:
                continue

        aggregated_recs = {}
        for rec in recommendations:
            sym = rec["symbol"]
            if sym in aggregated_recs:
                aggregated_recs[sym]["weight"] += rec["weight"]
                aggregated_recs[sym]["reasoning"] += f" Also suggested in {rec['portfolio_strategy']}."
            else:
                aggregated_recs[sym] = rec

        top_recommendations = sorted(aggregated_recs.values(), key=lambda x: x["weight"], reverse=True)[:10]

        return {
            "portfolio": top_recommendations,
            "summary": {
                "investment_goal": investment_goal,
                "risk_tolerance": risk_tolerance,
                "selected_portfolios": strategies,
                "total_recommendations": len(top_recommendations),
            },
            "insights": [
                "Recommendations consider both your investment goal and risk tolerance.",
                "Portfolio metrics are included to provide additional context per strategy.",
                "Refine your input for more tailored results."
            ],
        }


def get_ai_recommendations(preferences):
    model_dir = current_app.config.get("MODEL_DIR", "../MLmodel/models/")
    predictions_path = os.path.join(model_dir, "predictions.pkl")
    portfolios_path = os.path.join(model_dir, "portfolios.pkl")

    if not os.path.exists(predictions_path) or not os.path.exists(portfolios_path):
        return {
            "portfolio": [
                {
                    "symbol": "TCS",
                    "name": "Tata Consultancy Services",
                    "weight": 25,
                    "confidence": 90,
                    "reasoning": "Strong growth in IT sector.",
                    "sector": "Information Technology",
                    "expectedReturn": 15.2,
                    "riskScore": 6,
                },
                {
                    "symbol": "RELIANCE",
                    "name": "Reliance Industries",
                    "weight": 20,
                    "confidence": 85,
                    "reasoning": "Diversified business, market leader.",
                    "sector": "Oil & Gas",
                    "expectedReturn": 12.5,
                    "riskScore": 5,
                },
            ],
            "summary": {
                "totalExpectedReturn": 13.8,
                "portfolioRiskScore": 5.5,
                "diversificationScore": 8.0,
                "alignmentScore": 95,
            },
            "insights": [
                "Consider increasing exposure to renewable energy stocks.",
                "Mid-cap IT stocks show strong potential for the next quarter.",
            ],
        }

    try:
        predictions_df = joblib.load(predictions_path)
        portfolios_df = joblib.load(portfolios_path)
    except Exception as e:
        return {"error": f"Unable to load prediction files: {str(e)}"}

    recommender = PredictionModelWrapper(predictions_df, portfolios_df)

    investment_goal = preferences.get("investment_goal") or ""
    risk_tolerance = preferences.get("risk_tolerance")  # Optional

    return recommender.predict(investment_goal, risk_tolerance)


@app.route("/ai/recommend-nse", methods=["POST"])
def ai_recommend_nse():
    preferences = request.get_json()
    if not preferences:
        return jsonify({"error": "Missing JSON payload"}), 400

    if "investment_goal" not in preferences:
        return jsonify({"error": "Missing required field: investment_goal"}), 400

    recommendations = get_ai_recommendations(preferences)
    if isinstance(recommendations, dict) and "error" in recommendations:
        return jsonify(recommendations), 500

    return jsonify(recommendations)


if __name__ == "__main__":
    app.run(debug=True)
