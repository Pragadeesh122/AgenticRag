export type MessageRole = 'user' | 'assistant';

export interface User {
  id: string;
  email: string;
  name: string | null;
  image: string | null;
}

export type ToolStatus = 'running' | 'done' | 'error';

export interface ToolCall {
  id: string;
  name: string;
  status: ToolStatus;
  args?: Record<string, unknown>;
  startedAt?: number;
  completedAt?: number;
}

export type ThinkingEntry =
  | { type: 'text'; content: string }
  | { type: 'tool'; toolCall: ToolCall };

export interface MessageMetadata {
  agentName?: string;
  quizState?: Record<number, { selected: string | null; revealed: boolean; shortAnswer: string }>;
}

export type AssistantMessageStatus =
  | { type: 'running' }
  | { type: 'requires-action'; reason: 'tool-calls' | 'interrupt' }
  | { type: 'complete'; reason: 'stop' | 'unknown' }
  | { type: 'incomplete'; reason: 'cancelled' | 'tool-calls' | 'length' | 'content-filter' | 'other' | 'error'; error?: unknown };

export type MessagePart =
  | { type: 'text'; text: string; parentId?: string }
  | { type: 'reasoning'; text: string; parentId?: string }
  | {
      type: 'tool-call';
      toolCallId: string;
      toolName: string;
      args: Record<string, unknown>;
      argsText: string;
      result?: unknown;
      isError?: boolean;
      parentId?: string;
    }
  | {
      type: 'source';
      sourceType: 'url';
      id: string;
      url: string;
      title?: string;
      parentId?: string;
    }
  | { type: 'data'; name: string; data: unknown };

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  parts: MessagePart[];
  toolCalls: ToolCall[];
  thinkingEntries: ThinkingEntry[];
  sources: RetrievalSource[];
  status?: AssistantMessageStatus;
  thinkingStartedAt?: number;
  thinkingDuration?: number;
  metadata: MessageMetadata;
  createdAt: string; // ISO string from DB
  agentName?: string; // set during streaming, persisted in metadata
  dbId?: string; // actual database id replaced after streaming completes
}

export interface Session {
  id: string;
  projectId?: string | null;
  backendSessionId: string | null;
  title: string;
  createdAt: string; // ISO string from DB
  updatedAt: string;
}

export interface ProjectDocument {
  id: string;
  filename: string;
  fileType: string;
  fileSize: number;
  chunkCount: number;
  chunkStrategy: string | null;
  status: 'uploading' | 'processing' | 'ready' | 'failed';
  errorMessage: string | null;
  createdAt: string;
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  status: string;
  documents: ProjectDocument[];
  createdAt: string;
  updatedAt: string;
}

export interface ProjectSearchResult {
  id: string;
  snippet: string;
  source: string;
  page: number | null;
  score: number;
  documentId: string | null;
}

export interface RetrievalSource {
  source: string;
  page: number | null;
  score: number;
}

export interface AgentInfo {
  name: string;
  description: string;
  structured_output: boolean;
}

export type MemoryCategory = 'work_context' | 'personal_context' | 'top_of_mind' | 'preferences';

export type UserMemory = Record<MemoryCategory, string>;
