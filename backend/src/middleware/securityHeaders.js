const helmet = require('helmet');

/**
 * Security headers middleware powered by Helmet.
 *
 * Sets a comprehensive suite of HTTP response headers to protect against
 * common web vulnerabilities (XSS, clickjacking, MIME sniffing, etc.).
 *
 * This is a pure additive layer — no existing middleware is modified.
 */
const securityHeaders = helmet({
  // Prevent clickjacking — deny all framing
  frameguard: { action: 'deny' },

  // Prevent MIME-type sniffing
  noSniff: true,

  // Enable HSTS (browsers will only use HTTPS after first visit)
  hsts: {
    maxAge: 31536000,        // 1 year in seconds
    includeSubDomains: true,
    preload: true,
  },

  // Content-Security-Policy — restrictive defaults
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc:  ["'self'"],
      styleSrc:   ["'self'", "'unsafe-inline'"],  // inline styles needed for some UI libs
      imgSrc:     ["'self'", 'data:'],
      connectSrc: ["'self'"],
      fontSrc:    ["'self'"],
      objectSrc:  ["'none'"],
      frameSrc:   ["'none'"],
      baseUri:    ["'self'"],
      formAction: ["'self'"],
    },
  },

  // Referrer-Policy
  referrerPolicy: { policy: 'strict-origin-when-cross-origin' },

  // X-Permitted-Cross-Domain-Policies
  crossOriginEmbedderPolicy: false,    // can break CORS — keep disabled for API servers

  // Remove X-Powered-By (also done by helmet by default)
  hidePoweredBy: true,
});

module.exports = { securityHeaders };
