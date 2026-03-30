# InvestIQ — AI-Powered NSE Portfolio Advisor

> A full-stack investment intelligence platform combining deep learning price forecasting with preference-aware portfolio recommendation for the Indian stock market.

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [ML Pipeline](#ml-pipeline)
   - [Feature Engineering](#feature-engineering)
   - [LSTM Forecasting Model](#lstm-forecasting-model)
   - [Portfolio Recommender](#portfolio-recommender)
   - [Training Pipeline](#training-pipeline)
   - [Evaluation](#evaluation)
4. [Backend API](#backend-api)
5. [Frontend](#frontend)
6. [Database Design](#database-design)
7. [Project Structure](#project-structure)
8. [Getting Started](#getting-started)
9. [Configuration](#configuration)
10. [Known Limitations](#known-limitations)

---

## Overview

InvestIQ is a research-grade investment advisory system built for the National Stock Exchange (NSE) of India. It combines two independent machine learning systems:

- **Price Forecasting** — A 3-branch hybrid deep learning model (CNN + Bidirectional LSTM + Transformer) that generates 30-day ahead Close price predictions for 29 NSE large-cap stocks, trained on 5 years of daily OHLCV data enriched with 22 technical indicators.

- **Portfolio Recommendation** — A neural network that scores every available stock against a specific user's financial preferences, producing a ranked, allocation-weighted portfolio. The model is trained on a synthetic database of ~65,000 user profiles, with each (user, stock) pair labelled by a user-aware utility score derived from Sharpe ratio, volatility penalty, and goal-specific weightings.

The two models are served together through a FastAPI backend and consumed by a Next.js 14 frontend with JWT-based authentication.

---

## System Architecture

```
┌─────────────────────────────────────────────────┐
│                  Next.js Frontend                │
│  (App Router · Tailwind · shadcn/ui · Framer)   │
│                                                  │
│   /             Home landing page                │
│   /ai-advisor   Portfolio recommendation UI      │
│   /login        JWT auth (localStorage tokens)  │
│   /signup       User registration                │
└────────────────────┬────────────────────────────┘
                     │ HTTP (Bearer JWT)
                     ▼
┌─────────────────────────────────────────────────┐
│             Express / Next.js Auth API           │
│         (handles /api/auth/* routes)             │
│  Issues access_token + refresh_token on login   │
└────────────────────┬────────────────────────────┘
                     │ Internal HTTP
                     ▼
┌─────────────────────────────────────────────────┐
│              FastAPI ML API  :8000               │
│                                                  │
│  POST /train       Train LSTM + Recommender      │
│  POST /predict     30-day price forecast         │
│  POST /recommend   Portfolio recommendation      │
│  GET  /evaluate    Evaluation report             │
│  GET  /health      Liveness check                │
└──────┬──────────────────────┬───────────────────┘
       │                      │
       ▼                      ▼
┌─────────────┐     ┌─────────────────────────────┐
│ Yahoo Finance│     │  SQLite / Postgres DB        │
│ (yfinance)  │     │  synthetic_profiles table    │
│ 5y OHLCV    │     │  ~65,000 rows                │
└─────────────┘     └─────────────────────────────┘
```

---

## ML Pipeline

### Feature Engineering

Raw OHLCV data from Yahoo Finance (`{SYMBOL}.NS`, 5-year window) is processed through `StockDataCollector.compute_features()` into a 22-feature matrix before any model sees it.

| Category | Features |
|---|---|
| Price returns | `Return` (daily pct change) |
| Moving averages | `SMA10`, `SMA20`, `SMA50`, `EMA10`, `EMA20` |
| Volatility | `Volatility10`, `Volatility20` (rolling std of returns) |
| Volume | `VolumeChange`, `OBV` (On-Balance Volume) |
| Momentum | `RSI14`, `Momentum5`, `Momentum10`, `Momentum20` |
| MACD | `MACD`, `Signal`, `MACD_Hist` |
| Bollinger Bands | `BB_upper`, `BB_lower`, `BB_width`, `BB_pos` |

All features are computed causally (no look-ahead bias). `inf` and `NaN` values are replaced with `pd.NA` and rows containing them are dropped. A per-stock `MinMaxScaler` is fit on the full feature matrix and saved to disk — both model training and inference use the same scaler instance to guarantee consistent normalisation.

---

### LSTM Forecasting Model

The core forecasting model is a 3-branch hybrid architecture defined in `LSTMModelTrainer.build_model()`. A separate model instance is trained per stock symbol.

#### Input / Output

- **Input shape:** `(120, 22)` — 120-day lookback window × 22 features
- **Output shape:** `(30,)` — next 30 days of normalised Close prices
- **Loss function:** Huber loss (robust to price outliers vs. MSE)
- **Optimiser:** Adam with gradient clipping (`clipnorm=1.0`), initial LR `1e-3`

#### Branch A — Causal CNN Feature Extractor

```
Conv1D(32,  kernel=3, padding='causal') → BN → ReLU
Conv1D(64,  kernel=3, padding='causal') → BN → ReLU
Conv1D(128, kernel=3, padding='causal') → BN → ReLU → Dropout(0.2)
GlobalAveragePooling1D()
→ output: (batch, 128)
```

Causal padding ensures no future timesteps leak into the convolution. Three stacked layers progressively extract local price patterns at increasing receptive fields (3, 6, 9 days).

#### Branch B — Stacked Bidirectional LSTM with Custom Attention

Three residual BiLSTM blocks, each augmented with a custom `ChannelAttention` layer (Squeeze-and-Excitation style):

```
Block 1:  BiLSTM(64) → ChannelAttention → LayerNorm → Dropout(0.3)
          + Conv1D(128, 1×1) residual projection from input
Block 2:  BiLSTM(64) → ChannelAttention → LayerNorm → Dropout(0.2)
          + direct residual (same shape)
Block 3:  BiLSTM(32) → ChannelAttention → LayerNorm → Dropout(0.15)
          + Conv1D(64, 1×1) residual projection
→ TemporalAttention(64)   # soft attention over 120 timesteps
→ output: (batch, 64)
```

**TemporalAttention** learns a scalar importance weight per timestep via a two-layer MLP (`tanh` activation + linear projection), then returns a weighted sum of hidden states. This allows the model to down-weight noisy intermediate timesteps and focus on high-signal periods (e.g. earnings windows, trend reversals).

**ChannelAttention** applies global average pooling across the time axis, passes the result through a bottleneck FC stack (reduction ratio 4), and multiplies the sigmoid-activated output back into the feature map channel-wise. This is functionally equivalent to SE-Net applied to temporal feature maps.

#### Branch C — Multi-Head Self-Attention (Transformer Block)

```
MultiHeadAttention(num_heads=4, key_dim=16, dropout=0.1)(inputs, inputs)
Add([inputs, attn]) → LayerNorm
GlobalAveragePooling1D()
→ output: (batch, 22)
```

A single transformer encoder block over the raw 22-feature input sequence. With `key_dim=16` and 4 heads, the total attention dimension is 64. This branch captures non-local dependencies the LSTM may miss — e.g. correlating RSI levels 60 days ago with current Bollinger Band position.

#### Merge and Dense Head

All three branch outputs are concatenated: `(128 + 64 + 22) = 214` features.

```
Dense(256) → LayerNorm → ReLU → Dropout(0.3)
Dense(128) → LayerNorm → ReLU → Dropout(0.2)  + skip connection Dense(128) from previous
Dense(64)  → ReLU → Dropout(0.1)
Dense(32)  → ReLU
Dense(30)  → linear activation (output layer)
```

The skip connection in the dense head reduces vanishing gradient risk and allows the network to preserve coarse-grained representations from layer 1 while layer 2 refines them.

#### Training Protocol

| Hyperparameter | Value |
|---|---|
| Lookback window | 120 days |
| Prediction horizon | 30 days |
| Epochs (max) | 55 |
| Batch size | 16 |
| Train / val split | 80 / 20 (temporal, no shuffle) |
| Early stopping patience | 20 epochs |
| LR reduction factor | 0.5, patience 8, min LR `1e-6` |
| L2 regularisation | `1e-4` on all LSTM and Conv kernels |

---

### Portfolio Recommender

The recommender is a preference-conditioned scoring network. Given a user's financial profile and a candidate stock's historical return statistics, it outputs a scalar utility score. At inference time all 29 stocks are scored and the top-N are ranked and allocated.

#### Feature Vector (22 dimensions per sample)

The input to the recommender is the concatenation of a **user vector** (20 features) and **stock statistics** (2 features):

**User vector (20 features):**

| Type | Features | Encoding |
|---|---|---|
| Categorical (5) | `riskTolerance`, `investmentHorizon`, `primaryGoal`, `hasEmergencyFund`, `investmentExperience` | `LabelEncoder` per field, pre-fit on full vocabulary |
| Sector OHE (12) | One binary column per sector in `ALL_SECTORS` | One-hot, fixed column order |
| Numeric (3) | `investmentAmount`, `age`, `currentIncome` | `StandardScaler` fit on training profiles |

**Stock statistics (2 features):**
- `mean_ret` — mean daily return over the 5-year window
- `std_ret` — standard deviation of daily returns (+ `1e-9` for numerical stability)

#### Utility Score Label

Rather than using a single objective (e.g. mean return) as the training label, each (user, stock) pair receives a **user-aware utility score**:

```
ann_return = mean_ret × 252
ann_vol    = std_ret  × √252
sharpe     = ann_return / (ann_vol + ε)

penalty    = RISK_PENALTY[risk_tolerance] × ann_vol
score      = ret_weight × sharpe − stab_weight × penalty

if stock_sector ∈ preferred_sectors:
    score × = 1.20
```

Where `RISK_PENALTY` ∈ `{conservative: 3.0, moderate: 1.5, aggressive: 0.5}` and `(ret_weight, stab_weight)` are drawn from `GOAL_WEIGHTS` keyed by `primaryGoal`. This formulation means the same stock will receive a high score for an aggressive growth investor and a low score for a conservative preservation investor, forcing the model to genuinely learn preference-conditional behaviour rather than ranking stocks by raw return.

#### Network Architecture

```
Input(22) → Dense(256) → BN → Dropout(0.3)
          → Dense(128) → BN → Dropout(0.2)
          → Dense(64)        → Dropout(0.1)
          → Dense(1, linear)
```

- **Loss:** MSE on the utility score
- **Optimiser:** Adam
- **Early stopping:** patience 8, monitoring `val_loss`
- **Epochs (max):** 40, batch size 16

#### Synthetic Training Database

The recommender is trained on a synthetic profile database generated by `seed_database.py`. Profiles are the Cartesian product of all discrete preference field values crossed with sampled numeric ranges:

| Field | Values |
|---|---|
| `riskTolerance` | conservative, moderate, aggressive |
| `investmentHorizon` | 5 options |
| `primaryGoal` | 6 options |
| `hasEmergencyFund` | yes, no |
| `investmentExperience` | beginner, intermediate, advanced, expert |
| `investmentAmount` | ₹75K, ₹175K, ₹375K, ₹750K, ₹1.75M, ₹2.5M |
| `age` | 22, 30, 40, 50, 60, 65 |
| `currentIncome` | ₹400K, ₹750K, ₹1.2M, ₹2M, ₹2.5M |

Default seeding (without `FULL_SECTOR_SWEEP=1`) produces ~64,800 profiles by cycling through sector combinations rather than full enumeration, keeping insertion time under a minute. With `FULL_SECTOR_SWEEP=1` the full combinatorial expansion produces ~5M rows.

#### Inference

At `/recommend` time:
1. The user's preferences are encoded using the saved `LabelEncoder` instances and `StandardScaler`.
2. For each stock in `stock_data`, `[mean_ret, std_ret]` are appended to the user vector.
3. The model scores all 29 candidate vectors.
4. Scores are ranked; the top `max_portfolio_stocks` (default 10) are selected.
5. Allocations are computed proportionally to shifted scores (floored at 1%), then normalised to sum to 100%.
6. `expectedReturn` and `riskScore` are derived from real annualised statistics, not raw model output — the model score is used only for ranking and allocation weight.

---

### Training Pipeline

`main.py` orchestrates the full pipeline in order:

```
seed_database.py          # one-time: populate investiq_profiles.db
    ↓
StockDataCollector        # fetch 5y OHLCV for 29 NSE symbols via yfinance
    ↓
LSTMModelTrainer          # train one model per symbol → save .keras + scaler .pkl
    ↓
PortfolioRecommender      # load profiles from DB → build (user, stock) pairs
                          # → train scorer → save model + encoders + scaler
    ↓
run_evaluation()          # load saved models → compute MSE/MAE/RMSE/R² per symbol
```

All artifacts are written to `models/`, `scalers/`, and `logs/` directories. The same pipeline can be triggered via `POST /train` on the running API server.

---

### Evaluation

`evaluate.py` computes four metrics per stock using the held-out validation split:

| Metric | Description |
|---|---|
| MSE | Mean Squared Error on rupee-scale Close prices |
| MAE | Mean Absolute Error |
| RMSE | Root Mean Squared Error |
| R² | Coefficient of determination (1.0 = perfect) |

Predictions are inverse-transformed from normalised space back to rupee prices before metric computation, using the per-stock `MinMaxScaler`. Reports are saved as JSON to `logs/{SYMBOL}_evaluation.json`.

---

## Backend API

The ML API is a FastAPI application served via Uvicorn on port `8000`.

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Liveness check |
| `/train` | POST | Fetch data, train all LSTM models, train recommender |
| `/predict` | POST | 30-day price forecast for a given symbol |
| `/recommend` | POST | Portfolio recommendation for a given user profile |
| `/evaluate` | GET | Run evaluation across all trained models |

### `POST /predict` — Request

```json
{
  "symbol": "RELIANCE",
  "days": 30
}
```

### `POST /recommend` — Request

```json
{
  "riskTolerance": "moderate",
  "investmentHorizon": "5-10 years",
  "primaryGoal": "growth",
  "hasEmergencyFund": "yes",
  "investmentExperience": "intermediate",
  "sectors": ["IT", "Finance"],
  "investmentAmount": 500000,
  "age": 32,
  "currentIncome": 1200000
}
```

### `POST /recommend` — Response (abbreviated)

```json
{
  "portfolio": [
    {
      "symbol": "TCS",
      "name": "TCS Ltd.",
      "allocation": 18.4,
      "confidence": 87.2,
      "reasoning": "Matches your preferred IT sector; moderate risk profile match",
      "sector": "IT",
      "expectedReturn": 34.1,
      "riskScore": 4.2
    }
  ],
  "summary": {
    "totalExpectedReturn": 28.6,
    "portfolioRiskScore": 5.1,
    "diversificationScore": 9,
    "alignmentScore": 81.3
  },
  "insights": [...]
}
```

---

## Frontend

Built with Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui, and Framer Motion.

| Route | Description |
|---|---|
| `/` | Landing page with feature overview |
| `/ai-advisor` | Main recommendation interface |
| `/login` | JWT login — stores `access_token` + `refresh_token` in localStorage |
| `/signup` | User registration |
| `/about` | Project information |

**Auth flow:** On successful login, `window.dispatchEvent(new Event("auth-change"))` is fired. The Navbar subscribes to this event via `addEventListener` in a `useEffect`, allowing it to swap Login/Signup links for a Sign Out button without a page reload or global state manager.

**Unauthenticated access:** Submitting the AI Advisor form without a token triggers a centred modal (rendered outside the page's motion container to avoid CSS `transform` conflicts) with Sign In and Create Account CTAs.

---

## Database Design

### `synthetic_profiles` table

```sql
CREATE TABLE synthetic_profiles (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    riskTolerance        TEXT    NOT NULL,
    investmentHorizon    TEXT    NOT NULL,
    primaryGoal          TEXT    NOT NULL,
    hasEmergencyFund     TEXT    NOT NULL,
    investmentExperience TEXT    NOT NULL,
    sectors              TEXT    NOT NULL,  -- JSON array
    investmentAmount     REAL    NOT NULL,
    age                  INTEGER NOT NULL,
    currentIncome        REAL    NOT NULL,
    created_at           TEXT    NOT NULL,
    version              INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX idx_risk ON synthetic_profiles (riskTolerance);
```

`sectors` is stored as a JSON-serialised list and deserialised at load time. The schema supports both SQLite (default, zero-config) and Postgres (set `DATABASE_URL` environment variable).

---

## Project Structure

```
InvestIQ/
├── MLmodel/
│   ├── api.py                  # FastAPI application
│   ├── config.py               # Hyperparameters and paths
│   ├── data_collector.py       # yfinance fetcher + feature engineering
│   ├── lstm_model.py           # 3-branch hybrid model + custom layers
│   ├── portfolio_recommender.py# Preference-conditioned scorer
│   ├── evaluate.py             # Metric computation
│   ├── main.py                 # CLI pipeline entry point
│   ├── seed_database.py        # Synthetic profile DB generator
│   ├── requirements.txt
│   ├── models/                 # Saved .keras model files (gitignored)
│   ├── scalers/                # Saved MinMaxScaler .pkl files (gitignored)
│   ├── data/
│   │   ├── raw/
│   │   └── processed/          # Per-symbol feature CSVs (gitignored)
│   └── logs/                   # Evaluation JSON reports (gitignored)
│
├── app/                        # Next.js App Router
│   ├── layout.tsx
│   ├── page.tsx                # Home
│   ├── ai-advisor/page.tsx
│   ├── login/page.tsx
│   ├── signup/page.tsx
│   └── globals.css
│
├── components/
│   ├── Navbar.tsx              # Auth-aware navigation
│   ├── AIAdvisorForm.tsx
│   ├── AIRecommendations.tsx
│   └── ui/                    # shadcn/ui components
│
├── lib/
│   └── api.ts                  # API_BASE_URL export
│
├── .env.local                  # NEXT_PUBLIC_API_BASE_URL
├── .gitignore
├── components.json             # shadcn/ui config
├── tailwind.config.ts
└── tsconfig.json
```

---

## Getting Started

### Prerequisites

- Python 3.11+ with pip
- Node.js 18+
- (Optional) Postgres if not using SQLite

### ML API

```powershell
cd InvestIQ/MLmodel

# Create and activate virtual environment
python -m venv venv313
.\venv313\Scripts\Activate.ps1      # Windows
# source venv313/bin/activate       # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Seed the synthetic profiles database (run once)
python seed_database.py

# Start the API server
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

Trigger model training via the API:

```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/train"
```

Or run the full offline pipeline directly:

```powershell
python main.py
```

### Frontend

```bash
cd InvestIQ
npm install
cp .env.local.example .env.local   # set NEXT_PUBLIC_API_BASE_URL
npm run dev
```

### Full re-seed (optional)

To generate the full ~5M profile dataset instead of the default ~65K:

```powershell
$env:FULL_SECTOR_SWEEP="1"
python seed_database.py --force
```

---

## Configuration

All ML hyperparameters are centralised in `config.py`:

| Parameter | Default | Description |
|---|---|---|
| `data_period` | `5y` | yfinance historical window |
| `lookback_window` | `120` | LSTM input sequence length (days) |
| `prediction_days` | `30` | Forecast horizon (days) |
| `train_ratio` | `0.8` | Temporal train/val split |
| `epochs` | `55` | Max LSTM training epochs |
| `batch_size` | `16` | LSTM batch size |
| `early_stopping_patience` | `20` | Epochs without improvement before stop |
| `lr_patience` | `8` | Epochs before LR reduction |
| `recommender_epochs` | `40` | Max recommender training epochs |
| `recommender_batch_size` | `16` | Recommender batch size |
| `risk_free_rate` | `0.05` | Used in Sharpe-based utility scoring |
| `max_portfolio_stocks` | `10` | Maximum stocks in a recommendation |

---

## Known Limitations

- **CPU-only training on Windows** — TensorFlow ≥ 2.11 dropped native GPU support on Windows. Use WSL2 or the TensorFlow-DirectML plugin for GPU acceleration.
- **HDFC.NS delisted** — Yahoo Finance no longer carries this ticker. It is silently skipped; the remaining 28 symbols train normally.
- **No real-time data** — Predictions are based on the last available closing price at fetch time. The API does not stream live tick data.
- **Synthetic recommender training data** — The recommender is trained entirely on programmatically generated profiles. Performance on real user cohorts may differ and would benefit from fine-tuning on actual interaction data.
- **Single-step inverse transform** — Close price inverse transformation reconstructs only the Close column from the full feature scaler. Predictions for other features are not recovered.
- **No confidence intervals** — The model outputs point forecasts. Uncertainty quantification (e.g. Monte Carlo Dropout, conformal prediction) is not yet implemented.
