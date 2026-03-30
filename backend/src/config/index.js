require('dotenv').config();

module.exports = {
  jwtAccessSecret:   process.env.JWT_ACCESS_SECRET  || 'dev_access_secret',
  jwtRefreshSecret:  process.env.JWT_REFRESH_SECRET || 'dev_refresh_secret',
  jwtAccessExpiresIn:  parseInt(process.env.JWT_ACCESS_EXPIRES_IN  || '900',     10),
  jwtRefreshExpiresIn: parseInt(process.env.JWT_REFRESH_EXPIRES_IN || '2592000', 10),

  // URL of the FastAPI ML model service
  mlModelUrl: process.env.ML_MODEL_URL || 'http://localhost:8000',

  corsOrigins: (process.env.CORS_ORIGINS || 'http://localhost:3000')
    .split(',')
    .map(o => o.trim()),
};