import { Router } from 'express';
import { ObjectId } from 'mongodb';
import {
  createSession,
  listSessions,
  getSession,
  updateSession,
  deleteSession,
  sendMessage,
} from '../controllers/chat.controller.js';
// import { requireAuth } from '../middleware/auth.middleware.js';

const router = Router();

// TEMPORARY: Anonymous user middleware (bypasses OAuth)
// TODO: Re-enable authentication when ready
const ANONYMOUS_USER_ID = new ObjectId('000000000000000000000001');
router.use((req, _res, next) => {
  if (!req.user) {
    req.user = {
      _id: ANONYMOUS_USER_ID,
      provider: 'google',
      providerId: 'anonymous',
      email: 'anonymous@aml-expert.local',
      displayName: 'Anonymous User',
    };
  }
  next();
});

// Session CRUD
router.post('/sessions', createSession);
router.get('/sessions', listSessions);
router.get('/sessions/:id', getSession);
router.patch('/sessions/:id', updateSession);
router.delete('/sessions/:id', deleteSession);

// Messages (SSE stream)
router.post('/sessions/:id/messages', sendMessage);

export default router;
