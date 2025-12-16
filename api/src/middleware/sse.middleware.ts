import type { Response } from 'express';
import type { SSEEventType, SSEStatusEvent, SSESourcesEvent, SSEDeltaEvent, SSEDoneEvent, SSEErrorEvent } from '../types/index.js';

export class SSEConnection {
  private res: Response;
  private closed = false;

  constructor(res: Response) {
    this.res = res;
    this.setupSSE();
  }

  private setupSSE(): void {
    this.res.setHeader('Content-Type', 'text/event-stream');
    this.res.setHeader('Cache-Control', 'no-cache');
    this.res.setHeader('Connection', 'keep-alive');
    this.res.setHeader('X-Accel-Buffering', 'no');
    this.res.flushHeaders();

    // Handle client disconnect
    this.res.on('close', () => {
      this.closed = true;
    });
  }

  send(event: SSEEventType, data: SSEStatusEvent | SSESourcesEvent | SSEDeltaEvent | SSEDoneEvent | SSEErrorEvent): void {
    if (this.closed) return;

    this.res.write(`event: ${event}\n`);
    this.res.write(`data: ${JSON.stringify(data)}\n\n`);
  }

  sendStatus(stage: SSEStatusEvent['stage']): void {
    this.send('status', { stage });
  }

  sendSources(sources: SSESourcesEvent['sources']): void {
    this.send('sources', { sources });
  }

  sendDelta(content: string): void {
    this.send('delta', { content });
  }

  sendDone(totalTimeMs: number, tokenUsage: SSEDoneEvent['tokenUsage'], messageId: string): void {
    this.send('done', { totalTimeMs, tokenUsage, messageId });
    this.close();
  }

  sendError(message: string, code: string): void {
    this.send('error', { message, code });
    this.close();
  }

  close(): void {
    if (!this.closed) {
      this.res.end();
      this.closed = true;
    }
  }

  isClosed(): boolean {
    return this.closed;
  }
}
