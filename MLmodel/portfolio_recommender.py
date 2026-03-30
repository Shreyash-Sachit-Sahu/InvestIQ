"""
portfolio_recommender.py
------------------------
Loads synthetic training profiles from the private SQLite/Postgres database
seeded by seed_database.py, trains a Keras model, and serves recommendations.

Key fixes vs previous version:
  - Training label is now a USER-AWARE utility score, not just mean return.
    Conservative users get penalized for high volatility; aggressive users get
    rewarded for it. This forces the model to actually learn user preferences.
  - Sector filtering: stocks in preferred sectors get a score boost.
  - Output expectedReturn and riskScore are computed from real stock statistics
    (annualised return + volatility) scaled by the user's risk tolerance —
    not from the raw tiny model score.
  - Investment horizon adjusts the expected return window.
  - CATEGORICAL_VOCAB pre-fits all LabelEncoders — no ValueError on unseen labels.
  - _safe_transform() gracefully handles unknown values.
"""

import json
import logging
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers import Dense, Dropout, Input, BatchNormalization
from tensorflow.keras.models import Sequential, load_model

# ---------------------------------------------------------------------------
# Full vocabulary — keep in sync with seed_database.py and AIAdvisorForm.tsx
# ---------------------------------------------------------------------------
CATEGORICAL_VOCAB = {
    "riskTolerance":        ["conservative", "moderate", "aggressive"],
    "investmentHorizon":    ["1-2 years", "3-5 years", "5-10 years", "10-20 years", "20+ years"],
    "primaryGoal":          ["growth", "income", "balanced", "preservation", "retirement", "tax-saving"],
    "hasEmergencyFund":     ["yes", "no"],
    "investmentExperience": ["beginner", "intermediate", "advanced", "expert"],
}

ALL_SECTORS = [
    "IT", "Finance", "Oil & Gas", "FMCG", "Pharma",
    "Auto", "Metals", "Telecom", "Power",
    "Real Estate", "Textiles", "Chemicals",
]

# Risk tolerance → volatility penalty multiplier
# Conservative users are penalised heavily for volatile stocks
RISK_PENALTY = {
    "conservative": 3.0,
    "moderate":     1.5,
    "aggressive":   0.5,
}

# Investment horizon → annualisation multiplier for expected return display
HORIZON_YEARS = {
    "1-2 years":   1.5,
    "3-5 years":   4.0,
    "5-10 years":  7.5,
    "10-20 years": 15.0,
    "20+ years":   25.0,
}

# Primary goal → return vs stability bias
# (return_weight, stability_weight)
GOAL_WEIGHTS = {
    "growth":       (1.5, 0.5),
    "income":       (1.0, 1.0),
    "balanced":     (1.0, 1.0),
    "preservation": (0.5, 2.0),
    "retirement":   (0.8, 1.5),
    "tax-saving":   (1.2, 0.8),
}

# NSE stock → sector mapping (used for sector preference boost)
STOCK_SECTOR_MAP = {
    "RELIANCE":   "Oil & Gas",
    "HDFCBANK":   "Finance",
    "ICICIBANK":  "Finance",
    "INFY":       "IT",
    "TCS":        "IT",
    "KOTAKBANK":  "Finance",
    "HDFC":       "Finance",
    "AXISBANK":   "Finance",
    "SBIN":       "Finance",
    "LT":         "Auto",
    "ITC":        "FMCG",
    "BAJFINANCE": "Finance",
    "BHARTIARTL": "Telecom",
    "HINDUNILVR": "FMCG",
    "ONGC":       "Oil & Gas",
    "MARUTI":     "Auto",
    "TITAN":      "FMCG",
    "ULTRACEMCO": "Metals",
    "NESTLEIND":  "FMCG",
    "ASIANPAINT": "Chemicals",
    "DIVISLAB":   "Pharma",
    "TECHM":      "IT",
    "EICHERMOT":  "Auto",
    "JSWSTEEL":   "Metals",
    "TATASTEEL":  "Metals",
    "WIPRO":      "IT",
    "M&M":        "Auto",
    "ADANIPORTS": "Power",
    "DRREDDY":    "Pharma",
}


# ---------------------------------------------------------------------------
# DB loader
# ---------------------------------------------------------------------------

def load_profiles_from_db(db_path: str = "investiq_profiles.db") -> pd.DataFrame:
    """Load all synthetic profiles from SQLite or Postgres."""
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        import psycopg2
        conn = psycopg2.connect(database_url)
    else:
        import sqlite3
        conn = sqlite3.connect(db_path)

    df = pd.read_sql("SELECT * FROM synthetic_profiles", conn)
    conn.close()
    df["sectors"] = df["sectors"].apply(json.loads)
    return df


# ---------------------------------------------------------------------------
# User-aware utility score
# ---------------------------------------------------------------------------

def compute_utility_score(
    mean_ret: float,
    std_ret: float,
    symbol: str,
    risk_tolerance: str,
    primary_goal: str,
    preferred_sectors: list,
) -> float:
    """
    Computes a user-specific utility score for a stock.

    Higher = more suitable for this particular user.
    This is the training label — it varies per user, forcing the model
    to actually learn preference-dependent behaviour.

    Components:
      1. Sharpe-like ratio (annualised)
      2. Penalty for volatility scaled by risk tolerance
      3. Bonus if stock is in a preferred sector
      4. Goal-specific weighting of return vs stability
    """
    ann_return  = mean_ret * 252           # annualised daily mean return
    ann_vol     = std_ret  * (252 ** 0.5)  # annualised daily std

    # Base Sharpe ratio
    sharpe = ann_return / (ann_vol + 1e-9)

    # Volatility penalty — heavier for conservative users
    penalty = RISK_PENALTY.get(risk_tolerance, 1.5) * ann_vol

    # Goal weighting
    ret_w, stab_w = GOAL_WEIGHTS.get(primary_goal, (1.0, 1.0))
    score = ret_w * sharpe - stab_w * penalty

    # Sector preference boost (+20% if stock matches any preferred sector)
    if preferred_sectors:
        stock_sector = STOCK_SECTOR_MAP.get(symbol, "")
        if stock_sector in preferred_sectors:
            score *= 1.20

    return float(score)


# ---------------------------------------------------------------------------
# Recommender
# ---------------------------------------------------------------------------

class PortfolioRecommender:
    def __init__(self, config):
        self.config         = config
        self.logger         = logging.getLogger(__name__)
        self.model_path     = os.path.join(self.config.models_dir, "recommender_model.keras")
        self.encoder_path   = os.path.join(self.config.models_dir, "recommender_encoders.pkl")
        self.scaler_path    = os.path.join(self.config.models_dir, "recommender_scaler.pkl")
        self.label_encoders = {}
        self.scaler         = StandardScaler()
        self.model          = None

    # ------------------------------------------------------------------
    # Encoding
    # ------------------------------------------------------------------

    def _fit_encoders(self) -> None:
        """Pre-fit every LabelEncoder on the complete known vocabulary."""
        for col, vocab in CATEGORICAL_VOCAB.items():
            le = LabelEncoder()
            le.fit(vocab)
            self.label_encoders[col] = le

    def _safe_transform(self, col: str, values: list) -> np.ndarray:
        """Transform, falling back to index-0 for any truly unknown value."""
        le      = self.label_encoders[col]
        known   = set(le.classes_)
        unknown = [v for v in values if v not in known]
        if unknown:
            self.logger.warning(
                "Unknown value(s) %s for field '%s'. Falling back to '%s'.",
                unknown, col, le.classes_[0],
            )
        sanitized = [v if v in known else le.classes_[0] for v in values]
        return le.transform(sanitized)

    def _encode(self, df: pd.DataFrame, fit_scaler: bool = False) -> pd.DataFrame:
        df_enc = df.copy()

        # Categorical
        for col in CATEGORICAL_VOCAB:
            if col in df_enc.columns:
                df_enc[col] = self._safe_transform(col, df_enc[col].astype(str).tolist())

        # Sector one-hot — always the same fixed columns
        if "sectors" in df_enc.columns:
            def _parse_sectors(x):
                if isinstance(x, list):
                    return x
                if isinstance(x, str):
                    try:
                        parsed = json.loads(x)
                        return parsed if isinstance(parsed, list) else []
                    except Exception:
                        return []
                return []
            secs = df_enc["sectors"].apply(_parse_sectors)
            for s in ALL_SECTORS:
                df_enc[f"sector_{s}"] = secs.apply(lambda lst: 1 if s in lst else 0)
            df_enc = df_enc.drop(columns=["sectors"])
        else:
            # No sectors column provided (e.g. inference without sectors key)
            # Still emit the fixed OHE columns as zeros so shape is consistent
            for s in ALL_SECTORS:
                col_name = f"sector_{s}"
                if col_name not in df_enc.columns:
                    df_enc[col_name] = 0

        # Drop DB metadata columns if present
        df_enc = df_enc.drop(
            columns=[c for c in ["id", "created_at", "version"] if c in df_enc.columns]
        )

        # Numeric scaling
        num_cols = ["investmentAmount", "age", "currentIncome"]
        present  = [c for c in num_cols if c in df_enc.columns]
        if present:
            if fit_scaler:
                df_enc[present] = self.scaler.fit_transform(df_enc[present])
            else:
                df_enc[present] = self.scaler.transform(df_enc[present])

        # ── Enforce a fixed, deterministic column order ───────────────────────
        # This guarantees training and inference always produce identical shapes.
        FIXED_COLS = (
            list(CATEGORICAL_VOCAB.keys())           # 5 encoded categoricals
            + [f"sector_{s}" for s in ALL_SECTORS]   # 12 OHE sector columns
            + ["investmentAmount", "age", "currentIncome"]  # 3 numerics
        )
        # Add any missing columns as 0, then select in fixed order
        for col in FIXED_COLS:
            if col not in df_enc.columns:
                df_enc[col] = 0
        df_enc = df_enc[FIXED_COLS]

        return df_enc

    # ------------------------------------------------------------------
    # Training data preparation — USER-AWARE labels
    # ------------------------------------------------------------------

    def prepare_data(self, stock_data: dict, user_profiles: pd.DataFrame):
        """
        Build (X, y) where y is a USER-SPECIFIC utility score.
        Each (user, stock) pair gets a different label depending on that
        user's risk tolerance, goal, and sector preferences.
        """
        X, y = [], []

        for _, user in user_profiles.iterrows():
            df_user       = self._encode(pd.DataFrame([user]), fit_scaler=False)
            user_features = df_user.values.flatten().tolist()

            risk_tol  = str(user.get("riskTolerance", "moderate"))
            goal      = str(user.get("primaryGoal", "growth"))
            sectors   = user.get("sectors", [])
            if isinstance(sectors, str):
                try:
                    sectors = json.loads(sectors)
                except Exception:
                    sectors = []

            for symbol, data in stock_data.items():
                if data["Return"].isna().any():
                    continue

                mean_ret = float(data["Return"].mean())
                std_ret  = float(data["Return"].std()) + 1e-9

                # ── USER-AWARE label ────────────────────────────────────
                score = compute_utility_score(
                    mean_ret, std_ret, symbol,
                    risk_tol, goal, sectors
                )
                X.append(user_features + [mean_ret, std_ret])
                y.append(score)

        return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

    # ------------------------------------------------------------------
    # Model — deeper network to capture preference interactions
    # ------------------------------------------------------------------

    def build_model(self, input_dim: int):
        model = Sequential([
            Input(shape=(input_dim,)),
            Dense(256, activation="relu"),
            BatchNormalization(),
            Dropout(0.3),
            Dense(128, activation="relu"),
            BatchNormalization(),
            Dropout(0.2),
            Dense(64, activation="relu"),
            Dropout(0.1),
            Dense(1, activation="linear"),
        ])
        model.compile(optimizer="adam", loss="mse", metrics=["mae"])
        return model

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def train(self, stock_data: dict, user_profiles: pd.DataFrame = None) -> None:
        """
        Train the recommender.
        user_profiles — pass a DataFrame for tests; None loads from private DB.
        """
        if user_profiles is None:
            db_path       = getattr(self.config, "profiles_db_path", "investiq_profiles.db")
            user_profiles = load_profiles_from_db(db_path)
            self.logger.info("Loaded %d profiles from database.", len(user_profiles))

        # 1. Pre-fit encoders on full vocabulary
        self._fit_encoders()

        # 2. Fit scaler on numeric columns
        num_cols = ["investmentAmount", "age", "currentIncome"]
        self.scaler.fit(user_profiles[num_cols])

        # 3. Build feature matrix with user-aware labels
        X, y = self.prepare_data(stock_data, user_profiles)
        if len(X) < 5:
            self.logger.warning("Not enough data for recommender training.")
            return

        self.logger.info(
            "Training recommender on %d samples. y range: [%.4f, %.4f]",
            len(X), float(y.min()), float(y.max()),
        )

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        self.model = self.build_model(X_train.shape[1])
        es = EarlyStopping(monitor="val_loss", patience=8, restore_best_weights=True)
        self.model.fit(
            X_train, y_train,
            validation_data=(X_test, y_test),
            epochs=self.config.recommender_epochs,
            batch_size=self.config.recommender_batch_size,
            callbacks=[es],
            verbose=1,
        )
        self.model.save(self.model_path)
        joblib.dump(self.label_encoders, self.encoder_path)
        joblib.dump(self.scaler, self.scaler_path)
        self.logger.info("Saved recommender artifacts.")

    def load(self) -> None:
        if not os.path.exists(self.model_path):
            raise FileNotFoundError("Recommender model not found.")
        self.model          = load_model(self.model_path)
        self.label_encoders = joblib.load(self.encoder_path)
        self.scaler         = joblib.load(self.scaler_path)

    def recommend(self, preferences: dict, stock_data: dict) -> dict:
        if self.model is None:
            self.load()

        risk_tol  = preferences.get("riskTolerance", "moderate")
        goal      = preferences.get("primaryGoal", "growth")
        horizon   = preferences.get("investmentHorizon", "3-5 years")
        sectors   = preferences.get("sectors", [])
        if isinstance(sectors, str):
            try:
                sectors = json.loads(sectors)
            except Exception:
                sectors = []

        # Encode user preferences
        user_df     = pd.DataFrame([preferences])
        encoded     = self._encode(user_df, fit_scaler=False)
        user_vector = encoded.values.flatten()

        # Score every stock
        raw_scores = []
        for symbol, df in stock_data.items():
            if df["Return"].isna().any():
                continue
            mean_ret = float(df["Return"].mean())
            std_ret  = float(df["Return"].std()) + 1e-9
            inp      = np.concatenate([user_vector, [mean_ret, std_ret]]).reshape(1, -1).astype(np.float32)
            expected_dim = self.model.input_shape[-1]
            if inp.shape[1] != expected_dim:
                raise ValueError(
                    f"Feature shape mismatch: model expects {expected_dim} features, "
                    f"but inference produced {inp.shape[1]}. "
                    f"Re-train the recommender with POST /train."
                )
            score    = float(self.model.predict(inp, verbose=0)[0, 0])
            raw_scores.append((symbol, score, mean_ret, std_ret))

        # Sort by model score and take top N
        top = sorted(raw_scores, key=lambda x: x[1], reverse=True)[: self.config.max_portfolio_stocks]

        # Allocation — proportional to score, floored at 1%
        min_score = min(s for _, s, _, _ in top)
        shifted   = [(sym, s - min_score + 1e-6, mr, sr) for sym, s, mr, sr in top]
        total     = sum(s for _, s, _, _ in shifted) or 1

        # Horizon multiplier for expected return display
        horizon_yrs = HORIZON_YEARS.get(horizon, 4.0)

        # Risk penalty scale for riskScore display (1–10)
        risk_scale = {"conservative": 0.6, "moderate": 1.0, "aggressive": 1.5}.get(risk_tol, 1.0)

        portfolio = []
        for symbol, shifted_score, mean_ret, std_ret in shifted:
            alloc = max(1.0, (shifted_score / total) * 100)

            # Real annualised stats from stock data
            ann_return_pct = mean_ret * 252 * 100        # e.g. 14.2%
            ann_vol_pct    = std_ret  * (252 ** 0.5) * 100  # e.g. 22.5%

            # Expected return over investment horizon
            expected_ret = round(ann_return_pct * (horizon_yrs ** 0.5), 1)

            # Risk score 1–10 scaled by user's risk tolerance
            raw_risk  = min(10.0, ann_vol_pct / 3.0)    # 30% vol → score 10
            risk_score = round(min(10.0, raw_risk * risk_scale), 1)

            # Confidence: higher model score + sector match = higher confidence
            base_conf    = 50 + (shifted_score / (max(s for _, s, _, _ in shifted) + 1e-9)) * 40
            sector_bonus = 5 if STOCK_SECTOR_MAP.get(symbol, "") in sectors else 0
            confidence   = min(99, round(base_conf + sector_bonus, 1))

            # Reasoning
            sector_str = STOCK_SECTOR_MAP.get(symbol, "NSE")
            reasons = []
            if STOCK_SECTOR_MAP.get(symbol, "") in sectors:
                reasons.append(f"matches your preferred {sector_str} sector")
            if risk_tol == "conservative" and ann_vol_pct < 20:
                reasons.append("low volatility suits conservative profile")
            elif risk_tol == "aggressive" and ann_return_pct > 15:
                reasons.append("high growth potential for aggressive profile")
            else:
                reasons.append(f"{risk_tol} risk profile match")
            reasoning = "; ".join(reasons).capitalize()

            portfolio.append({
                "symbol":         symbol,
                "name":           f"{symbol} Ltd.",
                "allocation":     round(alloc, 1),
                "confidence":     confidence,
                "reasoning":      reasoning,
                "sector":         sector_str,
                "expectedReturn": expected_ret,
                "riskScore":      risk_score,
            })

        # Normalise allocations to sum to 100%
        total_alloc = sum(p["allocation"] for p in portfolio) or 1
        for p in portfolio:
            p["allocation"] = round(p["allocation"] / total_alloc * 100, 1)

        return {
            "portfolio": portfolio,
            "summary": {
                "totalExpectedReturn":  round(
                    sum(p["expectedReturn"] * p["allocation"] / 100 for p in portfolio), 1
                ),
                "portfolioRiskScore":   round(
                    sum(p["riskScore"] * p["allocation"] / 100 for p in portfolio), 1
                ),
                "diversificationScore": min(10, len(portfolio)),
                "alignmentScore":       round(
                    sum(p["confidence"] * p["allocation"] / 100 for p in portfolio), 1
                ),
            },
            "insights": _generate_insights(risk_tol, goal, horizon, sectors, portfolio),
        }


# ---------------------------------------------------------------------------
# Insight generator
# ---------------------------------------------------------------------------

def _generate_insights(risk_tol, goal, horizon, sectors, portfolio) -> list:
    insights = []

    avg_risk   = sum(p["riskScore"]      for p in portfolio) / len(portfolio)
    avg_return = sum(p["expectedReturn"] for p in portfolio) / len(portfolio)

    if risk_tol == "conservative":
        insights.append(
            f"Portfolio weighted towards lower-volatility stocks (avg risk score {avg_risk:.1f}/10)."
        )
    elif risk_tol == "aggressive":
        insights.append(
            f"High-growth stocks prioritised (avg expected return {avg_return:.1f}% over {horizon})."
        )
    else:
        insights.append(
            f"Balanced portfolio targeting {avg_return:.1f}% average return over {horizon}."
        )

    if sectors:
        matched = [p["symbol"] for p in portfolio if p["sector"] in sectors]
        if matched:
            insights.append(
                f"Sector preference applied — {', '.join(matched)} align with your chosen sectors."
            )

    if goal == "income":
        insights.append("Focus on dividend-paying blue-chip stocks for regular income.")
    elif goal == "preservation":
        insights.append("Capital preservation prioritised — consider adding debt funds alongside.")
    elif goal == "retirement":
        insights.append("Long-term compounding approach suited for retirement planning.")
    elif goal == "tax-saving":
        insights.append("ELSS-eligible stocks included where possible for tax efficiency.")

    insights.append("Rebalance quarterly or when any single holding exceeds 30%.")
    return insights