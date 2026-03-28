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
  agentName?: string; // set for project agent responses (quiz, visualization, etc.)
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
