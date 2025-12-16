import { Router } from 'express';
import {
  googleAuth,
  googleCallback,
  githubAuth,
  githubCallback,
  getCurrentUser,
  logout,
} from '../controllers/auth.controller.js';
import { requireAuth } from '../middleware/auth.middleware.js';

const router = Router();

// Google OAuth
router.get('/google', googleAuth);
router.get('/google/callback', googleCallback);

// GitHub OAuth
router.get('/github', githubAuth);
router.get('/github/callback', githubCallback);

// User info
router.get('/me', requireAuth, getCurrentUser);

// Logout
router.post('/logout', requireAuth, logout);

export default router;
