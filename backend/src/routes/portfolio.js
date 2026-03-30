const express = require('express');
const multer  = require('multer');

const { requireAuth }   = require('../middleware/auth');
const { errorResponse } = require('../utils/response');
const { parsePortfolioCsv } = require('../services/csvParser');

const router  = express.Router();
const upload  = multer({ storage: multer.memoryStorage() });  // keep CSV in RAM

// ── Helpers ───────────────────────────────────────────────────────────────────

/**
 * Returns (or lazily creates) the user's Default Portfolio.
 * Mirrors get_default_portfolio() in portfolio.py.
 */
async function getDefaultPortfolio(prisma, userId) {
  let portfolio = await prisma.portfolio.findFirst({
    where: { userId, name: 'Default Portfolio' },
  });
  if (!portfolio) {
    portfolio = await prisma.portfolio.create({
      data: { userId, name: 'Default Portfolio' },
    });
  }
  return portfolio;
}

// ── POST /api/portfolio/upload-csv ────────────────────────────────────────────
router.post('/upload-csv', requireAuth, upload.single('portfolio_csv'), async (req, res) => {
  if (!req.file) {
    return errorResponse(res, "No CSV file uploaded as 'portfolio_csv'.", 400);
  }
  if (!req.file.originalname.endsWith('.csv')) {
    return errorResponse(res, 'File must be a CSV.', 400);
  }

  const prisma = req.prisma;
  const { rows, errors: parseErrors } = await parsePortfolioCsv(req.file.buffer);

  if (rows === null) {
    return errorResponse(res, 'CSV parse error.', 400, parseErrors);
  }

  const portfolio = await getDefaultPortfolio(prisma, req.userId);
  let imported = 0;
  const rowErrors = [];

  for (const row of rows) {
    const { symbol, quantity, averageBuyPrice, purchaseDate } = row;

    if (!symbol || quantity <= 0 || averageBuyPrice <= 0) {
      rowErrors.push(`Invalid row: ${JSON.stringify(row)}`);
      continue;
    }

    try {
      const existing = await prisma.holding.findUnique({
        where: { portfolioId_symbol: { portfolioId: portfolio.id, symbol } },
      });

      if (existing) {
        const totalQty = existing.quantity + quantity;
        const newAvg   = totalQty > 0
          ? (existing.averageBuyPrice * existing.quantity + averageBuyPrice * quantity) / totalQty
          : averageBuyPrice;
        await prisma.holding.update({
          where: { id: existing.id },
          data: {
            quantity:       totalQty,
            averageBuyPrice: newAvg,
            ...(purchaseDate ? { purchaseDate } : {}),
          },
        });
      } else {
        await prisma.holding.create({
          data: { portfolioId: portfolio.id, symbol, quantity, averageBuyPrice,
                  purchaseDate: purchaseDate || null },
        });
      }
      imported++;
    } catch (err) {
      rowErrors.push(`${symbol}: ${err.message}`);
    }
  }

  return res.json({
    message: 'Portfolio uploaded successfully.',
    imported_holdings_count: imported,
    errors: [...parseErrors, ...rowErrors],
  });
});

// ── GET /api/portfolio/ ───────────────────────────────────────────────────────
router.get('/', requireAuth, async (req, res) => {
  const prisma    = req.prisma;
  const user      = await prisma.user.findUnique({ where: { id: req.userId } });
  if (!user) return errorResponse(res, 'User not found.', 404);

  const portfolio = await getDefaultPortfolio(prisma, req.userId);
  const holdings  = await prisma.holding.findMany({ where: { portfolioId: portfolio.id } });

  // NOTE: currentPrice and predictedPrice will be enriched by
  // calling GET /api/nse/stock/:symbol and POST /predict on the ML service.
  // Placeholder multipliers match the original Flask behaviour.
  const enriched = holdings.map(h => ({
    symbol:          h.symbol,
    quantity:        h.quantity,
    average_buy_price: h.averageBuyPrice,
    purchase_date:   h.purchaseDate,
    currentPrice:    parseFloat((h.averageBuyPrice * 1.05).toFixed(2)),
    predictedPrice:  parseFloat((h.averageBuyPrice * 1.10).toFixed(2)),
    change:          5.0,
    name:            `${h.symbol} Ltd.`,
  }));

  return res.json(enriched);
});

module.exports = router;