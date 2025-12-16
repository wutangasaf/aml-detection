import { ObjectId } from 'mongodb';

// User types
export interface User {
  _id?: ObjectId;
  provider: 'google' | 'github';
  providerId: string;
  email: string;
  displayName: string;
  avatarUrl?: string;
  createdAt: Date;
  lastLoginAt: Date;
}

// Chat session types
export interface ChatSession {
  _id?: ObjectId;
  userId: ObjectId;
  title: string;
  sourceFilter?: string;
  messageCount: number;
  createdAt: Date;
  updatedAt: Date;
}

// Message types
export interface Message {
  _id?: ObjectId;
  sessionId: ObjectId;
  userId: ObjectId;
  role: 'user' | 'assistant';
  content: string;
  ragContext?: RagContext;
  tokenUsage?: TokenUsage;
  createdAt: Date;
}

export interface RagContext {
  sources: RagSource[];
  model: string;
}

export interface RagSource {
  source: string;
  filename: string;
  score: number;
  textPreview: string;
}

export interface TokenUsage {
  inputTokens: number;
  outputTokens: number;
}

// SSE event types
export type SSEEventType = 'status' | 'sources' | 'delta' | 'done' | 'error';

export interface SSEStatusEvent {
  stage: 'embedding' | 'searching' | 'generating';
}

export interface SSESourcesEvent {
  sources: RagSource[];
}

export interface SSEDeltaEvent {
  content: string;
}

export interface SSEDoneEvent {
  totalTimeMs: number;
  tokenUsage: TokenUsage;
  messageId: string;
}

export interface SSEErrorEvent {
  message: string;
  code: string;
}

// Vector search types
export interface VectorSearchResult {
  text: string;
  metadata: {
    source: string;
    filename: string;
  };
  score: number;
}

// Express augmentation
declare global {
  namespace Express {
    interface User {
      _id: ObjectId;
      provider: 'google' | 'github';
      providerId: string;
      email: string;
      displayName: string;
      avatarUrl?: string;
    }
  }
}

export {};
