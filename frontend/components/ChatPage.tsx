"use client";

import {useState, useCallback, useEffect, useRef} from "react";
import { signOut } from "@/lib/api";
import {CaretLeft} from "@phosphor-icons/react/dist/ssr/CaretLeft";
import {CaretRight} from "@phosphor-icons/react/dist/ssr/CaretRight";
import {PencilSimpleLineIcon} from "@phosphor-icons/react/dist/ssr/PencilSimpleLine";
import {SignOut} from "@phosphor-icons/react/dist/ssr/SignOut";
import {Brain} from "@phosphor-icons/react/dist/ssr/Brain";
import {useExternalStoreRuntime, AssistantRuntimeProvider} from "@assistant-ui/react";
import Image from "next/image";
import Sidebar from "@/components/Sidebar";
import ChatArea from "@/components/ChatArea";
import MemoryPanel from "@/components/MemoryPanel";
import {
  backendSessionExists,
  createBackendSession,
  deleteBackendSession,
  restoreBackendSession,
  streamChat,
  fetchSessions,
  createChatSession,
  updateChatSession,
  deleteChatSession,
  fetchMessages,
  saveMessages,
} from "@/lib/api";
import {convertMessage} from "@/lib/chatRuntime";
import {
  appendReasoningPart,
  appendSourceParts,
  appendTextPart,
  appendToolCallPart,
  buildAssistantPartsFromLegacy,
  getDefaultAssistantStatus,
  markRunningToolParts,
} from "@/lib/messageParts";
import type {Session, Message, ToolCall, ThinkingEntry, Project, RetrievalSource} from "@/lib/types";

interface ChatPageProps {
  initialSessions?: Session[];
  initialProjects?: Project[];
  user: {
    name?: string | null;
    email?: string | null;
    image?: string | null;
  };
}

function generateLocalId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function extractComposerText(message: { content: unknown }): string {
  if (typeof message.content === "string") return message.content;
  if (!Array.isArray(message.content)) return "";

  return message.content
    .filter(
      (
        part
      ): part is {
        type: "text";
        text: string;
      } =>
        typeof part === "object" &&
        part !== null &&
        "type" in part &&
        "text" in part &&
        part.type === "text" &&
        typeof part.text === "string"
    )
    .map((part) => part.text)
    .join("\n");
}

export default function ChatPage({initialSessions = [], initialProjects = [], user}: ChatPageProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [memoryOpen, setMemoryOpen] = useState(false);
  const [sessions, setSessions] = useState<Session[]>(initialSessions);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(
    initialSessions.length > 0 ? initialSessions[0].id : null
  );
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
        const newSession = await createChatSession();
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
    const persistedMessages = messagesBySession[currentSessionId] ?? [];

    let backendSessionId =
      sessions.find((s) => s.id === currentSessionId)?.backendSessionId ??
      null;
    if (!backendSessionId) {
      try {
        backendSessionId = await createBackendSession();
        setSessions((prev) =>
          prev.map((s) =>
            s.id === currentSessionId ? {...s, backendSessionId} : s
          )
        );
        updateChatSession(currentSessionId, {backendSessionId}).catch(
          console.error
        );
      } catch (err) {
        console.error("Failed to create backend session:", err);
        return;
      }
    } else {
      const exists = await backendSessionExists(backendSessionId);
      if (!exists) {
        await restoreBackendSession(
          backendSessionId,
          persistedMessages.map((message) => ({
            role: message.role,
            content: message.content,
          }))
        );
      }
    }

    // Add user message to state
    const userMessage: Message = {
      id: generateLocalId(),
      role: "user",
      content,
      parts: [{ type: "text", text: content }],
      toolCalls: [],
      thinkingEntries: [],
      sources: [],
      metadata: {},
      createdAt: new Date().toISOString(),
    };
    updateMessages(currentSessionId, (prev) => [...prev, userMessage]);

    setInputValue("");
    setIsLoading(true);

    // Add assistant placeholder
    const assistantId = generateLocalId();
    const assistantMessage: Message = {
      id: assistantId,
      role: "assistant",
      content: "",
      parts: [],
      toolCalls: [],
      thinkingEntries: [],
      sources: [],
      status: { type: "running" },
      metadata: {},
      createdAt: new Date().toISOString(),
    };
    updateMessages(currentSessionId, (prev) => [...prev, assistantMessage]);
    setStreamingMessageId(assistantId);

    try {
      // Accumulate final content for DB save
      let finalContent = "";
      let finalToolCalls: ToolCall[] = [];
      let finalThinkingEntries: ThinkingEntry[] = [];
      let finalSources: RetrievalSource[] = [];
      let finalParts = buildAssistantPartsFromLegacy(assistantMessage);
      let finalStatus = getDefaultAssistantStatus(assistantMessage) ?? { type: "running" as const };

      const markToolsDone = (entries: ThinkingEntry[]): ThinkingEntry[] =>
        entries.map((e) =>
          e.type === "tool" && e.toolCall.status === "running"
            ? { ...e, toolCall: { ...e.toolCall, status: "done" as const } }
            : e
        );
      const markToolsError = (entries: ThinkingEntry[]): ThinkingEntry[] =>
        entries.map((e) =>
          e.type === "tool" && e.toolCall.status === "running"
            ? { ...e, toolCall: { ...e.toolCall, status: "error" as const } }
            : e
        );

      await streamChat(backendSessionId, content, (event) => {
        if (event.type === "token") {
          finalContent += event.data;
          finalToolCalls = finalToolCalls.map((t) =>
            t.status === "running" ? { ...t, status: "done" as const } : t
          );
          finalThinkingEntries = markToolsDone(finalThinkingEntries);
          finalParts = appendTextPart(markRunningToolParts(finalParts, "done"), event.data);
          finalStatus = { type: "running" };
          updateMessages(currentSessionId, (prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    content: m.content + event.data,
                    parts: appendTextPart(markRunningToolParts(m.parts, "done"), event.data),
                    toolCalls: m.toolCalls.map((t) =>
                      t.status === "running"
                        ? {...t, status: "done" as const}
                        : t
                    ),
                    thinkingEntries: markToolsDone(m.thinkingEntries),
                    status: { type: "running" },
                  }
                : m
            )
          );
        } else if (event.type === "thinking") {
          finalThinkingEntries = [...finalThinkingEntries, { type: "text" as const, content: event.data.content }];
          finalParts = appendReasoningPart(finalParts, event.data.content);
          updateMessages(currentSessionId, (prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    parts: appendReasoningPart(m.parts, event.data.content),
                    thinkingEntries: [...m.thinkingEntries, { type: "text" as const, content: event.data.content }],
                    thinkingStartedAt: m.thinkingStartedAt ?? Date.now(),
                  }
                : m
            )
          );
        } else if (event.type === "tool") {
          const toolCall: ToolCall = {
            id: generateLocalId(),
            name: event.data.name,
            args: event.data.args,
            status: "running",
          };
          finalToolCalls.push(toolCall);
          finalThinkingEntries = [...finalThinkingEntries, { type: "tool" as const, toolCall }];
          finalParts = appendToolCallPart(finalParts, toolCall);
          updateMessages(currentSessionId, (prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    parts: appendToolCallPart(m.parts, toolCall),
                    toolCalls: [...m.toolCalls, toolCall],
                    thinkingEntries: [...m.thinkingEntries, { type: "tool" as const, toolCall }],
                    thinkingStartedAt: m.thinkingStartedAt ?? Date.now(),
                  }
                : m
            )
          );
        } else if (event.type === "retrieval") {
          finalSources = event.data.sources;
          finalParts = appendSourceParts(finalParts, event.data.sources);
          updateMessages(currentSessionId, (prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    parts: appendSourceParts(m.parts, event.data.sources),
                    sources: event.data.sources,
                  }
                : m
            )
          );
        } else if (event.type === "done") {
          // Mark remaining running tools as done
          finalToolCalls = finalToolCalls.map((t) =>
            t.status === "running" ? {...t, status: "done" as const} : t
          );
          finalThinkingEntries = markToolsDone(finalThinkingEntries);
          finalParts = markRunningToolParts(finalParts, "done");
          finalStatus = { type: "complete", reason: "stop" };
          updateMessages(currentSessionId, (prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    parts: markRunningToolParts(m.parts, "done"),
                    toolCalls: m.toolCalls.map((t) =>
                      t.status === "running"
                        ? {...t, status: "done" as const}
                        : t
                    ),
                    thinkingEntries: markToolsDone(m.thinkingEntries),
                    status: { type: "complete", reason: "stop" },
                    thinkingDuration: m.thinkingStartedAt
                      ? (Date.now() - m.thinkingStartedAt) / 1000
                      : undefined,
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
          if (sessions.find((s) => s.id === currentSessionId)?.title === "New chat") {
            window.setTimeout(() => {
              fetchSessions().then(setSessions).catch(console.error);
            }, 1500);
          }
        } else if (event.type === "error") {
          finalToolCalls = finalToolCalls.map((t) =>
            t.status === "running" ? { ...t, status: "error" as const } : t
          );
          finalThinkingEntries = markToolsError(finalThinkingEntries);
          finalParts = markRunningToolParts(finalParts, "error", event.data);
          finalStatus = { type: "incomplete", reason: "error", error: event.data };
          updateMessages(currentSessionId, (prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    content: m.content || `Error: ${event.data}`,
                    parts: markRunningToolParts(m.parts, "error", event.data),
                    toolCalls: m.toolCalls.map((t) =>
                      t.status === "running"
                        ? {...t, status: "error" as const}
                        : t
                    ),
                    thinkingEntries: markToolsError(m.thinkingEntries),
                    status: { type: "incomplete", reason: "error", error: event.data },
                  }
                : m
            )
          );
        }
      });

      // Save both messages to DB after streaming completes
      // Replace local IDs with DB IDs so metadata PATCH works
      saveMessages(currentSessionId, [
        {role: "user", content, parts: [{ type: "text", text: content }], toolCalls: []},
        {
          role: "assistant",
          content: finalContent,
          parts: finalParts,
          toolCalls: finalToolCalls,
          thinkingEntries: finalThinkingEntries,
          sources: finalSources,
          status: finalStatus,
        },
      ]).then((saved) => {
        if (saved.length === 2) {
          updateMessages(currentSessionId, (prev) =>
            prev.map((m) => {
              if (m.id === userMessage.id) return { ...m, dbId: saved[0].id };
              if (m.id === assistantId) return { ...m, dbId: saved[1].id };
              return m;
            })
          );
        }
      }).catch(console.error);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Unknown error occurred";
      updateMessages(currentSessionId, (prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? {
                ...m,
                content: m.content || `Failed to get response: ${message}`,
                parts: markRunningToolParts(m.parts, "error", message),
                toolCalls: m.toolCalls.map((t) =>
                  t.status === "running" ? {...t, status: "error" as const} : t
                ),
                thinkingEntries: m.thinkingEntries.map((e) =>
                  e.type === "tool" && e.toolCall.status === "running"
                    ? { ...e, toolCall: { ...e.toolCall, status: "error" as const } }
                    : e
                ),
                status: { type: "incomplete", reason: "error", error: message },
              }
            : m
        )
      );
    } finally {
      setIsLoading(false);
      setStreamingMessageId(null);
    }
  }, [inputValue, isLoading, activeSessionId, sessions, messagesBySession, updateMessages]);

  // ─── assistant-ui ExternalStoreRuntime ───
  // Bridge our message state to assistant-ui's runtime so its primitives
  // (Thread, ActionBar, etc.) can read from our existing state.
  const runtime = useExternalStoreRuntime({
    messages: activeMessages,
    isRunning: isLoading,
    convertMessage,
    onNew: async (message) => {
      const text = extractComposerText(message);
      if (text) {
        setInputValue(text);
        // Use a microtask so inputValue state updates before handleSubmit reads it
        await Promise.resolve();
        handleSubmit();
      }
    },
  });

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
            initialProjects={initialProjects}
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
              onClick={() => setMemoryOpen(true)}
              aria-label='View memory'
              title='Memory'
              className='p-1.5 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-white/8 transition-colors duration-100'>
              <Brain size={18} weight="duotone" aria-hidden='true' />
            </button>
            <button
              onClick={handleNewChat}
              aria-label='New chat'
              className='p-1.5 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-white/8 transition-colors duration-100'>
              <PencilSimpleLineIcon size={18} aria-hidden='true' />
            </button>

            {/* User menu */}
            <div className='flex items-center gap-1 ml-2 pl-2 border-l border-white/6'>
              {user.image ? (
                <Image
                  src={user.image}
                  alt={user.name || "User"}
                  className='h-6 w-6 rounded-full'
                  width={24}
                  height={24}
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
        <AssistantRuntimeProvider runtime={runtime}>
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
        </AssistantRuntimeProvider>
      </main>

      <MemoryPanel open={memoryOpen} onClose={() => setMemoryOpen(false)} />
    </div>
  );
}
