const hpp = require('hpp');

/**
 * Input sanitization middleware.
 *
 * 1. Strips keys starting with '$' from req.body / req.query / req.params
 *    to prevent NoSQL-style injection (safe-guard even though Prisma + SQLite
 *    aren't vulnerable to MongoDB injection — defense-in-depth).
 *
 * 2. HPP (HTTP Parameter Pollution) — collapses duplicate query-string
 *    parameters into their last value, preventing parameter pollution attacks.
 *
 * No existing middleware or route logic is modified.
 */

// ── Recursive key-stripping ───────────────────────────────────────────────────

function stripDollarKeys(obj) {
  if (obj === null || typeof obj !== 'object') return obj;

  if (Array.isArray(obj)) {
    return obj.map(stripDollarKeys);
  }

  const cleaned = {};
  for (const [key, value] of Object.entries(obj)) {
    if (key.startsWith('$')) continue;          // drop dangerous key
    cleaned[key] = stripDollarKeys(value);       // recurse into nested objects
  }
  return cleaned;
}

// ── Express middleware ────────────────────────────────────────────────────────

function sanitizeInput(req, _res, next) {
  if (req.body  && typeof req.body  === 'object') req.body  = stripDollarKeys(req.body);
  if (req.query && typeof req.query === 'object') req.query = stripDollarKeys(req.query);
  if (req.params && typeof req.params === 'object') req.params = stripDollarKeys(req.params);
  next();
}

// ── HPP middleware (handles duplicate query params) ───────────────────────────
const hppProtection = hpp();

module.exports = { sanitizeInput, hppProtection };
