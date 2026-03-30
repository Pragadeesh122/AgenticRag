'use client';

import { useState } from 'react';
import { CircleNotch } from '@phosphor-icons/react/dist/ssr/CircleNotch';
import { CheckCircle } from '@phosphor-icons/react/dist/ssr/CheckCircle';
import { WarningCircle } from '@phosphor-icons/react/dist/ssr/WarningCircle';
import { CaretDown } from '@phosphor-icons/react/dist/ssr/CaretDown';
import { Wrench } from '@phosphor-icons/react/dist/ssr/Wrench';
import type { ToolCall } from '@/lib/types';

function formatDuration(startedAt?: number, completedAt?: number): string {
  if (!startedAt || !completedAt) return '';
  const ms = completedAt - startedAt;
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function formatToolName(name: string): string {
  return name.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function getToolDescription(tool: ToolCall): string | null {
  if (!tool.args) return null;
  const { name, args } = tool;

  // Agent/retrieval events pass description directly
  if (args.description) return args.description;

  switch (name) {
    case 'search':
      return args.query ? `Searching: ${args.query}` : null;
    case 'query_db':
      return args.question ? `Querying: ${args.question}` : null;
    case 'browser_task':
      return args.goal ? `Browsing: ${args.goal}` : null;
    case 'query_local_kb':
      return args.query ? `Searching knowledge base: ${args.query}` : null;
    case 'portfolio':
      return args.query ? `Looking up: ${args.query}` : null;
    default: {
      const firstValue = Object.values(args).find((v) => typeof v === 'string' && v.length > 0);
      return firstValue ? String(firstValue) : null;
    }
  }
}

interface SingleToolProps {
  tool: ToolCall;
  compact?: boolean;
}

function SingleTool({ tool, compact = false }: SingleToolProps) {
  const duration = formatDuration(tool.startedAt, tool.completedAt);
  const isRunning = tool.status === 'running';
  const isDone = tool.status === 'done';
  const isError = tool.status === 'error';
  const description = getToolDescription(tool);

  return (
    <div
      className={`flex flex-col gap-0.5 ${compact ? '' : 'px-3 py-2'}`}
      role="status"
      aria-label={`Tool ${formatToolName(tool.name)}: ${tool.status}`}
    >
      <div className="flex items-center gap-2">
        {isRunning && (
          <CircleNotch
            size={18}
            className="text-violet-400 animate-spin shrink-0"
            aria-hidden="true"
          />
        )}
        {isDone && (
          <CheckCircle
            size={18}
            weight="duotone"
            className="text-emerald-400 shrink-0"
            aria-hidden="true"
          />
        )}
        {isError && (
          <WarningCircle
            size={18}
            weight="duotone"
            className="text-amber-400 shrink-0"
            aria-hidden="true"
          />
        )}
        <span
          className={`text-xs font-medium truncate ${
            isRunning
              ? 'text-zinc-300'
              : isDone
              ? 'text-zinc-400'
              : 'text-amber-300'
          }`}
        >
          {formatToolName(tool.name)}
        </span>
        {isRunning && (
          <span className="text-xs text-zinc-600 shrink-0">Running...</span>
        )}
        {isDone && duration && (
          <span className="text-xs text-zinc-600 shrink-0">{duration}</span>
        )}
        {isError && (
          <span className="text-xs text-amber-500/80 shrink-0">Failed</span>
        )}
      </div>
      {description && (
        <span className="text-[11px] text-zinc-500 truncate pl-[26px]">
          {description}
        </span>
      )}
    </div>
  );
}

interface ToolIndicatorProps {
  tools: ToolCall[];
}

export default function ToolIndicator({ tools }: ToolIndicatorProps) {
  const hasRunning = tools.some((t) => t.status === 'running');
  const [expanded, setExpanded] = useState(hasRunning);

  // Expand when tools start running
  if (hasRunning && !expanded) {
    setExpanded(true);
  }

  if (tools.length === 0) return null;

  const completedCount = tools.filter((t) => t.status === 'done').length;
  const errorCount = tools.filter((t) => t.status === 'error').length;
  const runningCount = tools.filter((t) => t.status === 'running').length;

  // Single tool — simpler display
  if (tools.length === 1) {
    const tool = tools[0];
    return (
      <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/3 border border-white/5 w-fit max-w-full">
        <SingleTool tool={tool} />
      </div>
    );
  }

  // Multiple tools — grouped with expand/collapse
  const totalDoneMs = tools
    .filter((t) => t.status === 'done' && t.startedAt && t.completedAt)
    .reduce((sum, t) => sum + ((t.completedAt ?? 0) - (t.startedAt ?? 0)), 0);

  const summaryDuration =
    totalDoneMs > 0
      ? totalDoneMs < 1000
        ? `${totalDoneMs}ms`
        : `${(totalDoneMs / 1000).toFixed(1)}s`
      : '';

  return (
    <div className="rounded-lg bg-white/3 border border-white/5 overflow-hidden w-full max-w-lg">
      {/* Header row */}
      <button
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        className="flex items-center gap-2 w-full px-3 py-2 hover:bg-white/3 transition-colors duration-100 text-left"
      >
        <Wrench size={16} className="text-zinc-500 shrink-0" aria-hidden="true" />
        <span className="text-xs font-medium text-zinc-400 flex-1">
          {runningCount > 0
            ? `Running ${runningCount} of ${tools.length} steps...`
            : errorCount > 0
            ? `${tools.length} steps · ${errorCount} failed`
            : `${tools.length} steps complete`}
        </span>
        {summaryDuration && (
          <span className="text-xs text-zinc-600 shrink-0">{summaryDuration}</span>
        )}
        {runningCount > 0 && (
          <CircleNotch
            size={14}
            className="text-violet-400 animate-spin shrink-0"
            aria-hidden="true"
          />
        )}
        {!hasRunning && completedCount === tools.length && errorCount === 0 && (
          <CheckCircle
            size={14}
            weight="duotone"
            className="text-emerald-400 shrink-0"
            aria-hidden="true"
          />
        )}
        <CaretDown
          size={14}
          className={`text-zinc-600 shrink-0 transition-transform duration-200 ${
            expanded ? 'rotate-180' : ''
          }`}
          aria-hidden="true"
        />
      </button>

      {/* Expanded list */}
      {expanded && (
        <div className="border-t border-white/5 divide-y divide-white/3">
          {tools.map((tool) => (
            <div key={tool.id} className="px-3 py-1.5">
              <SingleTool tool={tool} compact />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
