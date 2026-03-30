const axios = require('axios');
const { mlModelUrl } = require('../config');

// ── Axios client pointed at the FastAPI ML service ────────────────────────────
const mlClient = axios.create({
  baseURL: mlModelUrl,
  timeout: 120_000,          // training/inference can take a while
  headers: { 'Content-Type': 'application/json' },
});

// ── ML API wrappers ───────────────────────────────────────────────────────────

/**
 * Calls POST /recommend on the FastAPI service.
 * Throws if FastAPI is unreachable — caller receives a clean 503.
 *
 * @param {Object} preferences  — user's investment preferences
 * @returns {Promise<Object>}   — portfolio recommendation object
 */
async function getAiRecommendations(preferences) {
  const { data } = await mlClient.post('/recommend', preferences);
  return data;
}

/**
 * Calls POST /predict on the FastAPI service.
 * Returns price predictions for a single symbol.
 *
 * @param {string} symbol
 * @param {number} [days]
 * @returns {Promise<Object>}  — { symbol, predictions: number[] }
 */
async function getPricePrediction(symbol, days) {
  const payload = { symbol, ...(days != null ? { days } : {}) };
  const { data } = await mlClient.post('/predict', payload);
  return data;
}

/**
 * Calls POST /train on the FastAPI service.
 * Triggers a full model re-training run.
 *
 * @returns {Promise<Object>}  — { trained: string[], metrics: Object }
 */
async function triggerTraining() {
  const { data } = await mlClient.post('/train');
  return data;
}

/**
 * Calls GET /evaluate on the FastAPI service.
 * Returns per-symbol evaluation metrics.
 *
 * @returns {Promise<Object>}
 */
async function getEvaluation() {
  const { data } = await mlClient.get('/evaluate');
  return data;
}

/**
 * Calls GET /health on the FastAPI service.
 * Returns true if the ML service is up.
 *
 * @returns {Promise<boolean>}
 */
async function isMlServiceHealthy() {
  try {
    await mlClient.get('/health', { timeout: 5_000 });
    return true;
  } catch {
    return false;
  }
}

module.exports = {
  getAiRecommendations,
  getPricePrediction,
  triggerTraining,
  getEvaluation,
  isMlServiceHealthy,
};