import { getRegulatoryDocsCollection } from '../config/database.js';
import { generateEmbedding } from './embedding.service.js';
import type { VectorSearchResult, RagSource } from '../types/index.js';

interface VectorSearchOptions {
  limit?: number;
  sourceFilter?: string;
}

export async function searchRegulatoryDocs(
  query: string,
  options: VectorSearchOptions = {}
): Promise<RagSource[]> {
  const { limit = 8, sourceFilter } = options;

  // Generate embedding for the query
  const queryEmbedding = await generateEmbedding(query);

  const collection = getRegulatoryDocsCollection();

  // Build the vector search pipeline
  const vectorSearchStage: Record<string, unknown> = {
    index: 'vector_index',
    path: 'embedding',
    queryVector: queryEmbedding,
    numCandidates: 100,
    limit,
  };

  // Add source filter if specified
  if (sourceFilter) {
    vectorSearchStage.filter = { 'metadata.source': sourceFilter };
  }

  const pipeline = [
    { $vectorSearch: vectorSearchStage },
    {
      $project: {
        text: 1,
        metadata: 1,
        score: { $meta: 'vectorSearchScore' },
      },
    },
  ];

  const results = await collection.aggregate(pipeline).toArray();

  // Transform to RagSource format
  return results.map((doc) => ({
    source: doc.metadata?.source || 'Unknown',
    filename: doc.metadata?.filename || 'Unknown',
    score: doc.score || 0,
    textPreview: (doc.text || '').substring(0, 500),
  }));
}

export function formatContextForLLM(sources: RagSource[]): string {
  const contextParts = sources.map((source, i) => `
---
SOURCE ${i + 1}: [${source.source}] ${source.filename} (relevance: ${source.score.toFixed(2)})
${source.textPreview}
---
`);

  return contextParts.join('\n');
}
