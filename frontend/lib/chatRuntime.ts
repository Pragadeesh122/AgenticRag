import type { ThreadMessageLike } from '@assistant-ui/react';
import type { Message } from './types';
import { buildAssistantPartsFromLegacy, getDefaultAssistantStatus } from './messageParts';

// Content part types that ThreadMessageLike accepts
type ContentPart = NonNullable<
  Exclude<ThreadMessageLike['content'], string>
>[number];

/**
 * Convert our internal Message type to assistant-ui's ThreadMessageLike.
 *
 * This is the bridge between our custom state and assistant-ui's runtime.
 * It maps our content + toolCalls + thinkingEntries into the content-parts
 * array that assistant-ui expects.
 */
export function convertMessage(message: Message): ThreadMessageLike {
  if (message.role === 'user') {
    return {
      id: message.id,
      role: 'user',
      content: [{ type: 'text', text: message.content }],
      createdAt: new Date(message.createdAt),
      metadata: {
        custom: {
          dbId: message.dbId,
        },
      },
    };
  }

  const parts = (message.parts.length > 0
    ? message.parts
    : buildAssistantPartsFromLegacy(message)) as ContentPart[];

  return {
    id: message.id,
    role: 'assistant',
    content: parts.length > 0 ? parts : [{ type: 'text' as const, text: message.content }],
    createdAt: new Date(message.createdAt),
    status: message.status ?? getDefaultAssistantStatus(message) ?? { type: 'running' },
    metadata: {
      custom: {
        dbId: message.dbId,
        agentName: message.agentName,
        sources: message.sources,
      },
    },
  };
}
