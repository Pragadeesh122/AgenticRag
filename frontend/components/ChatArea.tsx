'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { ArrowLineDown } from '@phosphor-icons/react/dist/ssr/ArrowLineDown';
import { BookOpenText } from '@phosphor-icons/react/dist/ssr/BookOpenText';
import { Table } from '@phosphor-icons/react/dist/ssr/Table';
import { Compass } from '@phosphor-icons/react/dist/ssr/Compass';
import { Sparkle } from '@phosphor-icons/react/dist/ssr/Sparkle';
import { ThreadPrimitive } from '@assistant-ui/react';
import type { Message, ProjectDocument } from '@/lib/types';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';

interface SuggestionCard {
  label: string;
  query: string;
  icon: React.ReactNode;
}

const SUGGESTIONS: SuggestionCard[] = [
  {
    label: 'Search the knowledge base',
    query: 'Search the knowledge base for information about ',
    icon: <BookOpenText size={20} className="text-violet-400" aria-hidden="true" />,
  },
  {
    label: 'Query the database',
    query: 'Query the database to show me ',
    icon: <Table size={20} className="text-blue-400" aria-hidden="true" />,
  },
  {
    label: 'Browse the web',
    query: 'Browse the web and find information about ',
    icon: <Compass size={20} className="text-emerald-400" aria-hidden="true" />,
  },
  {
    label: 'What can you do?',
    query: 'What tools and capabilities do you have?',
    icon: <Sparkle size={20} className="text-amber-400" aria-hidden="true" />,
  },
];

// AgenticRAG logo: interconnected network graph with central pulse spark
export function AgenticLogo({ size = 40 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      aria-hidden="true"
    >
      {/* Outer ring — subtle orbit */}
      <circle cx="20" cy="20" r="17" stroke="rgba(139,92,246,0.12)" strokeWidth="1" />

      {/* Edge connections between nodes */}
      <line x1="20" y1="9" x2="31" y2="25" stroke="rgba(167,139,250,0.25)" strokeWidth="1.2" strokeLinecap="round" />
      <line x1="20" y1="9" x2="9" y2="25" stroke="rgba(167,139,250,0.25)" strokeWidth="1.2" strokeLinecap="round" />
      <line x1="9" y1="25" x2="31" y2="25" stroke="rgba(167,139,250,0.25)" strokeWidth="1.2" strokeLinecap="round" />
      {/* Center to periphery connections */}
      <line x1="20" y1="20" x2="20" y2="9" stroke="rgba(167,139,250,0.35)" strokeWidth="1" strokeLinecap="round" />
      <line x1="20" y1="20" x2="31" y2="25" stroke="rgba(167,139,250,0.35)" strokeWidth="1" strokeLinecap="round" />
      <line x1="20" y1="20" x2="9" y2="25" stroke="rgba(167,139,250,0.35)" strokeWidth="1" strokeLinecap="round" />

      {/* Peripheral nodes */}
      <circle cx="20" cy="9" r="2.5" fill="#7c3aed" opacity="0.7" />
      <circle cx="31" cy="25" r="2.5" fill="#7c3aed" opacity="0.7" />
      <circle cx="9" cy="25" r="2.5" fill="#7c3aed" opacity="0.7" />

      {/* Central hub — brighter, larger */}
      <circle cx="20" cy="20" r="4" fill="rgba(124,58,237,0.3)" />
      <circle cx="20" cy="20" r="2.5" fill="#a78bfa" />

      {/* Spark / pulse — top right of center */}
      <path
        d="M27 11 L27.8 13.5 L30.5 14.3 L27.8 15.1 L27 17.5 L26.2 15.1 L23.5 14.3 L26.2 13.5 Z"
        fill="#c4b5fd"
        opacity="0.95"
      />
    </svg>
  );
}

interface ChatAreaProps {
  messages: Message[];
  streamingMessageId: string | null;
  isLoading: boolean;
  isStreaming: boolean;
  inputValue: string;
  onInputChange: (value: string) => void;
  onSubmit: () => void;
  onStop?: () => void;
  projectId?: string;
  projectDocuments?: ProjectDocument[];
}

export default function ChatArea({
  messages,
  streamingMessageId,
  isLoading,
  isStreaming,
  inputValue,
  onInputChange,
  onSubmit,
  onStop,
  projectId,
  projectDocuments,
}: ChatAreaProps) {
  const inputRef = useRef<HTMLDivElement>(null);

  // Keyboard shortcuts: / to focus input, Escape to blur
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      const isEditable = tag === 'INPUT' || tag === 'TEXTAREA' || (e.target as HTMLElement).isContentEditable;

      if (e.key === '/' && !isEditable) {
        e.preventDefault();
        const textarea = inputRef.current?.querySelector('textarea');
        textarea?.focus();
      }

      if (e.key === 'Escape' && isEditable) {
        (e.target as HTMLElement).blur();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const userScrolledUp = useRef(false);

  const scrollToBottomPassive = useCallback((behavior: ScrollBehavior = 'smooth') => {
    bottomRef.current?.scrollIntoView({ behavior, block: 'end' });
    userScrolledUp.current = false;
  }, []);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = 'smooth') => {
    scrollToBottomPassive(behavior);
    setShowScrollBtn(false);
  }, [scrollToBottomPassive]);

  // Detect user scrolling up
  useEffect(() => {
    const el = scrollContainerRef.current;
    if (!el) return;
    const handleScroll = () => {
      const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
      if (distanceFromBottom > 120) {
        userScrolledUp.current = true;
        setShowScrollBtn(true);
      } else {
        userScrolledUp.current = false;
        setShowScrollBtn(false);
      }
    };
    el.addEventListener('scroll', handleScroll, { passive: true });
    return () => el.removeEventListener('scroll', handleScroll);
  }, []);

  // Auto-scroll on new messages/tokens unless user scrolled up
  useEffect(() => {
    if (!userScrolledUp.current) {
      scrollToBottomPassive('smooth');
    }
  }, [messages, scrollToBottomPassive]);

  // Scroll immediately when a new user message is sent
  useEffect(() => {
    if (messages.length > 0 && messages[messages.length - 1].role === 'user') {
      scrollToBottomPassive('smooth');
      userScrolledUp.current = false;
    }
  }, [messages.length, messages, scrollToBottomPassive]);

  const isEmpty = messages.length === 0;

  return (
    <div className="flex flex-col flex-1 min-h-0 relative">
      {/* Messages area */}
      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto"
        role="log"
        aria-live="polite"
        aria-label="Chat messages"
      >
        {isEmpty ? (
          /* Welcome / empty state */
          <div className="flex flex-col items-center justify-center min-h-full px-4 py-10">
            <div className="w-full max-w-xl flex flex-col items-center gap-6">
              {/* Logo + heading */}
              <div className="flex flex-col items-center gap-3 text-center">
                <div className="w-14 h-14 rounded-2xl bg-linear-to-br from-violet-600/20 to-purple-600/20 border border-violet-500/20 flex items-center justify-center">
                  <AgenticLogo size={36} />
                </div>
                <div>
                  <h1 className="text-2xl font-semibold text-zinc-100 tracking-tight mb-1.5">
                    AgenticRAG
                  </h1>
                  <p className="text-sm text-zinc-500 max-w-sm leading-relaxed">
                    AI with full tool access — RAG search, database queries, and web browsing
                  </p>
                </div>
              </div>

              {/* Suggestion cards */}
              <div className="grid grid-cols-2 gap-2.5 w-full">
                {SUGGESTIONS.map((card) => (
                  <button
                    key={card.label}
                    onClick={() => onInputChange(card.query)}
                    className="flex items-start gap-3 px-4 py-3.5 rounded-xl bg-white/3 border border-white/5 text-left hover:bg-white/6 hover:border-white/10 hover:scale-[1.02] transition-all duration-150 group"
                  >
                    <span className="mt-0.5 shrink-0">{card.icon}</span>
                    <span className="text-sm text-zinc-400 group-hover:text-zinc-300 transition-colors duration-150 leading-snug">
                      {card.label}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="px-4 py-8">
            <div className="max-w-[48rem] mx-auto flex flex-col gap-6">
              <ThreadPrimitive.Messages>
                {({ message: auiMessage }) => {
                  const index = messages.findIndex((m) => m.id === auiMessage.id);
                  const message = messages[index];
                  if (!message) return null;
                  return (
                    <MessageBubble
                      key={message.id}
                      message={message}
                      isStreaming={streamingMessageId === message.id}
                      isLast={index === messages.length - 1}
                      projectId={projectId}
                      projectDocuments={projectDocuments}
                    />
                  );
                }}
              </ThreadPrimitive.Messages>
              <div ref={bottomRef} aria-hidden="true" className="h-1" />
            </div>
          </div>
        )}
      </div>

      {/* Scroll to bottom floating pill */}
      {showScrollBtn && (
        <div className="absolute bottom-32 left-1/2 -translate-x-1/2 z-10">
          <button
            onClick={() => scrollToBottom('smooth')}
            aria-label="Scroll to bottom"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-zinc-800 border border-white/10 text-xs text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700 shadow-lg transition-all duration-150"
          >
            <ArrowLineDown size={12} weight="fill" aria-hidden="true" />
            <span>Scroll to bottom</span>
          </button>
        </div>
      )}

      {/* Input area */}
      <div ref={inputRef} className="shrink-0 px-4 pb-5 pt-2">
        <div className="max-w-[48rem] mx-auto">
          <ChatInput
            value={inputValue}
            onChange={onInputChange}
            onSubmit={onSubmit}
            onStop={onStop}
            isStreaming={isStreaming}
            disabled={isLoading && !isStreaming}
          />
        </div>
      </div>
    </div>
  );
}
