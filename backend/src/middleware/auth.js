const jwt = require('jsonwebtoken');
const { jwtAccessSecret, jwtRefreshSecret } = require('../config');
const { errorResponse } = require('../utils/response');

/**
 * Protects routes — mirrors Flask's @jwt_required().
 * Expects: Authorization: Bearer <access_token>
 * On success sets req.userId = <user id from token>.
 */
function requireAuth(req, res, next) {
  const header = req.headers['authorization'] || '';
  const token  = header.startsWith('Bearer ') ? header.slice(7) : null;

  if (!token) return errorResponse(res, 'Unauthorized.', 401);

  try {
    const payload = jwt.verify(token, jwtAccessSecret);
    req.userId = payload.sub;            // sub = user id (set in auth route)
    next();
  } catch (err) {
    return errorResponse(res, 'Unauthorized.', 401);
  }
}

/**
 * Protects the refresh endpoint — mirrors @jwt_required(refresh=True).
 * Expects: Authorization: Bearer <refresh_token>
 * On success sets req.userId.
 */
function requireRefresh(req, res, next) {
  const header = req.headers['authorization'] || '';
  const token  = header.startsWith('Bearer ') ? header.slice(7) : null;

  if (!token) return errorResponse(res, 'Unauthorized.', 401);

  try {
    const payload = jwt.verify(token, jwtRefreshSecret);
    req.userId = payload.sub;
    next();
  } catch (err) {
    return errorResponse(res, 'Unauthorized.', 401);
  }
}

module.exports = { requireAuth, requireRefresh };