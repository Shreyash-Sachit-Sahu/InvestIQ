import joblib
import os
from flask import current_app
import pandas as pd


class PredictionModelWrapper:
    def __init__(self, predictions_data, portfolios_data):
        """
        :param predictions_data: Either a DataFrame with a 'Date' column (legacy) or
                                 a dict mapping symbols to DataFrames with 'Date' column.
        :param portfolios_data: Either a Pandas DataFrame indexed by portfolio strategy names or
                                a dict mapping portfolio strategy names to metadata dicts.
        """
        self.pred_data = predictions_data
        self.portfolios_df = portfolios_data

    def predict(self, investment_goal, risk_tolerance=None):
        goal_to_portfolios = {
            "capital growth": ["Max Sharpe", "Risk Parity"],
            "regular income": ["Min Variance"],
            "balanced growth and income": ["Max Sharpe", "Min Variance"],
            "capital preservation": ["Min Variance"],
            "retirement planning": ["Risk Parity", "Max Sharpe"],
            "elss": ["Max Sharpe"],
        }

        investment_goal = str(investment_goal).lower() if investment_goal else ""
        strategies = goal_to_portfolios.get(investment_goal, ["Max Sharpe"])

        # Normalize risk tolerance strings to expected values
        if risk_tolerance:
            risk_tolerance = str(risk_tolerance).lower()
        else:
            risk_tolerance = None

        allowed_strategies = []

        is_portfolios_dict = isinstance(self.portfolios_df, dict)

        # Filter strategies by risk tolerance if provided
        if risk_tolerance:
            for strat in strategies:
                # Get portfolio risk metrics
                if is_portfolios_dict:
                    port_info = self.portfolios_df.get(strat, {})
                    vol = port_info.get("volatility") or port_info.get("risk_score")
                else:
                    if strat in self.portfolios_df.index:
                        port_info = self.portfolios_df.loc[strat]
                        vol = port_info.get("volatility") or port_info.get("risk_score")
                    else:
                        vol = None

                if vol is not None:
                    if risk_tolerance == "conservative" and vol <= 0.1:
                        allowed_strategies.append(strat)
                    elif risk_tolerance == "moderate" and vol <= 0.2:
                        allowed_strategies.append(strat)
                    elif risk_tolerance == "aggressive":
                        allowed_strategies.append(strat)
                else:
                    # Default to allow if no volatility info
                    allowed_strategies.append(strat)

            strategies = allowed_strategies if allowed_strategies else strategies

        recommendations = []

        is_pred_dict = isinstance(self.pred_data, dict)

        # Process predictions, supporting dict of DataFrames (by symbol)
        if is_pred_dict:
            # Aggregate recommendations across selected strategies by combining symbol weights
            for strat in strategies:
                # For each symbol's prediction DataFrame in dict, check if strat is a column
                for symbol, pred_df in self.pred_data.items():
                    if strat not in pred_df.columns:
                        continue

                    try:
                        last_date = pred_df["Date"].max()
                        latest_pred_df = pred_df[pred_df["Date"] == last_date]
                    except Exception:
                        # If no Date or invalid, skip this symbol
                        continue

                    # Get weights for this portfolio strategy
                    portfolio_weights = latest_pred_df[latest_pred_df[strat] > 0][[strat]]

                    for idx, row in portfolio_weights.iterrows():
                        weight = row[strat]
                        # Get portfolio metrics for this strategy
                        if is_portfolios_dict:
                            portfolio_metrics = self.portfolios_df.get(strat, {})
                        else:
                            portfolio_metrics = (
                                self.portfolios_df.loc[strat].to_dict()
                                if strat in self.portfolios_df.index else {}
                            )

                        recommendations.append({
                            "symbol": symbol,
                            "portfolio_strategy": strat,
                            "weight": float(weight),
                            "reasoning": f"Selected from {strat} portfolio matching your investment goal.",
                            "confidence": 90,
                            "portfolio_metrics": portfolio_metrics,
                        })
        else:
            # Legacy: if predictions in single DataFrame with Date column
            try:
                last_date = self.pred_data["Date"].max()
                latest_preds = self.pred_data[self.pred_data["Date"] == last_date]
            except Exception as e:
                return {"error": f"Error processing prediction dates: {str(e)}"}

            for portfolio_name in strategies:
                if portfolio_name not in latest_preds.columns:
                    continue
                try:
                    portfolio_weights = latest_preds[latest_preds[portfolio_name] > 0][[portfolio_name]]
                    for symbol, row in portfolio_weights.iterrows():
                        weight = row[portfolio_name]
                        if is_portfolios_dict:
                            portfolio_metrics = self.portfolios_df.get(portfolio_name, {})
                        else:
                            portfolio_metrics = (
                                self.portfolios_df.loc[portfolio_name].to_dict()
                                if portfolio_name in self.portfolios_df.index else {}
                            )
                        recommendations.append({
                            "symbol": symbol,
                            "portfolio_strategy": portfolio_name,
                            "weight": float(weight),
                            "reasoning": f"Selected from {portfolio_name} portfolio matching your investment goal.",
                            "confidence": 90,
                            "portfolio_metrics": portfolio_metrics,
                        })
                except Exception:
                    continue

        # Aggregate multiple recommendations for same symbol across strategies
        aggregated_recs = {}
        for rec in recommendations:
            sym = rec["symbol"]
            if sym in aggregated_recs:
                aggregated_recs[sym]["weight"] += rec["weight"]
                aggregated_recs[sym]["reasoning"] += f" Also suggested in {rec['portfolio_strategy']}."
            else:
                aggregated_recs[sym] = rec

        top_recommendations = sorted(
            aggregated_recs.values(), key=lambda x: x["weight"], reverse=True
        )[:10]

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
                "Refine your input for more tailored results.",
            ],
        }


def get_ai_recommendations(preferences):
    model_dir = current_app.config.get("MODEL_DIR", "../MLmodel/outputs/")
    predictions_path = os.path.join(model_dir, "predictions.pkl")
    portfolios_path = os.path.join(model_dir, "portfolios.pkl")

    if not os.path.exists(predictions_path):
        return {"error": f"Predictions file not found at {predictions_path}"}
    if not os.path.exists(portfolios_path):
        return {"error": f"Portfolios file not found at {portfolios_path}"}

    try:
        predictions_data = joblib.load(predictions_path)
        portfolios_data = joblib.load(portfolios_path)
        current_app.logger.info(f"Loaded predictions data type: {type(predictions_data)}")
        if hasattr(predictions_data, "columns"):
            current_app.logger.info(f"Predictions columns: {predictions_data.columns.tolist()}")
        elif isinstance(predictions_data, dict):
            current_app.logger.info(f"Predictions dict keys: {list(predictions_data.keys())}")
        else:
            current_app.logger.info("Predictions data unknown format")

        current_app.logger.info(f"Loaded portfolios data type: {type(portfolios_data)}")
        if hasattr(portfolios_data, "index"):
            current_app.logger.info(f"Portfolios index: {portfolios_data.index}")
        elif isinstance(portfolios_data, dict):
            current_app.logger.info(f"Portfolios keys: {list(portfolios_data.keys())}")
        else:
            current_app.logger.info("Portfolios data unknown format")

    except Exception as e:
        return {"error": f"Unable to load prediction files: {str(e)}"}

    recommender = PredictionModelWrapper(predictions_data, portfolios_data)

    investment_goal = preferences.get("investment_goal") or ""
    risk_tolerance = preferences.get("risk_tolerance")  # Optional

    return recommender.predict(investment_goal, risk_tolerance)
