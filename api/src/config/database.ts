import { MongoClient, Db, Collection } from 'mongodb';
import { env } from './env.js';
import type { User, ChatSession, Message, VectorSearchResult } from '../types/index.js';

let client: MongoClient | null = null;
let amlDb: Db | null = null;
let crmDb: Db | null = null;

export async function connectDatabase(): Promise<void> {
  if (client) return;

  client = new MongoClient(env.MONGODB_URI, {
    serverSelectionTimeoutMS: 30000,
  });

  await client.connect();

  // Two databases:
  // aml_db - existing regulatory docs with vector embeddings
  // aml_crm_expert - new database for users, sessions, messages
  amlDb = client.db('aml_db');
  crmDb = client.db('aml_crm_expert');

  console.log('Connected to MongoDB');
}

export function getAmlDb(): Db {
  if (!amlDb) throw new Error('Database not connected');
  return amlDb;
}

export function getCrmDb(): Db {
  if (!crmDb) throw new Error('Database not connected');
  return crmDb;
}

// Collection accessors
export function getUsersCollection(): Collection<User> {
  return getCrmDb().collection<User>('users');
}

export function getSessionsCollection(): Collection<ChatSession> {
  return getCrmDb().collection<ChatSession>('sessions');
}

export function getMessagesCollection(): Collection<Message> {
  return getCrmDb().collection<Message>('messages');
}

export function getRegulatoryDocsCollection(): Collection<VectorSearchResult & { embedding: number[] }> {
  return getAmlDb().collection('regulatory_docs');
}

export async function createIndexes(): Promise<void> {
  const users = getUsersCollection();
  const sessions = getSessionsCollection();
  const messages = getMessagesCollection();

  // Users indexes
  await users.createIndex({ provider: 1, providerId: 1 }, { unique: true });
  await users.createIndex({ email: 1 });

  // Sessions indexes
  await sessions.createIndex({ userId: 1, updatedAt: -1 });

  // Messages indexes
  await messages.createIndex({ sessionId: 1, createdAt: 1 });
  await messages.createIndex({ userId: 1 });

  console.log('Database indexes created');
}

export async function closeDatabase(): Promise<void> {
  if (client) {
    await client.close();
    client = null;
    amlDb = null;
    crmDb = null;
  }
}
