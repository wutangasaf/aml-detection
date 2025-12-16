import { searchRegulatoryDocs, formatContextForLLM } from './vector-search.service.js';
import { streamChatResponse, formatMessagesForContext, type StreamCallbacks } from './claude.service.js';
import type { Message, RagSource, TokenUsage } from '../types/index.js';

export interface RagStreamCallbacks {
  onStatus: (stage: 'embedding' | 'searching' | 'generating') => void;
  onSources: (sources: RagSource[]) => void;
  onToken: (token: string) => void;
  onComplete: (usage: TokenUsage, fullResponse: string) => void;
  onError: (error: Error) => void;
}

export async function processRagQuery(
  question: string,
  conversationHistory: Message[],
  sourceFilter: string | undefined,
  callbacks: RagStreamCallbacks
): Promise<void> {
  try {
    // Step 1: Search for relevant documents
    callbacks.onStatus('embedding');
    callbacks.onStatus('searching');

    const sources = await searchRegulatoryDocs(question, {
      limit: 8,
      sourceFilter,
    });

    callbacks.onSources(sources);

    // Step 2: Format context
    const context = formatContextForLLM(sources);

    // Step 3: Stream response from Claude
    callbacks.onStatus('generating');

    let fullResponse = '';
    const formattedHistory = formatMessagesForContext(conversationHistory);

    const claudeCallbacks: StreamCallbacks = {
      onToken: (token) => {
        fullResponse += token;
        callbacks.onToken(token);
      },
      onComplete: (usage) => {
        callbacks.onComplete(usage, fullResponse);
      },
      onError: (error) => {
        callbacks.onError(error);
      },
    };

    await streamChatResponse(question, context, formattedHistory, claudeCallbacks);
  } catch (error) {
    callbacks.onError(error instanceof Error ? error : new Error(String(error)));
  }
}
