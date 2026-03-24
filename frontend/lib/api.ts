const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function createSession(): Promise<string> {
  const res = await fetch(`${BASE_URL}/session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) throw new Error(`Failed to create session: ${res.status}`);
  const data = await res.json();
  return data.session_id;
}

export async function deleteSession(sessionId: string): Promise<void> {
  await fetch(`${BASE_URL}/session/${sessionId}`, { method: 'DELETE' });
}

export type SSEEvent =
  | { type: 'token'; data: string }
  | { type: 'tool'; data: { name: string } }
  | { type: 'error'; data: string }
  | { type: 'done'; data: { tools_used: string[]; prompt_tokens: number } };

export async function streamChat(
  sessionId: string,
  message: string,
  onEvent: (event: SSEEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message }),
    signal,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Chat request failed: ${res.status} ${text}`);
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE events are separated by double newlines
    const parts = buffer.split('\n\n');
    buffer = parts.pop() ?? '';

    for (const part of parts) {
      const lines = part.trim().split('\n');
      let eventType = '';
      const dataLines: string[] = [];

      for (const line of lines) {
        if (line.startsWith('event: ')) {
          eventType = line.slice(7).trim();
        } else if (line.startsWith('data: ')) {
          dataLines.push(line.slice(6));
        }
      }

      const eventData = dataLines.join('\n');

      if (!eventType || dataLines.length === 0) continue;

      if (eventType === 'token') {
        onEvent({ type: 'token', data: eventData });
      } else if (eventType === 'tool') {
        try {
          onEvent({ type: 'tool', data: JSON.parse(eventData) });
        } catch {
          // ignore malformed tool event
        }
      } else if (eventType === 'error') {
        onEvent({ type: 'error', data: eventData });
      } else if (eventType === 'done') {
        try {
          onEvent({ type: 'done', data: JSON.parse(eventData) });
        } catch {
          onEvent({ type: 'done', data: { tools_used: [], prompt_tokens: 0 } });
        }
      }
    }
  }
}
