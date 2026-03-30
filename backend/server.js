require('dotenv').config();
const express = require('express');
const cors    = require('cors');
const { PrismaClient } = require('@prisma/client');

const authRoutes      = require('./src/routes/auth');
const portfolioRoutes = require('./src/routes/portfolio');
const aiAdvisorRoutes = require('./src/routes/aiAdvisor');
const nseDataRoutes   = require('./src/routes/nseData');
const { errorHandler, notFoundHandler } = require('./src/middleware/errorHandler');

const prisma = new PrismaClient();
const app    = express();

// ── CORS ──────────────────────────────────────────────────────────────────────
const allowedOrigins = (process.env.CORS_ORIGINS || 'http://localhost:3000')
  .split(',')
  .map(o => o.trim());

app.use(cors({
  origin: allowedOrigins,
  credentials: true,
}));

// ── Body parsing ──────────────────────────────────────────────────────────────
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// ── Attach Prisma to every request ────────────────────────────────────────────
app.use((req, _res, next) => {
  req.prisma = prisma;
  next();
});

// ── Routes ────────────────────────────────────────────────────────────────────
app.use('/api/auth',      authRoutes);
app.use('/api/portfolio', portfolioRoutes);
app.use('/api/ai',        aiAdvisorRoutes);
app.use('/api/nse',       nseDataRoutes);

// ── Health check ──────────────────────────────────────────────────────────────
app.get('/health', (_req, res) => res.json({ status: 'ok' }));

// ── Error handling ────────────────────────────────────────────────────────────
app.use(notFoundHandler);
app.use(errorHandler);

// ── Boot ──────────────────────────────────────────────────────────────────────
const PORT = parseInt(process.env.PORT || '5000', 10);

async function bootstrap() {
  try {
    await prisma.$connect();
    console.log('✓ Database connected');
    app.listen(PORT, '0.0.0.0', () => {
      console.log(`✓ InvestIQ backend running on http://0.0.0.0:${PORT}`);
    });
  } catch (err) {
    console.error('✗ Failed to start:', err);
    process.exit(1);
  }
}

bootstrap();

// ── Graceful shutdown ─────────────────────────────────────────────────────────
process.on('SIGINT',  async () => { await prisma.$disconnect(); process.exit(0); });
process.on('SIGTERM', async () => { await prisma.$disconnect(); process.exit(0); });