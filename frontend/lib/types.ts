export type MessageRole = 'user' | 'assistant';

export type ToolStatus = 'running' | 'done' | 'error';

export interface ToolCall {
  id: string;
  name: string;
  status: ToolStatus;
  args?: Record<string, string>;
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

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  toolCalls: ToolCall[];
  thinkingEntries: ThinkingEntry[];
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
