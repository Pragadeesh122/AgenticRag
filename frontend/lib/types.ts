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
  createdAt: number;
}

export interface Session {
  id: string;
  sessionId: string;
  title: string;
  createdAt: number;
  updatedAt: number;
}
