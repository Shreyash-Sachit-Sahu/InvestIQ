const { errorResponse } = require('../utils/response');

/**
 * 404 handler — must be registered after all routes.
 */
function notFoundHandler(req, res) {
  return errorResponse(res, 'Not found.', 404);
}

/**
 * Global error handler — mirrors Flask's @app.errorhandler(500).
 * Express recognises a 4-arg middleware as an error handler.
 */
function errorHandler(err, req, res, _next) {  // eslint-disable-line no-unused-vars
  console.error('[InvestIQ]', err);
  const status = err.status || err.statusCode || 500;
  const msg    = status === 500 ? 'Internal server error.' : err.message;
  return errorResponse(res, msg, status);
}

module.exports = { notFoundHandler, errorHandler };