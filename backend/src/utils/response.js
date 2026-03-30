/**
 * Sends a standardised error JSON response.
 * Mirrors Flask's error_response() in utils.py.
 */
function errorResponse(res, message, statusCode = 400, errors = null) {
  const body = { error: message };
  if (errors) body.errors = errors;
  return res.status(statusCode).json(body);
}

module.exports = { errorResponse };