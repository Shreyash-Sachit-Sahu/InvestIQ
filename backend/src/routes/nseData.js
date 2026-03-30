const express = require('express');
const { requireAuth }   = require('../middleware/auth');
const { errorResponse } = require('../utils/response');

const router = express.Router();

// ── Static mock data (mirrors MOCK_STOCKS in nse_data.py) ────────────────────
// TODO: Replace with live yfinance calls via the ML service's /predict endpoint
// or a dedicated Node yfinance wrapper.
const MOCK_STOCKS = {
  RELIANCE:   { name: 'Reliance Industries',          sector: 'Oil & Gas',               currentPrice: 2600 },
  TCS:        { name: 'Tata Consultancy Services',     sector: 'IT',                      currentPrice: 3700 },
  HDFCBANK:   { name: 'HDFC Bank',                    sector: 'Banking',                 currentPrice: 1620 },
  ICICIBANK:  { name: 'ICICI Bank',                   sector: 'Banking',                 currentPrice: 1100 },
  INFY:       { name: 'Infosys',                      sector: 'IT',                      currentPrice: 1450 },
  KOTAKBANK:  { name: 'Kotak Mahindra Bank',          sector: 'Banking',                 currentPrice: 1760 },
  AXISBANK:   { name: 'Axis Bank',                    sector: 'Banking',                 currentPrice: 1065 },
  SBIN:       { name: 'State Bank of India',          sector: 'Banking',                 currentPrice: 770  },
  LT:         { name: 'Larsen & Toubro',              sector: 'Infrastructure',          currentPrice: 3480 },
  ITC:        { name: 'ITC Ltd.',                     sector: 'FMCG',                    currentPrice: 425  },
  BAJFINANCE: { name: 'Bajaj Finance',                sector: 'Finance',                 currentPrice: 7100 },
  BHARTIARTL: { name: 'Bharti Airtel',                sector: 'Telecom',                 currentPrice: 1680 },
  HINDUNILVR: { name: 'Hindustan Unilever',           sector: 'FMCG',                    currentPrice: 2290 },
  ONGC:       { name: 'Oil & Natural Gas Corp',       sector: 'Oil & Gas',               currentPrice: 263  },
  MARUTI:     { name: 'Maruti Suzuki India',          sector: 'Automobiles',             currentPrice: 11500},
  TITAN:      { name: 'Titan Company',                sector: 'Consumer Goods',          currentPrice: 3300 },
  ULTRACEMCO: { name: 'UltraTech Cement',             sector: 'Cement',                  currentPrice: 10800},
  NESTLEIND:  { name: 'Nestle India',                 sector: 'FMCG',                    currentPrice: 2280 },
  ASIANPAINT: { name: 'Asian Paints',                 sector: 'Paints',                  currentPrice: 2420 },
  DIVISLAB:   { name: "Divi's Laboratories",          sector: 'Pharmaceuticals',         currentPrice: 5700 },
  TECHM:      { name: 'Tech Mahindra',                sector: 'IT',                      currentPrice: 1510 },
  EICHERMOT:  { name: 'Eicher Motors',                sector: 'Automobiles',             currentPrice: 4770 },
  JSWSTEEL:   { name: 'JSW Steel',                    sector: 'Metals',                  currentPrice: 870  },
  TATASTEEL:  { name: 'Tata Steel',                   sector: 'Metals',                  currentPrice: 142  },
  WIPRO:      { name: 'Wipro',                        sector: 'IT',                      currentPrice: 462  },
  'M&M':      { name: 'Mahindra & Mahindra',          sector: 'Automobiles',             currentPrice: 2850 },
  ADANIPORTS: { name: 'Adani Ports & SEZ',            sector: 'Infrastructure',          currentPrice: 1320 },
  DRREDDY:    { name: "Dr. Reddy's Laboratories",     sector: 'Pharmaceuticals',         currentPrice: 1260 },
};

// ── GET /api/nse/stock/:symbol ────────────────────────────────────────────────
router.get('/stock/:symbol', requireAuth, (req, res) => {
  const symbol = req.params.symbol.toUpperCase();
  const stock  = MOCK_STOCKS[symbol];
  if (!stock) return errorResponse(res, `Symbol '${symbol}' not found.`, 404);

  return res.json({ symbol, ...stock });
});

// ── GET /api/nse/historical/:symbol ──────────────────────────────────────────
router.get('/historical/:symbol', requireAuth, (req, res) => {
  const symbol = req.params.symbol.toUpperCase();
  const stock  = MOCK_STOCKS[symbol];
  if (!stock) return errorResponse(res, `Symbol '${symbol}' not found.`, 404);

  const today  = new Date();
  const labels = [];
  for (let i = 364; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    labels.push(d.toISOString().slice(0, 10));
  }

  const base     = stock.currentPrice;
  const datasets = [{
    label: symbol,
    data: labels.map(() => parseFloat((base * (0.9 + Math.random() * 0.2)).toFixed(2))),
  }];

  return res.json({ labels, datasets });
});

module.exports = router;