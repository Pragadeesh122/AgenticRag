'use client';

import { useState, useCallback, useEffect } from 'react';
import { CaretLeft } from '@phosphor-icons/react/dist/ssr/CaretLeft';
import { CaretRight } from '@phosphor-icons/react/dist/ssr/CaretRight';
import { PencilSimpleLineIcon } from '@phosphor-icons/react/dist/ssr/PencilSimpleLine';
import Sidebar from '@/components/Sidebar';
import ChatArea from '@/components/ChatArea';
import { createSession, deleteSession, streamChat } from '@/lib/api';
import type { Session, Message, ToolCall } from '@/lib/types';

const STORAGE_KEY = 'agentic-rag-sessions';
const MESSAGES_KEY = 'agentic-rag-messages';

function loadSessions(): Session[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Session[]) : [];
  } catch {
    return [];
  }
}

function saveSessions(sessions: Session[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
}

function loadMessages(sessionLocalId: string): Message[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(`${MESSAGES_KEY}:${sessionLocalId}`);
    return raw ? (JSON.parse(raw) as Message[]) : [];
  } catch {
    return [];
  }
}

function saveMessages(sessionLocalId: string, messages: Message[]) {
  localStorage.setItem(`${MESSAGES_KEY}:${sessionLocalId}`, JSON.stringify(messages));
}

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function getTitleFromContent(content: string): string {
  const trimmed = content.trim();
  if (trimmed.length <= 40) return trimmed;
  return trimmed.slice(0, 40).trim() + '\u2026';
}

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messagesBySession, setMessagesBySession] = useState<Record<string, Message[]>>({});
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);

  // Load persisted data on mount
  useEffect(() => {
    const stored = loadSessions();
    setSessions(stored);

    const allMessages: Record<string, Message[]> = {};
    for (const s of stored) {
      allMessages[s.id] = loadMessages(s.id);
    }
    setMessagesBySession(allMessages);

    if (stored.length > 0) {
      setActiveSessionId(stored[0].id);
    }
  }, []);

  const activeMessages: Message[] = activeSessionId
    ? (messagesBySession[activeSessionId] ?? [])
    : [];

  const updateMessages = useCallback(
    (sessionLocalId: string, updater: (prev: Message[]) => Message[]) => {
      setMessagesBySession((prev) => {
        const current = prev[sessionLocalId] ?? [];
        const next = updater(current);
        saveMessages(sessionLocalId, next);
        return { ...prev, [sessionLocalId]: next };
      });
    },
    []
  );

  const handleNewChat = useCallback(() => {
    // If current session is already empty, just stay on it
    if (activeSessionId) {
      const currentMessages = messagesBySession[activeSessionId] ?? [];
      if (currentMessages.length === 0) return;
    }

    const localId = generateId();
    const newSession: Session = {
      id: localId,
      sessionId: '',
      title: 'New chat',
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };
    setSessions((prev) => {
      const next = [newSession, ...prev];
      saveSessions(next);
      return next;
    });
    setMessagesBySession((prev) => ({ ...prev, [localId]: [] }));
    setActiveSessionId(localId);
    setInputValue('');
  }, [activeSessionId, messagesBySession]);

  const handleSelectSession = useCallback((id: string) => {
    setActiveSessionId(id);
    setInputValue('');
  }, []);

  const handleDeleteSession = useCallback(
    async (localId: string) => {
      const session = sessions.find((s) => s.id === localId);
      if (session?.sessionId) {
        try {
          await deleteSession(session.sessionId);
        } catch {
          // ignore backend errors on delete
        }
      }

      setSessions((prev) => {
        const next = prev.filter((s) => s.id !== localId);
        saveSessions(next);
        return next;
      });

      setMessagesBySession((prev) => {
        const next = { ...prev };
        delete next[localId];
        localStorage.removeItem(`${MESSAGES_KEY}:${localId}`);
        return next;
      });

      setActiveSessionId((prev) => {
        if (prev === localId) {
          const remaining = sessions.filter((s) => s.id !== localId);
          return remaining.length > 0 ? remaining[0].id : null;
        }
        return prev;
      });
    },
    [sessions]
  );

  const handleSubmit = useCallback(async () => {
    const content = inputValue.trim();
    if (!content || isLoading) return;

    let localId = activeSessionId;

    // Create a new local session if none is active
    if (!localId) {
      const newId = generateId();
      const newSession: Session = {
        id: newId,
        sessionId: '',
        title: getTitleFromContent(content),
        createdAt: Date.now(),
        updatedAt: Date.now(),
      };
      setSessions((prev) => {
        const next = [newSession, ...prev];
        saveSessions(next);
        return next;
      });
      setMessagesBySession((prev) => ({ ...prev, [newId]: [] }));
      setActiveSessionId(newId);
      localId = newId;
    }

    const sessionLocalId = localId;

    // Add user message
    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content,
      toolCalls: [],
      createdAt: Date.now(),
    };
    updateMessages(sessionLocalId, (prev) => [...prev, userMessage]);

    // Update session title from first message
    setSessions((prev) => {
      const session = prev.find((s) => s.id === sessionLocalId);
      if (session && session.title === 'New chat') {
        const next = prev.map((s) =>
          s.id === sessionLocalId
            ? { ...s, title: getTitleFromContent(content), updatedAt: Date.now() }
            : s
        );
        saveSessions(next);
        return next;
      }
      return prev;
    });

    setInputValue('');
    setIsLoading(true);

    // Add assistant placeholder
    const assistantId = generateId();
    const assistantMessage: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      toolCalls: [],
      createdAt: Date.now(),
    };
    updateMessages(sessionLocalId, (prev) => [...prev, assistantMessage]);
    setStreamingMessageId(assistantId);

    try {
      // Ensure backend session exists
      let backendSessionId =
        sessions.find((s) => s.id === sessionLocalId)?.sessionId ?? '';
      if (!backendSessionId) {
        backendSessionId = await createSession();
        setSessions((prev) => {
          const next = prev.map((s) =>
            s.id === sessionLocalId ? { ...s, sessionId: backendSessionId } : s
          );
          saveSessions(next);
          return next;
        });
      }

      await streamChat(backendSessionId, content, (event) => {
        if (event.type === 'token') {
          // When tokens start arriving, any running tools are done
          updateMessages(sessionLocalId, (prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    content: m.content + event.data,
                    toolCalls: m.toolCalls.map((t) =>
                      t.status === 'running' ? { ...t, status: 'done' as const } : t
                    ),
                  }
                : m
            )
          );
        } else if (event.type === 'tool') {
          const toolCall: ToolCall = {
            id: generateId(),
            name: event.data.name,
            status: 'running',
          };
          updateMessages(sessionLocalId, (prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, toolCalls: [...m.toolCalls, toolCall] }
                : m
            )
          );
        } else if (event.type === 'done') {
          updateMessages(sessionLocalId, (prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    toolCalls: m.toolCalls.map((t) =>
                      t.status === 'running' ? { ...t, status: 'done' as const } : t
                    ),
                  }
                : m
            )
          );
          setSessions((prev) => {
            const next = prev.map((s) =>
              s.id === sessionLocalId ? { ...s, updatedAt: Date.now() } : s
            );
            saveSessions(next);
            return next;
          });
        } else if (event.type === 'error') {
          updateMessages(sessionLocalId, (prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    content: m.content || `Error: ${event.data}`,
                    toolCalls: m.toolCalls.map((t) =>
                      t.status === 'running' ? { ...t, status: 'error' as const } : t
                    ),
                  }
                : m
            )
          );
        }
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error occurred';
      updateMessages(sessionLocalId, (prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? {
                ...m,
                content: m.content || `Failed to get response: ${message}`,
                toolCalls: m.toolCalls.map((t) =>
                  t.status === 'running' ? { ...t, status: 'error' as const } : t
                ),
              }
            : m
        )
      );
    } finally {
      setIsLoading(false);
      setStreamingMessageId(null);
    }
  }, [inputValue, isLoading, activeSessionId, sessions, updateMessages]);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#1a1a1a] text-zinc-100">
      {/* Sidebar */}
      <div
        className={`shrink-0 transition-all duration-200 ease-in-out overflow-hidden ${
          sidebarOpen ? 'w-[260px]' : 'w-0'
        }`}
        aria-hidden={!sidebarOpen}
      >
        <div className="w-[260px] h-full">
          <Sidebar
            sessions={sessions}
            activeSessionId={activeSessionId}
            onSelectSession={handleSelectSession}
            onNewChat={handleNewChat}
            onDeleteSession={handleDeleteSession}
          />
        </div>
      </div>

      {/* Main content */}
      <main className="flex flex-col flex-1 min-w-0 min-h-0">
        {/* Top bar */}
        <header className="flex items-center gap-2 px-4 py-3 shrink-0 border-b border-white/[0.06]">
          <button
            onClick={() => setSidebarOpen((v) => !v)}
            aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
            aria-expanded={sidebarOpen}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-white/8 transition-colors duration-100"
          >
            {sidebarOpen
              ? <CaretLeft size={18} aria-hidden="true" />
              : <CaretRight size={18} aria-hidden="true" />
            }
          </button>
          <div className="flex-1 flex items-center justify-center">
            <span className="text-sm font-medium text-zinc-400 truncate max-w-xs">
              {activeSessionId
                ? sessions.find((s) => s.id === activeSessionId)?.title || 'New chat'
                : 'AgenticRAG'}
            </span>
          </div>
          <button
            onClick={handleNewChat}
            aria-label="New chat"
            className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-white/8 transition-colors duration-100"
          >
            <PencilSimpleLineIcon size={18} aria-hidden="true" />
          </button>
        </header>

        {/* Chat area */}
        <div className="relative flex flex-col flex-1 min-h-0">
          <ChatArea
            messages={activeMessages}
            streamingMessageId={streamingMessageId}
            isLoading={isLoading}
            isStreaming={streamingMessageId !== null}
            inputValue={inputValue}
            onInputChange={setInputValue}
            onSubmit={handleSubmit}
          />
        </div>
      </main>
    </div>
  );
}
