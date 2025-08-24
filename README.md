---------------------------------------
# InvestIQ — AI-Powered NSE Portfolio Recommendations

Smarter investments powered by AI. Get data-driven insights and personalized NSE portfolio recommendations to maximize your returns in the Indian stock market.

## Table of Contents

- Overview
- Features
- Architecture
- Technology Stack
- Prerequisites
- Installation & Setup
  - Backend
  - Frontend
  - Running with Docker (optional)
- Configuration
- Usage
- API Endpoints
- Data & Models
- Database Schema
- Development
- Deployment
- Monitoring & Logs
- Troubleshooting
- Security Notes
- Roadmap
- Contributing
- License

## Overview

InvestIQ is a full-stack application that generates personalized stock portfolios for Indian investors using AI and quantitative modeling. It fetches NSE stock data, scores securities, optimizes allocations with a mean-variance approach, and evaluates risk to deliver actionable insights aligned with an investor’s goal and risk tolerance.

Core value:
- Personalized portfolios in minutes
- Transparent reasoning and risk metrics
- Repeatable and extensible ML pipeline

## Features

- AI recommendations tailored to:
  - investment_amount
  - risk_tolerance (1=conservative, 2=moderate, 3=aggressive)
  - primary_goal (growth, income, balanced, preservation)
- Real-time NSE data ingestion with batching and retry resilience
- Scoring via ensemble regressors (RandomForest/GBR) + engineered factors
- Portfolio optimization using MPT (SLSQP with bounds/constraints)
- Risk assessment (risk score, diversification, VaR, Sharpe, drawdown)
- JWT-authenticated REST API
- Recommendation history with pagination
- Sensible fallbacks and defaults when live data is sparse/unavailable

## Architecture

- Frontend: React app (SPA) consuming REST APIs
- Backend: Flask app exposing auth and AI endpoints
- Services:
  - NSEDataService: loads stock universe, fetches/updates prices and fundamentals
  - StockScoringModel: feature engineering, ensemble scoring
  - PortfolioOptimizer: mean-variance weights with allocation constraints
  - RiskAssessmentModel: risk metrics, diversification, VaR, Sharpe, drawdown
  - MLService: orchestrates data → score → optimize → assess → package response
- Database: SQLAlchemy models for NSEStock, Recommendation, etc.
- Auth: JWT-based

## Technology Stack

- Backend: Python, Flask, SQLAlchemy
- ML/Analytics: scikit-learn, numpy, pandas, scipy
- Data: yfinance
- DB: PostgreSQL (prod), SQLite (dev)
- Frontend: React (Vite/CRA/Next, depending on your repo)
- Auth: flask-jwt-extended
- Deployment: Vercel (frontend), Render/Heroku/Fly.io (backend) or Docker

## Prerequisites

- Python 3.10+ recommended
- Node.js 18+ and npm/yarn (for frontend)
- PostgreSQL 13+ (or use SQLite for local dev)
- Git
- Optional: Docker & Docker Compose

## Installation & Setup

### Backend

1) Clone and enter:
- git clone <your-backend-repo>
- cd backend

2) Create venv and install deps:
- python -m venv venv
- source venv/bin/activate  (Windows: venv\Scripts\activate)
- pip install -r requirements.txt

3) Environment variables: copy .env.example to .env and set values:
- FLASK_ENV=development
- SECRET_KEY=change_me
- DATABASE_URL=postgresql://user:pass@localhost:5432/investiq
- JWT_SECRET_KEY=change_me
- YFINANCE_BASE_DELAY=2
- YFINANCE_BATCH_SIZE=12

4) Initialize DB:
- flask db upgrade
  or if using Alembic/Flask-Migrate equivalent
- If you have a seeding script: python init_data.py

5) Run backend:
- flask run
  or
- python wsgi.py / python app.py depending on your entrypoint

### Frontend

1) Clone and enter:
- git clone <your-frontend-repo>
- cd frontend

2) Install deps:
- npm install

3) Set API base URL in env (e.g., VITE_API_URL or NEXT_PUBLIC_API_URL):
- cp .env.example .env
- Update API URL to point to your backend (http://localhost:5000)

4) Start dev server:
- npm run dev (or npm start as per your setup)

### Running with Docker (optional)

Provide a docker-compose.yml like:
- services:
  - api:
    - build: ./backend
    - ports: "5000:5000"
    - env_file: backend/.env
  - db:
    - image: postgres:14
    - ports: "5432:5432"
    - environment: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
  - web:
    - build: ./frontend
    - ports: "3000:3000"
    - env_file: frontend/.env

Usage:
- docker compose up --build

## Configuration

Key backend envs:
- SECRET_KEY, JWT_SECRET_KEY
- DATABASE_URL
- YFINANCE_BASE_DELAY, YFINANCE_BATCH_SIZE, YFINANCE_MAX_RETRIES
- LOG_LEVEL=INFO|DEBUG

Frontend envs:
- API base URL variable (e.g., VITE_API_URL)

## Usage

1) Authenticate (signup/login) to obtain a JWT.
2) Call POST /api/ai/recommend-nse with:
- {
  "investment_amount": 100000,
  "risk_tolerance": 2,
  "primary_goal": "growth"
}
3) Receive recommended portfolio with risk metrics and insights.
4) View history via GET /api/ai/recommendations/history.

## API Endpoints

Auth
- POST /api/auth/signup
- POST /api/auth/login

AI
- POST /api/ai/recommend-nse  (JWT required)
  - Body:
    - investment_amount: number > 0
    - risk_tolerance: 1|2|3
    - primary_goal: growth|income|balanced|preservation
- GET /api/ai/recommendations/history (JWT)
- GET /api/ai/recommendations/<id> (JWT)

Stocks (optional public)
- GET /api/nse/stocks
- GET /api/nse/stock/<symbol>

Response shape (recommend-nse, success):
- {
  "success": true,
  "data": {
    "portfolio": [ ... ],
    "summary": {
      "totalExpectedReturn": number,
      "portfolioRiskScore": number,
      "diversificationScore": number,
      "alignmentScore": number
    },
    "insights": [string],
    "metadata": {
      "generatedAt": ISO8601,
      "modelVersion": "vX.Y.Z",
      "dataSource": "NSE",
      "processingTime": ms,
      "stocksAnalyzed": number,
      "recommendationId": number,
      "userId": "user_<id>"
    }
  }
}

## Data & Models

NSEDataService:
- Loads NSE symbols from JSON
- Fetches data via yfinance with batching & retries
- Persists to DB, converts to dicts for scoring

StockScoringModel:
- Feature engineering: PE, dividend, beta, market cap, momentum, quality/value, sector score
- Ensemble of RandomForestRegressor + GradientBoostingRegressor
- Synthetic training fallback if data sparse
- Outputs combined score and supporting fields

PortfolioOptimizer:
- Constructs covariance proxy and optimizes weights with SLSQP
- Constraints: weights sum to 1, min/max per stock
- Risk aversion adjusts by user risk_tolerance
- Produces allocation, expectedReturn, reasoning, riskScore

RiskAssessmentModel:
- Portfolio risk score (weighted), diversification (HHI + stock count), VaR, volatility, beta, Sharpe, drawdown
- Sensible defaults if portfolio empty

MLService:
- Orchestrates data retrieval → scoring → optimization → risk → response
- Provides defaults if live data unavailable

## Database Schema

- nse_stocks:
  - symbol, company_name, sector, current_price, market_cap, pe_ratio, dividend_yield, beta, last_updated
- recommendations:
  - id, user_id, preferences (JSON), recommendations (JSON), model_version, confidence_score, created_at
- users: (standard auth fields)

Migrations managed via Flask-Migrate/Alembic.

## Development

- Tests:
  - pytest
- Lint/format:
  - flake8 .
  - black .
  - isort .
- Migrations:
  - flask db migrate -m "message"
  - flask db upgrade
- Useful tips:
  - Seed DB before recommending
  - Use Postman collections for API testing
  - Enable DEBUG logs during dev

## Deployment

- Frontend: deploy to Vercel (configure API base URL env)
- Backend: deploy to Render/Heroku/Fly (set env vars, run migrations)
- Database: managed PostgreSQL (Neon, RDS, Render, etc.)
- Set LOG_LEVEL=INFO or WARNING in production

## Monitoring & Logs

- Standard Flask logging
- Add request IDs and structured JSON logs if desired
- Capture errors from yfinance (rate limiting) and database exceptions

## Troubleshooting

422 Unprocessable Entity:
- Ensure request JSON is valid:
  - investment_amount > 0 (number)
  - risk_tolerance in[1][2][3]
  - primary_goal in [growth,income,balanced,preservation]
- Confirm backend receives JSON (Content-Type: application/json)
- Verify the AI route logs show non-empty data flow:
  - fetched stock count
  - scored count
  - portfolio length
- If needed, log the exact value/type returned from generate_ai_recommendations

Empty/Small Portfolio:
- Seed or update stock DB (init_data/update jobs)
- Review filters in scoring; relax thresholds if overly aggressive
- Ensure optimizer bounds are not too tight given top_stocks count

yfinance Rate Limits:
- Increase base delays and batch sleeps
- Reduce batch size temporarily
- Retry with exponential backoff already in place

Auth Issues:
- JWT secrets must be set
- Token expiry and clock skew considerations

## Security Notes

- Keep SECRET_KEY and JWT_SECRET_KEY secure
- Never log sensitive tokens
- Use HTTPS in production
- Validate and sanitize all inputs at API boundary

## Roadmap

- Historical backtesting and scenario analysis
- Sector/thematic overlays and constraints
- Rebalancing suggestions and alerts
- Export to CSV/PDF
- Advanced factor models and explainability

## Contributing

1) Fork the repo
2) Create a feature branch
3) Write tests and run lint/format
4) Submit a PR with context and screenshots where helpful

## License

MIT License. See LICENSE for details.
---------------------------------------
