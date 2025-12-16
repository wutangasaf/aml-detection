import type { Request, Response } from 'express';
import { ObjectId } from 'mongodb';
import { z } from 'zod';
import { getSessionsCollection, getMessagesCollection } from '../config/database.js';
import { processRagQuery } from '../services/rag.service.js';
import { SSEConnection } from '../middleware/sse.middleware.js';
import { createError } from '../middleware/error.middleware.js';
import type { ChatSession, Message, RagSource, TokenUsage } from '../types/index.js';

// Validation schemas
const createSessionSchema = z.object({
  title: z.string().min(1).max(200).optional(),
  sourceFilter: z.string().optional(),
});

const updateSessionSchema = z.object({
  title: z.string().min(1).max(200).optional(),
  sourceFilter: z.string().optional(),
});

const sendMessageSchema = z.object({
  content: z.string().min(1).max(10000),
});

// Create new session
export async function createSession(req: Request, res: Response): Promise<void> {
  const parsed = createSessionSchema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: 'VALIDATION_ERROR', message: parsed.error.message });
    return;
  }

  const sessions = getSessionsCollection();
  const now = new Date();

  const session: ChatSession = {
    userId: req.user!._id,
    title: parsed.data.title || 'New Chat',
    sourceFilter: parsed.data.sourceFilter,
    messageCount: 0,
    createdAt: now,
    updatedAt: now,
  };

  const result = await sessions.insertOne(session);

  res.status(201).json({
    session: {
      id: result.insertedId,
      ...session,
    },
  });
}

// List user sessions
export async function listSessions(req: Request, res: Response): Promise<void> {
  const sessions = getSessionsCollection();

  const userSessions = await sessions
    .find({ userId: req.user!._id })
    .sort({ updatedAt: -1 })
    .limit(50)
    .toArray();

  res.json({
    sessions: userSessions.map((s) => ({
      id: s._id,
      title: s.title,
      sourceFilter: s.sourceFilter,
      messageCount: s.messageCount,
      createdAt: s.createdAt,
      updatedAt: s.updatedAt,
    })),
  });
}

// Get session with messages
export async function getSession(req: Request, res: Response): Promise<void> {
  const { id } = req.params;

  if (!ObjectId.isValid(id)) {
    throw createError('Invalid session ID', 400, 'INVALID_ID');
  }

  const sessions = getSessionsCollection();
  const messages = getMessagesCollection();

  const session = await sessions.findOne({
    _id: new ObjectId(id),
    userId: req.user!._id,
  });

  if (!session) {
    throw createError('Session not found', 404, 'SESSION_NOT_FOUND');
  }

  const sessionMessages = await messages
    .find({ sessionId: session._id })
    .sort({ createdAt: 1 })
    .toArray();

  res.json({
    session: {
      id: session._id,
      title: session.title,
      sourceFilter: session.sourceFilter,
      messageCount: session.messageCount,
      createdAt: session.createdAt,
      updatedAt: session.updatedAt,
    },
    messages: sessionMessages.map((m) => ({
      id: m._id,
      role: m.role,
      content: m.content,
      ragContext: m.ragContext,
      createdAt: m.createdAt,
    })),
  });
}

// Update session
export async function updateSession(req: Request, res: Response): Promise<void> {
  const { id } = req.params;

  if (!ObjectId.isValid(id)) {
    throw createError('Invalid session ID', 400, 'INVALID_ID');
  }

  const parsed = updateSessionSchema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: 'VALIDATION_ERROR', message: parsed.error.message });
    return;
  }

  const sessions = getSessionsCollection();

  const result = await sessions.findOneAndUpdate(
    { _id: new ObjectId(id), userId: req.user!._id },
    { $set: { ...parsed.data, updatedAt: new Date() } },
    { returnDocument: 'after' }
  );

  if (!result) {
    throw createError('Session not found', 404, 'SESSION_NOT_FOUND');
  }

  res.json({
    session: {
      id: result._id,
      title: result.title,
      sourceFilter: result.sourceFilter,
      messageCount: result.messageCount,
      createdAt: result.createdAt,
      updatedAt: result.updatedAt,
    },
  });
}

// Delete session
export async function deleteSession(req: Request, res: Response): Promise<void> {
  const { id } = req.params;

  if (!ObjectId.isValid(id)) {
    throw createError('Invalid session ID', 400, 'INVALID_ID');
  }

  const sessions = getSessionsCollection();
  const messages = getMessagesCollection();

  const session = await sessions.findOne({
    _id: new ObjectId(id),
    userId: req.user!._id,
  });

  if (!session) {
    throw createError('Session not found', 404, 'SESSION_NOT_FOUND');
  }

  // Delete all messages in the session
  await messages.deleteMany({ sessionId: session._id });

  // Delete the session
  await sessions.deleteOne({ _id: session._id });

  res.json({ success: true });
}

// Send message (SSE stream)
export async function sendMessage(req: Request, res: Response): Promise<void> {
  const { id } = req.params;

  if (!ObjectId.isValid(id)) {
    throw createError('Invalid session ID', 400, 'INVALID_ID');
  }

  const parsed = sendMessageSchema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: 'VALIDATION_ERROR', message: parsed.error.message });
    return;
  }

  const sessions = getSessionsCollection();
  const messagesCollection = getMessagesCollection();

  // Verify session exists and belongs to user
  const session = await sessions.findOne({
    _id: new ObjectId(id),
    userId: req.user!._id,
  });

  if (!session) {
    throw createError('Session not found', 404, 'SESSION_NOT_FOUND');
  }

  // Save user message
  const userMessage: Message = {
    sessionId: session._id!,
    userId: req.user!._id,
    role: 'user',
    content: parsed.data.content,
    createdAt: new Date(),
  };

  await messagesCollection.insertOne(userMessage);

  // Get conversation history for context
  const history = await messagesCollection
    .find({ sessionId: session._id })
    .sort({ createdAt: 1 })
    .limit(20)
    .toArray();

  // Set up SSE connection
  const sse = new SSEConnection(res);
  const startTime = Date.now();

  let sources: RagSource[] = [];

  // Process RAG query with streaming
  await processRagQuery(
    parsed.data.content,
    history,
    session.sourceFilter,
    {
      onStatus: (stage) => {
        sse.sendStatus(stage);
      },
      onSources: (foundSources) => {
        sources = foundSources;
        sse.sendSources(foundSources);
      },
      onToken: (token) => {
        sse.sendDelta(token);
      },
      onComplete: async (usage: TokenUsage, fullResponse: string) => {
        // Save assistant message
        const assistantMessage: Message = {
          sessionId: session._id!,
          userId: req.user!._id,
          role: 'assistant',
          content: fullResponse,
          ragContext: {
            sources,
            model: 'claude-opus-4-20250514',
          },
          tokenUsage: usage,
          createdAt: new Date(),
        };

        const result = await messagesCollection.insertOne(assistantMessage);

        // Update session
        await sessions.updateOne(
          { _id: session._id },
          {
            $inc: { messageCount: 2 },
            $set: { updatedAt: new Date() },
          }
        );

        // Auto-generate title if this is the first message
        if (session.messageCount === 0) {
          const title = parsed.data.content.substring(0, 50) + (parsed.data.content.length > 50 ? '...' : '');
          await sessions.updateOne(
            { _id: session._id },
            { $set: { title } }
          );
        }

        sse.sendDone(Date.now() - startTime, usage, result.insertedId.toString());
      },
      onError: (error) => {
        console.error('RAG error:', error);
        sse.sendError(error.message, 'RAG_ERROR');
      },
    }
  );
}
