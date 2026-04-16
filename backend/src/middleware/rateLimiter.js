const rateLimit = require('express-rate-limit');

/**
 * Rate-limiting middleware to protect against brute-force and DDoS attacks.
 *
 * Two limiters are exported:
 *   1. globalLimiter — applied to ALL routes (generous ceiling)
 *   2. authLimiter   — applied only to /api/auth/* (tight ceiling)
 *
 * Both return a standardised JSON error response on limit breach.
 */

// ── Shared response formatter ─────────────────────────────────────────────────
const limitHandler = (_req, res) => {
  return res.status(429).json({
    error: 'Too many requests. Please try again later.',
  });
};

// ── Global limiter ────────────────────────────────────────────────────────────
const globalLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,   // 15 minutes
  max: 100,                    // 100 requests per window per IP
  standardHeaders: true,       // Return RateLimit-* headers
  legacyHeaders: false,        // Disable X-RateLimit-* headers
  handler: limitHandler,
  message: { error: 'Too many requests. Please try again later.' },
});

// ── Auth-specific limiter (login / register / refresh) ────────────────────────
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,   // 15 minutes
  max: 15,                     // 15 requests per window per IP
  standardHeaders: true,
  legacyHeaders: false,
  handler: limitHandler,
  message: { error: 'Too many authentication attempts. Please try again later.' },
});

module.exports = { globalLimiter, authLimiter };
