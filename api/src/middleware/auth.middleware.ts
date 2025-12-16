import type { Request, Response, NextFunction } from 'express';

export function requireAuth(req: Request, res: Response, next: NextFunction): void {
  if (req.isAuthenticated() && req.user) {
    next();
    return;
  }
  res.status(401).json({ error: 'Unauthorized', message: 'Please log in to access this resource' });
}

export function optionalAuth(req: Request, res: Response, next: NextFunction): void {
  // Just pass through - user may or may not be authenticated
  next();
}
