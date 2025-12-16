import type { Request, Response, NextFunction } from 'express';
import passport from 'passport';
import { env } from '../config/env.js';

// Google OAuth
export function googleAuth(req: Request, res: Response, next: NextFunction): void {
  passport.authenticate('google', { scope: ['profile', 'email'] })(req, res, next);
}

export function googleCallback(req: Request, res: Response, next: NextFunction): void {
  passport.authenticate('google', {
    failureRedirect: `${env.CLIENT_URL}/login?error=google_auth_failed`,
  })(req, res, () => {
    res.redirect(`${env.CLIENT_URL}/chat`);
  });
}

// GitHub OAuth
export function githubAuth(req: Request, res: Response, next: NextFunction): void {
  passport.authenticate('github', { scope: ['user:email'] })(req, res, next);
}

export function githubCallback(req: Request, res: Response, next: NextFunction): void {
  passport.authenticate('github', {
    failureRedirect: `${env.CLIENT_URL}/login?error=github_auth_failed`,
  })(req, res, () => {
    res.redirect(`${env.CLIENT_URL}/chat`);
  });
}

// Get current user
export function getCurrentUser(req: Request, res: Response): void {
  if (req.user) {
    res.json({
      user: {
        id: req.user._id,
        email: req.user.email,
        displayName: req.user.displayName,
        avatarUrl: req.user.avatarUrl,
        provider: req.user.provider,
      },
    });
  } else {
    res.status(401).json({ error: 'Not authenticated' });
  }
}

// Logout
export function logout(req: Request, res: Response): void {
  req.logout((err) => {
    if (err) {
      console.error('Logout error:', err);
      res.status(500).json({ error: 'Logout failed' });
      return;
    }
    req.session.destroy(() => {
      res.json({ success: true });
    });
  });
}
