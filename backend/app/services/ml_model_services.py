import os
import joblib
from flask import current_app

class PredictionModelWrapper:
    """
    Wraps a pandas DataFrame loaded from predictions.pkl and
    exposes a .predict(preferences) method expected by the backend.
    """

    def __init__(self, predictions_df):
        self.pred_df = predictions_df

    def predict(self, preferences):
        """
        Generate AI recommendations based on user preferences.

        Args:
            preferences (dict): User preferences, e.g. risk tolerance, sectors etc.

        Returns:
            dict: AI recommendation results structured for frontend consumption.
        """
        # Example simplistic logic: return the top N predicted closes for requested symbols
        # In practice, you would implement meaningful filtering based on preferences

        # For demo, just pick top 5 stocks by their latest 'Predicted_Close' value
        try:
            # Get last date in predictions
            last_date = self.pred_df['Date'].max()
            latest_preds = self.pred_df[self.pred_df['Date'] == last_date]

            # Sort by predicted close descending
            top_preds = latest_preds.sort_values(by='Predicted_Close', ascending=False).head(5)

            recommendations = []
            for _, row in top_preds.iterrows():
                recommendations.append({
                    "symbol": row.name,  # Index is stock symbol
                    "date": row['Date'].strftime("%Y-%m-%d"),
                    "predicted_close": float(row['Predicted_Close']),
                    "name": f"{row.name} Ltd.",  # You can enhance this from separate lookup
                    "reasoning": "Strong predicted close according to model",
                    "confidence": 90  # mocked confidence score
                })

            return {
                "portfolio": recommendations,
                "summary": {
                    "note": "Top 5 predicted stock closes for latest date",
                    "count": len(recommendations),
                },
                "insights": [
                    "These stocks have the highest predicted closing prices.",
                    "Use as a baseline, customize with your risk preferences."
                ]
            }

        except Exception as e:
            # fallback or error response
            return {
                "error": f"Prediction processing error: {str(e)}"
            }


def get_ai_recommendations(preferences):
    """
    Loads the predictions.pkl DataFrame, wraps it,
    and returns recommendations using the wrapper's predict method.
    Falls back to mock data if file not found.
    """

    model_dir = current_app.config.get("MODEL_DIR", "../MLmodel/models/")
    model_path = os.path.join(model_dir, "predictions.pkl")

    if not os.path.exists(model_path):
        # Fallback mock data for demonstration
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

    # Load predictions DataFrame
    pred_df = joblib.load(model_path)
    recommender = PredictionModelWrapper(pred_df)
    return recommender.predict(preferences)
