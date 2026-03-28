"use client";

import {useState, useCallback, useEffect, useRef} from "react";
import {signOut} from "next-auth/react";
import {CaretLeft} from "@phosphor-icons/react/dist/ssr/CaretLeft";
import {CaretRight} from "@phosphor-icons/react/dist/ssr/CaretRight";
import {PencilSimpleLineIcon} from "@phosphor-icons/react/dist/ssr/PencilSimpleLine";
import {SignOut} from "@phosphor-icons/react/dist/ssr/SignOut";
import Sidebar from "@/components/Sidebar";
import ChatArea from "@/components/ChatArea";
import {
  createBackendSession,
  deleteBackendSession,
  streamChat,
  fetchSessions,
  createChatSession,
  updateChatSession,
  deleteChatSession,
  fetchMessages,
  saveMessages,
} from "@/lib/api";
import type {Session, Message, ToolCall} from "@/lib/types";

interface ChatPageProps {
  user: {
    name?: string | null;
    email?: string | null;
    image?: string | null;
  };
}

function generateLocalId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function getTitleFromContent(content: string): string {
  const trimmed = content.trim();
  if (trimmed.length <= 40) return trimmed;
  return trimmed.slice(0, 40).trim() + "\u2026";
}

export default function ChatPage({user}: ChatPageProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messagesBySession, setMessagesBySession] = useState<
    Record<string, Message[]>
  >({});
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(
    null
  );

  // Track which sessions have had their messages loaded from DB
  const loadedSessionsRef = useRef<Set<string>>(new Set());

  // Load sessions from DB on mount
  useEffect(() => {
    async function getSessions() {
      try {
        const response = await fetchSessions();
        setSessions(response);
        if (response.length > 0) {
          setActiveSessionId(response[0].id);
        }
      } catch (error) {
        console.error("Error getting sessions:", error);
      }
    }
    getSessions();
  }, []);

  // Load messages when switching to a session we haven't fetched yet
  useEffect(() => {
    if (!activeSessionId) return;
    if (loadedSessionsRef.current.has(activeSessionId)) return;

    loadedSessionsRef.current.add(activeSessionId);
    fetchMessages(activeSessionId)
      .then((msgs) => {
        setMessagesBySession((prev) => ({...prev, [activeSessionId]: msgs}));
      })
      .catch(console.error);
  }, [activeSessionId]);

  const activeMessages: Message[] = activeSessionId
    ? messagesBySession[activeSessionId] ?? []
    : [];

  // Update messages in React state (no localStorage, DB save happens separately)
  const updateMessages = useCallback(
    (sessionId: string, updater: (prev: Message[]) => Message[]) => {
      setMessagesBySession((prev) => {
        const current = prev[sessionId] ?? [];
        const next = updater(current);
        return {...prev, [sessionId]: next};
      });
    },
    []
  );

  const handleNewChat = useCallback(async () => {
    // If current session is already empty, just stay on it
    if (activeSessionId) {
      const currentMessages = messagesBySession[activeSessionId] ?? [];
      if (currentMessages.length === 0) return;
    }

    try {
      const newSession = await createChatSession();
      setSessions((prev) => [newSession, ...prev]);
      setMessagesBySession((prev) => ({...prev, [newSession.id]: []}));
      loadedSessionsRef.current.add(newSession.id);
      setActiveSessionId(newSession.id);
      setInputValue("");
    } catch (err) {
      console.error("Failed to create session:", err);
    }
  }, [activeSessionId, messagesBySession]);

  const handleSelectSession = useCallback((id: string) => {
    setActiveSessionId(id);
    setInputValue("");
  }, []);

  const handleDeleteSession = useCallback(
    async (id: string) => {
      try {
        const {backendSessionId} = await deleteChatSession(id);
        // Also clean up Redis session
        if (backendSessionId) {
          deleteBackendSession(backendSessionId).catch(() => {});
        }
      } catch {
        // ignore errors on delete
      }

      setSessions((prev) => {
        const next = prev.filter((s) => s.id !== id);
        return next;
      });

      setMessagesBySession((prev) => {
        const next = {...prev};
        delete next[id];
        return next;
      });
      loadedSessionsRef.current.delete(id);

      setActiveSessionId((prev) => {
        if (prev === id) {
          const remaining = sessions.filter((s) => s.id !== id);
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

    let sessionId = activeSessionId;

    // Create a new DB session if none is active
    if (!sessionId) {
      try {
        const newSession = await createChatSession(
          getTitleFromContent(content)
        );
        setSessions((prev) => [newSession, ...prev]);
        setMessagesBySession((prev) => ({...prev, [newSession.id]: []}));
        loadedSessionsRef.current.add(newSession.id);
        setActiveSessionId(newSession.id);
        sessionId = newSession.id;
      } catch (err) {
        console.error("Failed to create session:", err);
        return;
      }
    }

    const currentSessionId = sessionId;

    // Add user message to state
    const userMessage: Message = {
      id: generateLocalId(),
      role: "user",
      content,
      toolCalls: [],
      createdAt: new Date().toISOString(),
    };
    updateMessages(currentSessionId, (prev) => [...prev, userMessage]);

    // Update title if it's still "New chat"
    const session = sessions.find((s) => s.id === currentSessionId);
    if (session && session.title === "New chat") {
      const newTitle = getTitleFromContent(content);
      setSessions((prev) =>
        prev.map((s) =>
          s.id === currentSessionId ? {...s, title: newTitle} : s
        )
      );
      updateChatSession(currentSessionId, {title: newTitle}).catch(
        console.error
      );
    }

    setInputValue("");
    setIsLoading(true);

    // Add assistant placeholder
    const assistantId = generateLocalId();
    const assistantMessage: Message = {
      id: assistantId,
      role: "assistant",
      content: "",
      toolCalls: [],
      createdAt: new Date().toISOString(),
    };
    updateMessages(currentSessionId, (prev) => [...prev, assistantMessage]);
    setStreamingMessageId(assistantId);

    try {
      // Ensure backend Redis session exists
      let backendSessionId =
        sessions.find((s) => s.id === currentSessionId)?.backendSessionId ??
        null;
      if (!backendSessionId) {
        backendSessionId = await createBackendSession();
        setSessions((prev) =>
          prev.map((s) =>
            s.id === currentSessionId ? {...s, backendSessionId} : s
          )
        );
        updateChatSession(currentSessionId, {backendSessionId}).catch(
          console.error
        );
      }

      // Accumulate final content for DB save
      let finalContent = "";
      let finalToolCalls: ToolCall[] = [];

      await streamChat(backendSessionId, content, (event) => {
        if (event.type === "token") {
          finalContent += event.data;
          updateMessages(currentSessionId, (prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    content: m.content + event.data,
                    toolCalls: m.toolCalls.map((t) =>
                      t.status === "running"
                        ? {...t, status: "done" as const}
                        : t
                    ),
                  }
                : m
            )
          );
        } else if (event.type === "tool") {
          const toolCall: ToolCall = {
            id: generateLocalId(),
            name: event.data.name,
            status: "running",
          };
          finalToolCalls.push(toolCall);
          updateMessages(currentSessionId, (prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {...m, toolCalls: [...m.toolCalls, toolCall]}
                : m
            )
          );
        } else if (event.type === "done") {
          // Mark remaining running tools as done
          finalToolCalls = finalToolCalls.map((t) =>
            t.status === "running" ? {...t, status: "done" as const} : t
          );
          updateMessages(currentSessionId, (prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    toolCalls: m.toolCalls.map((t) =>
                      t.status === "running"
                        ? {...t, status: "done" as const}
                        : t
                    ),
                  }
                : m
            )
          );
          // Bump session to top
          setSessions((prev) => {
            const updated = prev.map((s) =>
              s.id === currentSessionId
                ? {...s, updatedAt: new Date().toISOString()}
                : s
            );
            return updated;
          });
        } else if (event.type === "error") {
          updateMessages(currentSessionId, (prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    content: m.content || `Error: ${event.data}`,
                    toolCalls: m.toolCalls.map((t) =>
                      t.status === "running"
                        ? {...t, status: "error" as const}
                        : t
                    ),
                  }
                : m
            )
          );
        }
      });

      // Save both messages to DB after streaming completes
      saveMessages(currentSessionId, [
        {role: "user", content, toolCalls: []},
        {role: "assistant", content: finalContent, toolCalls: finalToolCalls},
      ]).catch(console.error);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Unknown error occurred";
      updateMessages(currentSessionId, (prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? {
                ...m,
                content: m.content || `Failed to get response: ${message}`,
                toolCalls: m.toolCalls.map((t) =>
                  t.status === "running" ? {...t, status: "error" as const} : t
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
    <div className='flex h-screen w-screen overflow-hidden bg-[#1a1a1a] text-zinc-100'>
      {/* Sidebar */}
      <div
        className={`shrink-0 transition-all duration-200 ease-in-out overflow-hidden ${
          sidebarOpen ? "w-[260px]" : "w-0"
        }`}
        aria-hidden={!sidebarOpen}>
        <div className='w-[260px] h-full'>
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
      <main className='flex flex-col flex-1 min-w-0 min-h-0'>
        {/* Top bar */}
        <header className='flex items-center gap-2 px-4 py-3 shrink-0 border-b border-white/6'>
          <button
            onClick={() => setSidebarOpen((v) => !v)}
            aria-label={sidebarOpen ? "Close sidebar" : "Open sidebar"}
            aria-expanded={sidebarOpen}
            className='p-1.5 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-white/8 transition-colors duration-100'>
            {sidebarOpen ? (
              <CaretLeft size={18} aria-hidden='true' />
            ) : (
              <CaretRight size={18} aria-hidden='true' />
            )}
          </button>
          <div className='flex-1 flex items-center justify-center'>
            <span className='text-sm font-medium text-zinc-400 truncate max-w-xs'>
              {activeSessionId
                ? sessions.find((s) => s.id === activeSessionId)?.title ||
                  "New chat"
                : "AgenticRAG"}
            </span>
          </div>
          <div className='flex items-center gap-1'>
            <button
              onClick={handleNewChat}
              aria-label='New chat'
              className='p-1.5 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-white/8 transition-colors duration-100'>
              <PencilSimpleLineIcon size={18} aria-hidden='true' />
            </button>

            {/* User menu */}
            <div className='flex items-center gap-1 ml-2 pl-2 border-l border-white/6'>
              {user.image ? (
                <img
                  src={user.image}
                  alt={user.name || "User"}
                  className='w-6 h-6 rounded-full'
                  referrerPolicy='no-referrer'
                />
              ) : (
                <div className='w-6 h-6 rounded-full bg-violet-600/30 flex items-center justify-center text-xs font-medium text-violet-300'>
                  {user.name?.charAt(0) || user.email?.charAt(0) || "?"}
                </div>
              )}
              <button
                onClick={() => signOut()}
                aria-label='Sign out'
                className='p-1.5 rounded-lg text-zinc-500 hover:text-zinc-200 hover:bg-white/8 transition-colors duration-100'>
                <SignOut size={16} aria-hidden='true' />
              </button>
            </div>
          </div>
        </header>

        {/* Chat area */}
        <div className='relative flex flex-col flex-1 min-h-0'>
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
