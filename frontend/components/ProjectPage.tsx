"use client";

import {useState, useCallback, useEffect, useRef} from "react";
import {signOut} from "next-auth/react";
import {CaretLeft} from "@phosphor-icons/react/dist/ssr/CaretLeft";
import {CaretRight} from "@phosphor-icons/react/dist/ssr/CaretRight";
import {ArrowLeft} from "@phosphor-icons/react/dist/ssr/ArrowLeft";
import {SignOut} from "@phosphor-icons/react/dist/ssr/SignOut";
import ProjectSidebar from "@/components/ProjectSidebar";
import ChatArea from "@/components/ChatArea";
import {
  fetchAgents,
  uploadDocument,
  deleteDocument,
  pollDocumentStatus,
  createProjectSession,
  deleteProjectSession,
  streamProjectChat,
  fetchMessages,
  saveMessages,
  updateChatSession,
  deleteChatSession,
} from "@/lib/api";
import type {Project, Session, Message, AgentInfo, ToolCall, ThinkingEntry} from "@/lib/types";
import Link from "next/link";

interface ProjectPageProps {
  initialProject: Project;
  initialSessions: Session[];
  projectId: string;
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

export default function ProjectPage({
  initialProject,
  initialSessions = [],
  projectId,
  user,
}: ProjectPageProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [project, setProject] = useState<Project>(initialProject);
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  // Session management (mirrors ChatPage pattern)
  const [sessions, setSessions] = useState<Session[]>(initialSessions);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(
    initialSessions.length > 0 ? initialSessions[0].id : null
  );
  const [messagesBySession, setMessagesBySession] = useState<
    Record<string, Message[]>
  >({});

  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(
    null
  );

  const loadedSessionsRef = useRef<Set<string>>(new Set());

  // Load agents on mount (project and sessions are already loaded via SSR)
  useEffect(() => {
    fetchAgents().then(setAgents).catch(console.error);
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

  // Poll processing documents
  useEffect(() => {
    if (!project) return;
    const processingDocs = project.documents.filter(
      (d) => d.status === "processing" || d.status === "uploading"
    );
    if (processingDocs.length === 0) return;

    const interval = setInterval(async () => {
      let changed = false;
      const updatedDocs = await Promise.all(
        project.documents.map(async (doc) => {
          if (doc.status !== "processing" && doc.status !== "uploading")
            return doc;
          try {
            const status = await pollDocumentStatus(projectId, doc.id);
            if (status.status !== doc.status) {
              changed = true;
              return {
                ...doc,
                status: status.status as typeof doc.status,
                chunkCount: status.chunkCount,
                chunkStrategy: status.chunkStrategy,
                errorMessage: status.errorMessage,
              };
            }
          } catch {
            // ignore
          }
          return doc;
        })
      );
      if (changed) {
        setProject((prev) => (prev ? {...prev, documents: updatedDocs} : prev));
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [project, projectId]);

  const handleUploadFile = useCallback(
    async (file: File) => {
      if (!project) return;
      setIsUploading(true);
      try {
        const doc = await uploadDocument(projectId, file);
        setProject((prev) =>
          prev ? {...prev, documents: [doc, ...prev.documents]} : prev
        );
      } catch (err) {
        console.error("Upload failed:", err);
      } finally {
        setIsUploading(false);
      }
    },
    [project, projectId]
  );

  const handleDeleteDocument = useCallback(
    async (docId: string) => {
      try {
        await deleteDocument(projectId, docId);
        setProject((prev) =>
          prev
            ? {...prev, documents: prev.documents.filter((d) => d.id !== docId)}
            : prev
        );
      } catch (err) {
        console.error("Delete failed:", err);
      }
    },
    [projectId]
  );

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
    // If current session is already empty, stay on it
    if (activeSessionId) {
      const currentMessages = messagesBySession[activeSessionId] ?? [];
      if (currentMessages.length === 0) return;
    }

    try {
      const newSession = await createProjectSession(projectId);
      setSessions((prev) => [newSession, ...prev]);
      setMessagesBySession((prev) => ({...prev, [newSession.id]: []}));
      loadedSessionsRef.current.add(newSession.id);
      setActiveSessionId(newSession.id);
      setInputValue("");
    } catch (err) {
      console.error("Failed to create session:", err);
    }
  }, [activeSessionId, messagesBySession, projectId]);

  const handleSelectSession = useCallback((id: string) => {
    setActiveSessionId(id);
    setInputValue("");
  }, []);

  const handleDeleteSession = useCallback(
    async (id: string) => {
      const session = sessions.find((s) => s.id === id);
      try {
        await deleteChatSession(id);
        if (session?.backendSessionId) {
          deleteProjectSession(projectId, session.backendSessionId).catch(
            () => {}
          );
        }
      } catch {
        // ignore
      }

      setSessions((prev) => prev.filter((s) => s.id !== id));
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
    [sessions, projectId]
  );

  const handleSubmit = useCallback(async () => {
    const content = inputValue.trim();
    if (!content || isLoading || !project) return;

    let sessionId = activeSessionId;
    let currentSession = sessions.find((s) => s.id === sessionId);

    // Create a new project session if none is active
    if (!sessionId) {
      try {
        const newSession = await createProjectSession(projectId);
        setSessions((prev) => [newSession, ...prev]);
        setMessagesBySession((prev) => ({...prev, [newSession.id]: []}));
        loadedSessionsRef.current.add(newSession.id);
        setActiveSessionId(newSession.id);
        sessionId = newSession.id;
        currentSession = newSession;
      } catch (err) {
        console.error("Failed to create project session:", err);
        return;
      }
    }

    const currentSessionId = sessionId;
    const backendSessionId = currentSession?.backendSessionId;

    if (!backendSessionId) {
      console.error("No backend session ID found");
      return;
    }

    // Add user message
    const userMessage: Message = {
      id: generateLocalId(),
      role: "user",
      content,
      toolCalls: [],
      thinkingEntries: [],
      metadata: {},
      createdAt: new Date().toISOString(),
    };
    updateMessages(currentSessionId, (prev) => [...prev, userMessage]);

    // Update title if it's still "New chat"
    if (currentSession && currentSession.title === "New chat") {
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
      thinkingEntries: [],
      metadata: {},
      createdAt: new Date().toISOString(),
    };
    updateMessages(currentSessionId, (prev) => [...prev, assistantMessage]);
    setStreamingMessageId(assistantId);

    try {
      let finalContent = "";
      let detectedAgent = "";

      await streamProjectChat(
        projectId,
        backendSessionId,
        content,
        (event) => {
          const markToolsDone = (entries: ThinkingEntry[]): ThinkingEntry[] =>
            entries.map((e) =>
              e.type === "tool" && e.toolCall.status === "running"
                ? { ...e, toolCall: { ...e.toolCall, status: "done" as const } }
                : e
            );

          if (event.type === "token") {
            finalContent += event.data;
            updateMessages(currentSessionId, (prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? {...m, content: m.content + event.data}
                  : m
              )
            );
          } else if (event.type === "thinking") {
            updateMessages(currentSessionId, (prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? {
                      ...m,
                      thinkingEntries: [...m.thinkingEntries, { type: "text" as const, content: event.data.content }],
                      thinkingStartedAt: m.thinkingStartedAt ?? Date.now(),
                    }
                  : m
              )
            );
          } else if (event.type === "agent") {
            detectedAgent = event.data.name;
            const agentTool: ToolCall = {
              id: generateLocalId(),
              name: `${event.data.name} agent`,
              args: { description: event.data.description },
              status: "running",
            };
            updateMessages(currentSessionId, (prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? {
                      ...m,
                      agentName: event.data.name,
                      toolCalls: [...m.toolCalls, agentTool],
                      thinkingEntries: [...m.thinkingEntries, { type: "tool" as const, toolCall: agentTool }],
                      thinkingStartedAt: m.thinkingStartedAt ?? Date.now(),
                    }
                  : m
              )
            );
          } else if (event.type === "retrieval") {
            const retrievalTool: ToolCall = {
              id: generateLocalId(),
              name: `searched ${event.data.count} passages`,
              status: "done",
            };
            updateMessages(currentSessionId, (prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? {
                      ...m,
                      toolCalls: m.toolCalls
                        .map((t) =>
                          t.status === "running"
                            ? {...t, status: "done" as const}
                            : t
                        )
                        .concat(retrievalTool),
                      thinkingEntries: markToolsDone(m.thinkingEntries)
                        .concat({ type: "tool" as const, toolCall: retrievalTool }),
                    }
                  : m
              )
            );
          } else if (event.type === "done") {
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
                      thinkingEntries: markToolsDone(m.thinkingEntries),
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
                      thinkingEntries: m.thinkingEntries.map((e) =>
                        e.type === "tool" && e.toolCall.status === "running"
                          ? { ...e, toolCall: { ...e.toolCall, status: "error" as const } }
                          : e
                      ),
                    }
                  : m
              )
            );
          }
        },
        selectedAgent
      );

      // Save messages to DB (persist agentName in metadata for session restore)
      // Replace local IDs with DB IDs so PATCH for quiz state works
      saveMessages(currentSessionId, [
        {role: "user", content, toolCalls: []},
        {
          role: "assistant",
          content: finalContent,
          toolCalls: [],
          metadata: detectedAgent ? {agentName: detectedAgent} : undefined,
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
      const message = err instanceof Error ? err.message : "Unknown error";
      updateMessages(currentSessionId, (prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? {
                ...m,
                content: m.content || `Failed to get response: ${message}`,
                toolCalls: m.toolCalls.map((t) =>
                  t.status === "running" ? {...t, status: "error" as const} : t
                ),
                thinkingEntries: m.thinkingEntries.map((e) =>
                  e.type === "tool" && e.toolCall.status === "running"
                    ? { ...e, toolCall: { ...e.toolCall, status: "error" as const } }
                    : e
                ),
              }
            : m
        )
      );
    } finally {
      setIsLoading(false);
      setStreamingMessageId(null);
    }
  }, [
    inputValue,
    isLoading,
    project,
    projectId,
    selectedAgent,
    activeSessionId,
    sessions,
    updateMessages,
  ]);



  return (
    <div className='flex h-screen w-screen overflow-hidden bg-[#1a1a1a] text-zinc-100'>
      {/* Project sidebar */}
      <div
        className={`shrink-0 transition-all duration-200 ease-in-out overflow-hidden ${
          sidebarOpen ? "w-[280px]" : "w-0"
        }`}
        aria-hidden={!sidebarOpen}>
        <div className='w-[280px] h-full'>
          <ProjectSidebar
            project={project}
            agents={agents}
            selectedAgent={selectedAgent}
            onSelectAgent={setSelectedAgent}
            onUploadFile={handleUploadFile}
            onDeleteDocument={handleDeleteDocument}
            isUploading={isUploading}
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
            className='p-1.5 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-white/8 transition-colors duration-100'>
            {sidebarOpen ? (
              <CaretLeft size={18} aria-hidden='true' />
            ) : (
              <CaretRight size={18} aria-hidden='true' />
            )}
          </button>

          <Link
            href='/'
            className='p-1.5 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-white/8 transition-colors duration-100'
            aria-label='Back to chats'>
            <ArrowLeft size={18} aria-hidden='true' />
          </Link>

          <div className='flex-1 flex items-center justify-center'>
            <span className='text-sm font-medium text-zinc-400 truncate max-w-xs'>
              {project.name}
            </span>
            {selectedAgent && (
              <span className='ml-2 px-2 py-0.5 text-[11px] rounded-full bg-violet-500/15 text-violet-400 border border-violet-500/20 capitalize'>
                {selectedAgent}
              </span>
            )}
          </div>

          {/* User */}
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
