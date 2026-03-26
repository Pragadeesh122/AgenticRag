export type MessageRole = 'user' | 'assistant';

export type ToolStatus = 'running' | 'done' | 'error';

export interface ToolCall {
  id: string;
  name: string;
  status: ToolStatus;
  startedAt?: number;
  completedAt?: number;
}

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  toolCalls: ToolCall[];
  createdAt: string; // ISO string from DB
}

export interface Session {
  id: string;
  backendSessionId: string | null;
  title: string;
  createdAt: string; // ISO string from DB
  updatedAt: string;
}
