'use client';

import { useRef, useEffect } from 'react';
import type { KeyboardEvent } from 'react';
import { PaperPlaneTilt } from '@phosphor-icons/react/dist/ssr/PaperPlaneTilt';
import { Stop } from '@phosphor-icons/react/dist/ssr/Stop';

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onStop?: () => void;
  isStreaming: boolean;
  disabled: boolean;
  placeholder?: string;
}

export default function ChatInput({
  value,
  onChange,
  onSubmit,
  onStop,
  isStreaming,
  disabled,
  placeholder = 'Send a message...',
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    const lineHeight = 24;
    const maxLines = 6;
    const maxHeight = lineHeight * maxLines + 24; // padding
    el.style.height = `${Math.min(el.scrollHeight, maxHeight)}px`;
  }, [value]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (canSubmit) {
        onSubmit();
      }
    }
  };

  const canSubmit = value.trim().length > 0 && !disabled;

  return (
    <div className="flex flex-col gap-0">
      <div
        className={`
          flex items-end gap-2 w-full rounded-2xl border px-4 py-3
          bg-white/5
          transition-colors duration-200
          ${isStreaming || disabled
            ? 'border-white/8'
            : 'border-white/10 focus-within:border-violet-500/30'
          }
        `}
      >
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled && !isStreaming}
          placeholder={placeholder}
          rows={1}
          aria-label="Message input"
          aria-multiline="true"
          className="flex-1 bg-transparent text-sm text-zinc-100 placeholder-zinc-600 resize-none outline-none leading-6 min-h-6 overflow-y-auto disabled:cursor-not-allowed disabled:text-zinc-500"
        />

        {/* Action button */}
        <div className="shrink-0 mb-0.5">
          {isStreaming ? (
            <button
              onClick={onStop}
              aria-label="Stop generation"
              className="flex items-center justify-center w-8 h-8 rounded-full bg-zinc-700 hover:bg-zinc-600 border border-white/10 text-zinc-300 hover:text-white transition-all duration-150"
            >
              <Stop size={14} weight="fill" aria-hidden="true" />
            </button>
          ) : (
            <button
              onClick={() => canSubmit && onSubmit()}
              disabled={!canSubmit}
              aria-label="Send message"
              className={`transition-colors duration-150 ${
                canSubmit
                  ? 'text-violet-400 hover:text-violet-300'
                  : 'text-zinc-700 cursor-not-allowed'
              }`}
            >
              <PaperPlaneTilt size={20} weight="fill" aria-hidden="true" />
            </button>
          )}
        </div>
      </div>

      <p className="text-center text-[11px] text-zinc-700 mt-1.5 select-none">
        Enter to send &middot; Shift+Enter for new line
      </p>
    </div>
  );
}
