import os
import joblib
from flask import current_app

def get_ai_recommendations(preferences):
    """
    Loads the portfolio recommender model and runs its `predict()` method.
    If the model file is missing, returns a mock AI recommendation result.

    Args:
        preferences (dict): The user's investment preferences and/or portfolio.

    Returns:
        dict: The model's recommendation or a mock output.
    """
    model_dir = current_app.config.get("MODEL_DIR", "MLmodel/outputs/")
    model_path = os.path.join(model_dir, "portfolios.pkl")

    if not os.path.exists(model_path):
        # --- MOCK result for demo, TODO: Replace with real model output ---
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
                # ... add more mock stocks as needed
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
    # --- Real model inference ---
    recommender = joblib.load(model_path)
    return recommender.predict(preferences)
