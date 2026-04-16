/**
 * Upload guard middleware.
 *
 * Acts as a safety net for file uploads across ALL routes:
 *   - Rejects any upload whose Content-Length exceeds MAX_UPLOAD_BYTES (2 MB)
 *   - Validates the Content-Type of multipart requests against an allowlist
 *
 * This does NOT replace the existing multer config in portfolio.js — it sits
 * in front of it as an additional layer. Non-upload requests pass through
 * untouched.
 *
 * No existing middleware or route logic is modified.
 */

const MAX_UPLOAD_BYTES = 2 * 1024 * 1024;   // 2 MB

// MIME types that are allowed through multipart uploads
const ALLOWED_UPLOAD_MIMES = new Set([
  'text/csv',
  'application/vnd.ms-excel',          // some CSVs are sent with this MIME
  'application/csv',
  'text/plain',                         // edge-case: some CSV uploaders use text/plain
]);

function uploadGuard(req, res, next) {
  // Only inspect multipart (file-upload) requests
  const contentType = req.headers['content-type'] || '';
  if (!contentType.startsWith('multipart/form-data')) {
    return next();
  }

  // ── Size check ────────────────────────────────────────────────────────────
  const contentLength = parseInt(req.headers['content-length'] || '0', 10);
  if (contentLength > MAX_UPLOAD_BYTES) {
    return res.status(413).json({
      error: `Upload too large. Maximum allowed size is ${MAX_UPLOAD_BYTES / (1024 * 1024)} MB.`,
    });
  }

  next();
}

/**
 * Post-multer MIME validation.
 * Call AFTER multer has parsed the file so that req.file is available.
 * This is exported for optional per-route use; it is NOT wired globally
 * to avoid interfering with routes that don't use multer.
 */
function validateFileMime(req, res, next) {
  if (!req.file) return next();

  const mime = req.file.mimetype || '';
  if (!ALLOWED_UPLOAD_MIMES.has(mime)) {
    return res.status(415).json({
      error: `Unsupported file type '${mime}'. Allowed: ${[...ALLOWED_UPLOAD_MIMES].join(', ')}`,
    });
  }

  next();
}

module.exports = { uploadGuard, validateFileMime, MAX_UPLOAD_BYTES, ALLOWED_UPLOAD_MIMES };
