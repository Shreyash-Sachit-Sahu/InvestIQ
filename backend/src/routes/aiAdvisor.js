const express = require('express');
const { requireAuth }           = require('../middleware/auth');
const { errorResponse }         = require('../utils/response');
const { getAiRecommendations }  = require('../services/mlModelService');

const router = express.Router();

// ── POST /api/ai/recommend-nse ────────────────────────────────────────────────
router.post('/recommend-nse', requireAuth, async (req, res) => {
  const preferences = req.body;
  if (!preferences || typeof preferences !== 'object') {
    return errorResponse(res, 'Missing or invalid request body.', 400);
  }

  try {
    const recs = await getAiRecommendations(preferences);
    return res.json(recs);
  } catch (err) {
    if (err.code === 'ECONNREFUSED' || err.code === 'ENOTFOUND') {
      return errorResponse(res, 'ML model service is unavailable.', 503);
    }
    if (err.message?.includes('not found') || err.message?.includes('404')) {
      return errorResponse(res, err.message, 500);
    }
    return errorResponse(res, `ML model error: ${err.message}`, 500);
  }
});

module.exports = router;