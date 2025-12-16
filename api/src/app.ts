import express from 'express';
import helmet from 'helmet';
import cors from 'cors';
import session from 'express-session';
import MongoStore from 'connect-mongo';
import passport from 'passport';
import rateLimit from 'express-rate-limit';

import { env } from './config/env.js';
import { configurePassport } from './config/passport.js';
import { errorHandler, notFoundHandler } from './middleware/error.middleware.js';

import authRoutes from './routes/auth.routes.js';
import chatRoutes from './routes/chat.routes.js';

export function createApp(): express.Application {
  const app = express();

  // Security middleware
  app.use(helmet({
    contentSecurityPolicy: false, // Disable for SSE
  }));

  // CORS
  app.use(cors({
    origin: env.CLIENT_URL,
    credentials: true,
  }));

  // Body parsing
  app.use(express.json({ limit: '1mb' }));
  app.use(express.urlencoded({ extended: true }));

  // Rate limiting
  const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // Limit each IP to 100 requests per window
    message: { error: 'RATE_LIMIT', message: 'Too many requests, please try again later' },
  });
  app.use('/api', limiter);

  // Stricter rate limit for chat messages
  const chatLimiter = rateLimit({
    windowMs: 60 * 1000, // 1 minute
    max: 20, // 20 messages per minute
    message: { error: 'RATE_LIMIT', message: 'Too many messages, please slow down' },
  });
  app.use('/chat/sessions/:id/messages', chatLimiter);

  // Session management
  app.use(session({
    secret: env.SESSION_SECRET,
    resave: false,
    saveUninitialized: false,
    store: MongoStore.create({
      mongoUrl: env.MONGODB_URI,
      dbName: 'aml_crm_expert',
      collectionName: 'sessions_store',
      ttl: 7 * 24 * 60 * 60, // 7 days
    }),
    cookie: {
      secure: env.NODE_ENV === 'production',
      httpOnly: true,
      maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
      sameSite: env.NODE_ENV === 'production' ? 'strict' : 'lax',
    },
  }));

  // Passport authentication
  configurePassport();
  app.use(passport.initialize());
  app.use(passport.session());

  // Health check
  app.get('/health', (_req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
  });

  // Routes
  app.use('/auth', authRoutes);
  app.use('/chat', chatRoutes);

  // Error handling
  app.use(notFoundHandler);
  app.use(errorHandler);

  return app;
}
