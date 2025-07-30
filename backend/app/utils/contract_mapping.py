import yfinance as yf
from datetime import datetime

MODEL_VERSION = "v2.1.0"
DATA_SOURCE = "NSE"


def yfinance_enrich(symbol):
    yf_symbol = f"{symbol}.NS"
    try:
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info
        return {
            "name": info.get("longName") or info.get("shortName") or symbol,
            "sector": info.get("sector", ""),
            "currentPrice": info.get("currentPrice"),
            "marketCap": info.get("marketCap"),
            "pe": info.get("trailingPE"),
            "dividend": info.get("dividendYield", 0) * 100 if info.get("dividendYield") is not None else None,
        }
    except Exception:
        return {
            "name": symbol,
            "sector": "",
            "currentPrice": None,
            "marketCap": None,
            "pe": None,
            "dividend": None,
        }


def make_success_response(portfolio, summary, insights, user_id=None, processing_time=0, message="AI recommendations generated successfully"):
    return {
        "success": True,
        "data": {
            "portfolio": portfolio,
            "summary": summary,
            "insights": insights,
            "metadata": {
                "generatedAt": datetime.utcnow().isoformat() + "Z",
                "modelVersion": MODEL_VERSION,
                "dataSource": DATA_SOURCE,
                "processingTime": processing_time,
                "userId": user_id,
            }
        },
        "message": message
    }


def make_error_response(error_msg, user_id=None, processing_time=0):
    return {
        "success": False,
        "data": {
            "portfolio": [],
            "summary": {
                "totalExpectedReturn": 0,
                "portfolioRiskScore": 0,
                "diversificationScore": 0,
                "alignmentScore": 0,
            },
            "insights": [],
            "metadata": {
                "generatedAt": datetime.utcnow().isoformat() + "Z",
                "modelVersion": MODEL_VERSION,
                "dataSource": DATA_SOURCE,
                "processingTime": processing_time,
                "userId": user_id,
            },
        },
        "error": error_msg
    }
