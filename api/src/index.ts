import 'dotenv/config';
import { createApp } from './app.js';
import { connectDatabase, createIndexes, closeDatabase } from './config/database.js';
import { env } from './config/env.js';

async function main(): Promise<void> {
  try {
    // Connect to MongoDB
    console.log('Connecting to MongoDB...');
    await connectDatabase();
    await createIndexes();

    // Create Express app
    const app = createApp();

    // Start server
    const server = app.listen(parseInt(env.PORT), () => {
      console.log(`
╔════════════════════════════════════════════════════════════════╗
║                   AML Expert Chat API                          ║
╠════════════════════════════════════════════════════════════════╣
║  Server running on: http://localhost:${env.PORT}                    ║
║  Environment: ${env.NODE_ENV.padEnd(46)}║
║                                                                ║
║  Endpoints:                                                    ║
║    Auth:                                                       ║
║      GET  /auth/google          - Start Google OAuth           ║
║      GET  /auth/github          - Start GitHub OAuth           ║
║      GET  /auth/me              - Get current user             ║
║      POST /auth/logout          - Logout                       ║
║                                                                ║
║    Chat:                                                       ║
║      POST /chat/sessions        - Create new session           ║
║      GET  /chat/sessions        - List user sessions           ║
║      GET  /chat/sessions/:id    - Get session with messages    ║
║      PATCH /chat/sessions/:id   - Update session               ║
║      DELETE /chat/sessions/:id  - Delete session               ║
║      POST /chat/sessions/:id/messages - Send message (SSE)     ║
║                                                                ║
║  Powered by: Claude Opus 4 + OpenAI Embeddings                 ║
╚════════════════════════════════════════════════════════════════╝
      `);
    });

    // Graceful shutdown
    const shutdown = async (): Promise<void> => {
      console.log('\nShutting down...');
      server.close();
      await closeDatabase();
      process.exit(0);
    };

    process.on('SIGINT', shutdown);
    process.on('SIGTERM', shutdown);

  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

main();
