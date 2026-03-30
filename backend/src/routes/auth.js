const express = require('express');
const bcrypt  = require('bcrypt');
const jwt     = require('jsonwebtoken');
const { body, validationResult } = require('express-validator');

const { jwtAccessSecret, jwtRefreshSecret,
        jwtAccessExpiresIn, jwtRefreshExpiresIn } = require('../config');
const { requireRefresh } = require('../middleware/auth');
const { errorResponse }  = require('../utils/response');

const router = express.Router();

// ── Helpers ───────────────────────────────────────────────────────────────────

const EMAIL_RE    = /^[\w.-]+@[\w.-]+\.\w+$/;
const PASSWORD_RE = /^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*\W).{8,}$/;

function makeAccessToken(userId) {
  return jwt.sign({ sub: userId }, jwtAccessSecret, { expiresIn: jwtAccessExpiresIn });
}

function makeRefreshToken(userId) {
  return jwt.sign({ sub: userId }, jwtRefreshSecret, { expiresIn: jwtRefreshExpiresIn });
}

// ── POST /api/auth/register ───────────────────────────────────────────────────
router.post('/register',
  body('email').custom(v => EMAIL_RE.test(v)).withMessage('Invalid or missing email.'),
  body('password').custom(v => PASSWORD_RE.test(v))
    .withMessage('Password must be 8+ chars with upper, lower, digit, special.'),

  async (req, res) => {
    const errs = validationResult(req);
    if (!errs.isEmpty()) {
      return errorResponse(res, errs.array()[0].msg, 400);
    }

    const { email, password } = req.body;
    const prisma = req.prisma;

    try {
      const existing = await prisma.user.findUnique({ where: { email } });
      if (existing) return errorResponse(res, 'User with this email already exists.', 409);

      const passwordHash = await bcrypt.hash(password, 12);
      await prisma.user.create({ data: { email, passwordHash } });
      return res.status(201).json({ message: 'Registered successfully.' });
    } catch (err) {
      console.error('[auth/register]', err);
      return errorResponse(res, 'Internal server error.', 500);
    }
  }
);

// ── POST /api/auth/login ──────────────────────────────────────────────────────
router.post('/login', async (req, res) => {
  const { email, password } = req.body || {};
  if (!email || !password) return errorResponse(res, 'Missing JSON payload.', 400);

  const prisma = req.prisma;
  try {
    const user = await prisma.user.findUnique({ where: { email } });
    if (!user) return errorResponse(res, 'Invalid email or password.', 401);

    const match = await bcrypt.compare(password, user.passwordHash);
    if (!match)  return errorResponse(res, 'Invalid email or password.', 401);

    return res.json({
      access_token:  makeAccessToken(user.id),
      refresh_token: makeRefreshToken(user.id),
    });
  } catch (err) {
    console.error('[auth/login]', err);
    return errorResponse(res, 'Internal server error.', 500);
  }
});

// ── POST /api/auth/refresh ────────────────────────────────────────────────────
router.post('/refresh', requireRefresh, (req, res) => {
  return res.json({ access_token: makeAccessToken(req.userId) });
});

module.exports = router;