import Anthropic from '@anthropic-ai/sdk';
import { env } from '../config/env.js';
import type { Message, TokenUsage } from '../types/index.js';

let anthropicClient: Anthropic | null = null;

function getAnthropic(): Anthropic {
  if (!anthropicClient) {
    anthropicClient = new Anthropic({ apiKey: env.ANTHROPIC_API_KEY });
  }
  return anthropicClient;
}

const CLAUDE_MODEL = 'claude-opus-4-20250514';

const AML_EXPERT_SYSTEM_PROMPT = `You are a senior AML/CFT compliance expert with 20+ years of experience.

Your background:
- Former MLRO (Money Laundering Reporting Officer) at a Tier 1 bank
- Certified Anti-Money Laundering Specialist (CAMS)
- Deep expertise in FATF recommendations, EU AML directives, and UK/US regulations
- Experience with enforcement actions and regulatory examinations
- Practical knowledge of transaction monitoring, KYC/CDD, and SAR filing

Your role:
- Answer questions about AML/CFT compliance with precision
- Explain complex regulatory concepts in clear terms
- Provide practical, actionable guidance
- Cite specific regulations and guidance when relevant
- Share real enforcement case examples to illustrate points
- Identify red flags and typologies
- Help design effective detection systems

Your style:
- Professional but accessible
- Specific and detailed, not vague
- Always cite sources when available
- Acknowledge uncertainty when appropriate
- Think step-by-step through complex questions

When answering:
1. First, understand what the user is really asking
2. Draw on the provided regulatory context
3. Give a clear, structured answer
4. Cite specific sources (FATF, EU AMLR, enforcement cases)
5. Provide practical examples where helpful`;

const RAG_PROMPT_TEMPLATE = `
REGULATORY CONTEXT (from knowledge base):
{context}

USER QUESTION:
{question}

Provide a comprehensive answer based on the regulatory context above and your expertise.
Structure your response clearly. Cite specific documents when referencing guidance.
`;

interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface StreamCallbacks {
  onToken: (token: string) => void;
  onComplete: (usage: TokenUsage) => void;
  onError: (error: Error) => void;
}

export async function streamChatResponse(
  question: string,
  context: string,
  conversationHistory: ConversationMessage[],
  callbacks: StreamCallbacks
): Promise<void> {
  const anthropic = getAnthropic();

  // Build the user prompt with context
  const userPrompt = RAG_PROMPT_TEMPLATE
    .replace('{context}', context)
    .replace('{question}', question);

  // Build messages array with conversation history
  const messages: Anthropic.MessageParam[] = [
    ...conversationHistory.map((msg) => ({
      role: msg.role as 'user' | 'assistant',
      content: msg.content,
    })),
    { role: 'user', content: userPrompt },
  ];

  try {
    const stream = await anthropic.messages.stream({
      model: CLAUDE_MODEL,
      max_tokens: 2000,
      system: AML_EXPERT_SYSTEM_PROMPT,
      messages,
    });

    for await (const event of stream) {
      if (event.type === 'content_block_delta') {
        const delta = event.delta;
        if ('text' in delta) {
          callbacks.onToken(delta.text);
        }
      }
    }

    const finalMessage = await stream.finalMessage();
    callbacks.onComplete({
      inputTokens: finalMessage.usage.input_tokens,
      outputTokens: finalMessage.usage.output_tokens,
    });
  } catch (error) {
    callbacks.onError(error instanceof Error ? error : new Error(String(error)));
  }
}

export function formatMessagesForContext(messages: Message[]): ConversationMessage[] {
  return messages
    .filter((m) => m.role === 'user' || m.role === 'assistant')
    .map((m) => ({
      role: m.role,
      content: m.content,
    }));
}
