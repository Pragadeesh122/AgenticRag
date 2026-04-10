import type {
  AssistantMessageStatus,
  Message,
  MessageMetadata,
  MessagePart,
  Project,
  ProjectDocument,
  RetrievalSource,
  Session,
  AgentInfo,
  UserMemory,
  MemoryCategory,
} from './types';
import {
  buildAssistantPartsFromLegacy,
  deriveSourcesFromParts,
  deriveThinkingEntriesFromParts,
  deriveToolCallsFromParts,
  extractTextFromParts,
  getDefaultAssistantStatus,
} from './messageParts';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function apiFetch(endpoint: string, options: RequestInit = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint.replace(/^\/api/, '')}`;
  const modifiedOptions = {
    ...options,
    credentials: 'include' as RequestCredentials,
  };
  return fetch(url, modifiedOptions);
}

// ─── Python backend (proxied or direct) ───

export async function signOut() {
  await apiFetch('/auth/logout', { method: 'POST' });
  // Make post-logout navigation explicit instead of relying on page guards after reload.
  window.location.href = '/auth/signin';
}

export async function loginWithCredentials(email: string, password: string): Promise<void> {
  const body = new URLSearchParams();
  body.set('username', email);
  body.set('password', password);

  const res = await apiFetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || 'Failed to sign in');
  }
}

export async function registerWithCredentials(email: string, password: string): Promise<void> {
  const res = await apiFetch('/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || 'Failed to create account');
  }
}

export async function createBackendSession(): Promise<string> {
  const res = await apiFetch('/api/chat/backend-session', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) throw new Error(`Failed to create session: ${res.status}`);
  const data = await res.json();
  return data.session_id;
}

export async function deleteBackendSession(sessionId: string): Promise<void> {
  await apiFetch(`/api/chat/backend-session/${sessionId}`, { method: 'DELETE' });
}

export async function backendSessionExists(sessionId: string): Promise<boolean> {
  const res = await apiFetch(`/session/${sessionId}/exists`);
  if (!res.ok) return false;
  const data = await res.json();
  return data.exists === true;
}

export async function restoreBackendSession(
  sessionId: string,
  messages: Array<{ role: string; content: string }>,
  projectName?: string
): Promise<void> {
  const res = await apiFetch('/session/restore', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      messages,
      project_name: projectName ?? null,
    }),
  });
  if (!res.ok) throw new Error('Failed to restore backend session');
}

export type SSEEvent =
  | { type: 'token'; data: string }
  | { type: 'tool'; data: { name: string; args?: Record<string, unknown> } }
  | { type: 'thinking'; data: { content: string } }
  | { type: 'agent'; data: { name: string; description: string } }
  | { type: 'retrieval'; data: { sources: RetrievalSource[]; count: number } }
  | { type: 'error'; data: string }
  | { type: 'done'; data: { tools_used?: string[]; sources_used?: number; agent?: string; structured?: boolean; prompt_tokens: number } };

export async function streamChat(
  sessionId: string,
  message: string,
  onEvent: (event: SSEEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const res = await apiFetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sessionId, message }),
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

    const parts = buffer.split('\n\n');
    buffer = parts.pop() ?? '';

    for (const part of parts) {
      const lines = part.split('\n');
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
      } else if (eventType === 'thinking') {
        try {
          onEvent({ type: 'thinking', data: JSON.parse(eventData) });
        } catch {
          // ignore malformed thinking event
        }
      } else if (eventType === 'retrieval') {
        try {
          onEvent({ type: 'retrieval', data: JSON.parse(eventData) });
        } catch {
          // ignore malformed retrieval event
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

// ─── FastAPI session + message persistence ───

export async function fetchSessions(): Promise<Session[]> {
  const res = await apiFetch('/api/chat/sessions');
  if (!res.ok) return [];
  return res.json();
}

export async function createChatSession(title?: string): Promise<Session> {
  const res = await apiFetch('/api/chat/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error('Failed to create chat session');
  return res.json();
}

export async function updateChatSession(
  id: string,
  data: { title?: string; backendSessionId?: string }
): Promise<void> {
  await apiFetch(`/api/chat/sessions/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

export async function deleteChatSession(
  id: string
): Promise<{ backendSessionId: string | null }> {
  const res = await apiFetch(`/api/chat/sessions/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete session');
  return res.json();
}

export async function fetchMessages(sessionId: string): Promise<Message[]> {
  const res = await apiFetch(`/api/chat/sessions/${sessionId}/messages`);
  if (!res.ok) return [];
  const messages: Array<{
    id: string;
    role: Message['role'];
    content: string;
    toolCalls?: Message['toolCalls'];
    parts?: MessagePart[];
    status?: AssistantMessageStatus;
    thinkingEntries?: Message['thinkingEntries'];
    sources?: RetrievalSource[];
    metadata?: MessageMetadata;
    agentName?: string;
    createdAt: string;
  }> = await res.json();

  return messages.map((message) => {
    const metadata = message.metadata ?? {};
    const parts =
      message.parts ??
      buildAssistantPartsFromLegacy({
        content: message.content,
        toolCalls: message.toolCalls ?? [],
        thinkingEntries: message.thinkingEntries ?? [],
        sources: message.sources ?? [],
      });

    const toolCalls = message.toolCalls ?? deriveToolCallsFromParts(parts);
    const thinkingEntries = message.thinkingEntries ?? deriveThinkingEntriesFromParts(parts);
    const sources = message.sources ?? deriveSourcesFromParts(parts);

    return {
      ...message,
      content: message.content || extractTextFromParts(parts),
      parts,
      toolCalls,
      thinkingEntries,
      sources,
      status: message.status ?? getDefaultAssistantStatus({ role: message.role, content: message.content || extractTextFromParts(parts) }),
      metadata,
      agentName: message.agentName ?? metadata.agentName,
    };
  });
}

export async function saveMessages(
  sessionId: string,
  messages: Array<{
    role: string;
    content: string;
    toolCalls?: unknown[];
    parts?: MessagePart[];
    status?: AssistantMessageStatus;
    thinkingEntries?: Message['thinkingEntries'];
    sources?: RetrievalSource[];
    agentName?: string;
    metadata?: Record<string, unknown>;
  }>
): Promise<Array<{ id: string; role: string }>> {
  const res = await apiFetch(`/api/chat/sessions/${sessionId}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(messages),
  });
  if (!res.ok) return [];
  const data = await res.json();
  return data.messages ?? [];
}

export async function updateMessageMetadata(
  messageId: string,
  metadata: Record<string, unknown>
): Promise<void> {
  const res = await apiFetch(`/api/chat/messages/${messageId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ metadata }),
  });
  if (!res.ok) throw new Error('Failed to update message metadata');
}

// ─── Projects API ───

export async function fetchProjects(): Promise<Project[]> {
  const res = await apiFetch('/api/projects');
  if (!res.ok) return [];
  return res.json();
}

export async function createProject(name: string, description?: string): Promise<Project> {
  const res = await apiFetch('/api/projects', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, description }),
  });
  if (!res.ok) throw new Error('Failed to create project');
  return res.json();
}

export async function fetchProject(id: string): Promise<Project> {
  const res = await apiFetch(`/api/projects/${id}`);
  if (!res.ok) throw new Error('Failed to fetch project');
  return res.json();
}

export async function updateProject(
  id: string,
  data: { name?: string; description?: string; status?: string }
): Promise<void> {
  await apiFetch(`/api/projects/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

export async function deleteProject(id: string): Promise<void> {
  await apiFetch(`/api/projects/${id}`, { method: 'DELETE' });
}

export async function uploadDocument(
  projectId: string,
  file: File
): Promise<ProjectDocument> {
  // 1. Create DB record + receive a scoped presigned upload URL.
  const initRes = await apiFetch(`/api/projects/${projectId}/upload`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename: file.name, fileSize: file.size }),
  });
  if (!initRes.ok) {
    const err = await initRes.json().catch(() => ({ error: 'Upload failed' }));
    throw new Error(err.detail || err.error || 'Upload failed');
  }

  const { uploadUrl, ...document } = await initRes.json();

  // 2. Upload file directly to object storage. No cookies should be sent.
  const uploadRes = await fetch(uploadUrl, {
    method: 'PUT',
    mode: 'cors',
    body: file,
  });
  if (!uploadRes.ok) {
    const detail = await uploadRes.text().catch(() => '');
    throw new Error(`Direct upload to storage failed (${uploadRes.status}): ${detail.slice(0, 300)}`);
  }

  // 3. Confirm upload and trigger ingestion.
  const confirmRes = await apiFetch(`/api/projects/${projectId}/upload`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ documentId: document.id, filename: file.name }),
  });
  if (!confirmRes.ok) {
    throw new Error('Failed to trigger ingestion');
  }

  return { ...document, status: 'processing' } as ProjectDocument;
}

export async function deleteDocument(projectId: string, docId: string): Promise<void> {
  const res = await apiFetch(`/api/projects/${projectId}/documents/${docId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete document');
}

export async function getDocumentDownloadUrl(
  projectId: string,
  docId: string
): Promise<string> {
  const res = await apiFetch(`/api/projects/${projectId}/documents/${docId}/download`);
  if (!res.ok) throw new Error('Failed to get document URL');
  const data = await res.json();
  return data.url;
}

export async function reingestDocument(
  projectId: string,
  docId: string,
  file: File
): Promise<ProjectDocument> {
  const initRes = await apiFetch(`/api/projects/${projectId}/documents/${docId}/reingest`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename: file.name, fileSize: file.size }),
  });
  if (!initRes.ok) {
    const err = await initRes.json().catch(() => ({ error: 'Re-ingest failed' }));
    throw new Error(err.detail || err.error || 'Re-ingest failed');
  }

  const { uploadUrl, ...document } = await initRes.json();

  const uploadRes = await fetch(uploadUrl, {
    method: 'PUT',
    mode: 'cors',
    body: file,
  });
  if (!uploadRes.ok) {
    const detail = await uploadRes.text().catch(() => '');
    throw new Error(`Direct upload to storage failed (${uploadRes.status}): ${detail.slice(0, 300)}`);
  }

  const confirmRes = await apiFetch(`/api/projects/${projectId}/upload`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ documentId: document.id, filename: file.name }),
  });
  if (!confirmRes.ok) {
    throw new Error('Failed to trigger ingestion');
  }

  return { ...document, status: 'processing' } as ProjectDocument;
}

export async function pollDocumentStatus(
  projectId: string,
  docId: string
): Promise<{ status: string; chunkCount: number; chunkStrategy: string | null; errorMessage: string | null }> {
  const res = await apiFetch(`/api/projects/${projectId}/documents/${docId}/status`);
  if (!res.ok) throw new Error('Failed to get document status');
  return res.json();
}

// ─── Project Chat ───

export async function fetchProjectSessions(projectId: string): Promise<Session[]> {
  const res = await apiFetch(`/api/projects/${projectId}/sessions`);
  if (!res.ok) return [];
  return res.json();
}

export async function createProjectSession(
  projectId: string
): Promise<Session> {
  const res = await apiFetch(`/api/projects/${projectId}/session`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to create project session');
  return res.json();
}

export async function deleteProjectSession(
  projectId: string,
  sessionId: string
): Promise<void> {
  await apiFetch(`/api/projects/${projectId}/session/${sessionId}`, {
    method: 'DELETE',
  });
}

export async function fetchAgents(): Promise<AgentInfo[]> {
  const res = await apiFetch('/api/projects/agents');
  if (!res.ok) return [];
  return res.json();
}

// ─── Memory API ───

export async function fetchMemory(): Promise<UserMemory> {
  const res = await apiFetch('/api/chat/memory');
  if (!res.ok) {
    return { work_context: '', personal_context: '', top_of_mind: '', preferences: '' };
  }
  return res.json();
}

export async function updateMemoryCategory(
  category: MemoryCategory,
  content: string
): Promise<void> {
  await apiFetch('/api/chat/memory', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ category, content }),
  });
}

// ─── Project Chat Stream ───

export async function streamProjectChat(
  projectId: string,
  sessionId: string,
  message: string,
  onEvent: (event: SSEEvent) => void,
  agent?: string | null,
  signal?: AbortSignal
): Promise<void> {
  const res = await apiFetch(`/api/projects/${projectId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sessionId, message, agent: agent || null }),
    signal,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Project chat failed: ${res.status} ${text}`);
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const parts = buffer.split('\n\n');
    buffer = parts.pop() ?? '';

    for (const part of parts) {
      const lines = part.split('\n');
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
      } else if (eventType === 'agent') {
        try {
          onEvent({ type: 'agent', data: JSON.parse(eventData) });
        } catch {
          // ignore
        }
      } else if (eventType === 'thinking') {
        try {
          onEvent({ type: 'thinking', data: JSON.parse(eventData) });
        } catch {
          // ignore
        }
      } else if (eventType === 'retrieval') {
        try {
          onEvent({ type: 'retrieval', data: JSON.parse(eventData) });
        } catch {
          // ignore
        }
      } else if (eventType === 'error') {
        onEvent({ type: 'error', data: eventData });
      } else if (eventType === 'done') {
        try {
          onEvent({ type: 'done', data: JSON.parse(eventData) });
        } catch {
          onEvent({ type: 'done', data: { sources_used: 0, prompt_tokens: 0 } });
        }
      }
    }
  }
}
