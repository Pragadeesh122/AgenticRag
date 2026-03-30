import type { ThreadMessageLike } from '@assistant-ui/react';
import type { Message } from './types';

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
  // For user messages, content is simple text
  if (message.role === 'user') {
    return {
      id: message.id,
      role: 'user',
      content: message.content,
      createdAt: new Date(message.createdAt),
    };
  }

  // For assistant messages, build a mutable content parts array
  const parts: ContentPart[] = [];

  // Add thinking/reasoning entries first (they appear before the text)
  for (const entry of message.thinkingEntries) {
    if (entry.type === 'text') {
      parts.push({
        type: 'data-thinking' as const,
        data: { content: entry.content },
      } as ContentPart);
    } else if (entry.type === 'tool') {
      parts.push({
        type: 'tool-call' as const,
        toolCallId: entry.toolCall.id,
        toolName: entry.toolCall.name,
        args: entry.toolCall.args ?? {},
        result: entry.toolCall.status === 'done'
          ? { status: 'done' }
          : entry.toolCall.status === 'error'
            ? { status: 'error' }
            : undefined,
      });
    }
  }

  // Add the main text content
  if (message.content) {
    parts.push({ type: 'text' as const, text: message.content });
  }

  return {
    id: message.id,
    role: 'assistant',
    content: parts.length > 0 ? parts : message.content,
    createdAt: new Date(message.createdAt),
    status: message.content ? { type: 'complete', reason: 'stop' } : { type: 'running' },
  };
}
