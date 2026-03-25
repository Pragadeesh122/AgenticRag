'use client';

import { PencilSimpleLineIcon } from '@phosphor-icons/react/dist/ssr/PencilSimpleLine';
import { TrashIcon } from '@phosphor-icons/react/dist/ssr/Trash';
import { ChatTeardropDots } from '@phosphor-icons/react/dist/ssr/ChatTeardropDots';
import { AgenticLogo } from './ChatArea';
import type { Session } from '@/lib/types';

function groupSessionsByTime(sessions: Session[]): {
  today: Session[];
  yesterday: Session[];
  older: Session[];
} {
  const now = Date.now();
  const oneDayMs = 24 * 60 * 60 * 1000;
  const startOfToday = new Date();
  startOfToday.setHours(0, 0, 0, 0);
  const startOfYesterday = new Date(startOfToday.getTime() - oneDayMs);

  const today: Session[] = [];
  const yesterday: Session[] = [];
  const older: Session[] = [];

  const sorted = [...sessions].sort((a, b) => b.updatedAt - a.updatedAt);

  for (const s of sorted) {
    if (s.updatedAt >= startOfToday.getTime()) {
      today.push(s);
    } else if (s.updatedAt >= startOfYesterday.getTime()) {
      yesterday.push(s);
    } else {
      older.push(s);
    }
  }
  // avoid unused warning
  void now;

  return { today, yesterday, older };
}

interface SidebarProps {
  sessions: Session[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onDeleteSession: (id: string) => void;
}

interface SessionGroupProps {
  label: string;
  sessions: Session[];
  activeSessionId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}

function SessionGroup({ label, sessions, activeSessionId, onSelect, onDelete }: SessionGroupProps) {
  if (sessions.length === 0) return null;
  return (
    <div className="mb-4">
      <p className="px-3 mb-1 text-[11px] font-medium uppercase tracking-widest text-zinc-500 select-none">
        {label}
      </p>
      <ul role="list" className="flex flex-col gap-0.5">
        {sessions.map((s) => (
          <li key={s.id} className="group relative">
            <button
              onClick={() => onSelect(s.id)}
              className={`
                w-full text-left px-3 py-2.5 rounded-lg text-sm truncate transition-colors duration-150
                ${activeSessionId === s.id
                  ? 'bg-violet-500/20 text-zinc-100'
                  : 'text-zinc-400 hover:bg-white/5 hover:text-zinc-200'
                }
              `}
              aria-current={activeSessionId === s.id ? 'true' : undefined}
            >
              {s.title || 'New chat'}
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete(s.id);
              }}
              aria-label={`Delete session: ${s.title || 'New chat'}`}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded opacity-0 group-hover:opacity-100 text-zinc-500 hover:text-red-400 hover:bg-white/5 transition-colors duration-150 focus:opacity-100"
            >
              <TrashIcon size={14} aria-hidden="true" />
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function Sidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
}: SidebarProps) {
  const { today, yesterday, older } = groupSessionsByTime(sessions);

  return (
    <aside
      className="flex flex-col h-full bg-[#1e1e1e] border-r border-white/6"
      aria-label="Chat sessions"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-4 shrink-0">
        {/* Logo */}
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-linear-to-br from-violet-600/30 to-purple-600/30 border border-violet-500/20 flex items-center justify-center shrink-0">
            <AgenticLogo size={22} />
          </div>
          <span className="text-sm font-semibold text-zinc-200 tracking-tight">AgenticRAG</span>
        </div>

        <button
          onClick={onNewChat}
          aria-label="New chat"
          className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-white/8 transition-colors duration-100"
        >
          <PencilSimpleLineIcon size={17} aria-hidden="true" />
        </button>
      </div>

      {/* Session list */}
      <nav className="flex-1 overflow-y-auto px-2 pb-4">
        {sessions.length === 0 ? (
          <div className="flex flex-col items-center gap-2 px-3 py-8 text-center select-none">
            <ChatTeardropDots size={24} className="text-zinc-700" aria-hidden="true" />
            <p className="text-xs text-zinc-600">No conversations yet</p>
          </div>
        ) : (
          <>
            <SessionGroup
              label="Today"
              sessions={today}
              activeSessionId={activeSessionId}
              onSelect={onSelectSession}
              onDelete={onDeleteSession}
            />
            <SessionGroup
              label="Yesterday"
              sessions={yesterday}
              activeSessionId={activeSessionId}
              onSelect={onSelectSession}
              onDelete={onDeleteSession}
            />
            <SessionGroup
              label="Older"
              sessions={older}
              activeSessionId={activeSessionId}
              onSelect={onSelectSession}
              onDelete={onDeleteSession}
            />
          </>
        )}
      </nav>
    </aside>
  );
}
