const morgan = require('morgan');

/**
 * HTTP request logger middleware.
 *
 * - Uses 'combined' format in production (Apache-style, good for log aggregation)
 * - Uses 'dev' format in development (concise, coloured)
 * - Registers a custom token ':redacted-auth' that masks the Authorization
 *   header value so tokens are never written to logs.
 *
 * No existing middleware or route logic is modified.
 */

// ── Custom token: redacted Authorization header ───────────────────────────────
morgan.token('redacted-auth', (req) => {
  const header = req.headers['authorization'];
  if (!header) return '-';
  if (header.startsWith('Bearer ')) return 'Bearer ***';
  return '***';
});

// ── Build the middleware ──────────────────────────────────────────────────────
const isProduction = process.env.NODE_ENV === 'production';

const requestLogger = morgan(
  isProduction
    ? ':remote-addr - :remote-user [:date[clf]] ":method :url HTTP/:http-version" :status :res[content-length] ":referrer" ":user-agent" auth=:redacted-auth'
    : 'dev'
);

module.exports = { requestLogger };
