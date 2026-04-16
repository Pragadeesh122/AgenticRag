"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Brain } from "@phosphor-icons/react/dist/ssr/Brain";
import { Plus } from "@phosphor-icons/react/dist/ssr/Plus";
import { Trash } from "@phosphor-icons/react/dist/ssr/Trash";
import { X } from "@phosphor-icons/react/dist/ssr/X";
import { addMemoryFact, fetchMemory, removeMemoryFact } from "@/lib/api";
import type { MemoryFact } from "@/lib/types";

interface MemoryPanelProps {
  open: boolean;
  onClose: () => void;
}

function formatObservedAt(timestamp: string): string {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function sourceLabel(sourceSessionId: string | null): string {
  if (sourceSessionId === "manual-memory") {
    return "Manual";
  }
  if (sourceSessionId === "backfill-from-redis") {
    return "Backfill";
  }
  return "Extracted";
}

export default function MemoryPanel({ open, onClose }: MemoryPanelProps) {
  const [facts, setFacts] = useState<MemoryFact[]>([]);
  const [newFact, setNewFact] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [removingId, setRemovingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchMemory();
      setFacts(data.facts);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) {
      load();
    }
  }, [open, load]);

  const trimmedNewFact = newFact.trim();
  const canAdd = trimmedNewFact.length > 0 && !submitting;

  const handleAdd = async () => {
    if (!canAdd) {
      return;
    }
    setSubmitting(true);
    try {
      const created = await addMemoryFact(trimmedNewFact);
      setFacts((prev) => {
        const withoutDuplicate = prev.filter((fact) => fact.id !== created.id);
        return [created, ...withoutDuplicate];
      });
      setNewFact("");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRemove = async (factId: string) => {
    setRemovingId(factId);
    try {
      await removeMemoryFact(factId);
      setFacts((prev) => prev.filter((fact) => fact.id !== factId));
    } finally {
      setRemovingId(null);
    }
  };

  const totalFacts = facts.length;
  const emptyState = useMemo(
    () =>
      "No atomic memories stored yet. As you chat, durable facts about your projects, preferences, and background will show up here.",
    []
  );

  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/40"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      <div
        className={`fixed top-0 right-0 z-50 h-full w-full max-w-md flex flex-col transition-transform duration-200 ease-in-out ${
          open ? "translate-x-0" : "translate-x-full"
        }`}
        style={{
          background: "#161618",
          borderLeft: "1px solid rgba(255,255,255,0.08)",
        }}
        role="dialog"
        aria-label="Memory panel"
        aria-hidden={!open}
      >
        <div className="flex items-center justify-between px-5 py-4 shrink-0 border-b border-white/6">
          <div className="flex items-center gap-2.5">
            <Brain size={18} weight="duotone" className="text-emerald-400" />
            <h2 className="text-sm font-semibold text-zinc-100">Memory</h2>
            <span className="text-[11px] text-zinc-500 font-medium">
              {totalFacts} active facts
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-white/8 transition-colors"
            aria-label="Close memory panel"
          >
            <X size={16} />
          </button>
        </div>

        <div className="px-5 py-4 shrink-0 border-b border-white/6">
          <div className="mb-2">
            <h3 className="text-xs font-semibold text-zinc-300 tracking-wide">
              Add Memory
            </h3>
            <p className="text-[11px] text-zinc-600 mt-0.5">
              Add one atomic fact the AI should remember. Keep it to a single durable fact.
            </p>
          </div>
          <textarea
            value={newFact}
            onChange={(e) => setNewFact(e.target.value)}
            placeholder="Example: Prefers concise explanations"
            rows={3}
            className="w-full text-[13px] leading-relaxed text-zinc-300 placeholder-zinc-600 rounded-lg px-3 py-2.5 resize-none transition-colors"
            style={{
              background: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.06)",
            }}
          />
          <div className="mt-2 flex items-center justify-between gap-2">
            <p className="text-[11px] text-zinc-600">
              Manual entries are stored alongside extracted memory facts.
            </p>
            <button
              onClick={handleAdd}
              disabled={!canAdd}
              className="flex items-center gap-1.5 px-2.5 py-1.5 text-[11px] font-medium rounded-md bg-emerald-500/15 text-emerald-400 hover:bg-emerald-500/25 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <div className="w-3 h-3 rounded-full border border-emerald-400/40 border-t-transparent animate-spin" />
              ) : (
                <Plus size={12} />
              )}
              Add Fact
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="w-5 h-5 rounded-full border-2 border-emerald-400/40 border-t-transparent animate-spin" />
            </div>
          ) : facts.length === 0 ? (
            <div
              className="rounded-xl p-4 text-[12px] leading-relaxed text-zinc-500"
              style={{
                background: "rgba(255,255,255,0.03)",
                border: "1px solid rgba(255,255,255,0.05)",
              }}
            >
              {emptyState}
            </div>
          ) : (
            facts.map((fact) => (
              <div
                key={fact.id}
                className="rounded-xl px-3.5 py-3"
                style={{
                  background: "rgba(255,255,255,0.04)",
                  border: "1px solid rgba(255,255,255,0.06)",
                }}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <p className="text-[13px] leading-relaxed text-zinc-200">
                      {fact.text}
                    </p>
                    <div className="mt-2 flex items-center gap-2 text-[11px] text-zinc-500">
                      <span>{sourceLabel(fact.source_session_id)}</span>
                      {formatObservedAt(fact.observed_at) ? (
                        <>
                          <span className="text-zinc-700">•</span>
                          <span>{formatObservedAt(fact.observed_at)}</span>
                        </>
                      ) : null}
                    </div>
                  </div>
                  <button
                    onClick={() => handleRemove(fact.id)}
                    disabled={removingId === fact.id}
                    className="p-1.5 rounded-lg text-zinc-500 hover:text-red-300 hover:bg-red-500/10 transition-colors disabled:opacity-50"
                    aria-label="Remove memory fact"
                    title="Remove memory fact"
                  >
                    {removingId === fact.id ? (
                      <div className="w-3.5 h-3.5 rounded-full border border-zinc-500/40 border-t-transparent animate-spin" />
                    ) : (
                      <Trash size={14} />
                    )}
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="px-5 py-3 shrink-0 border-t border-white/6">
          <p className="text-[11px] text-zinc-600 leading-relaxed">
            Durable user facts are extracted automatically from conversations and stored individually.
            Removing a fact stops it from being injected into future prompts.
          </p>
        </div>
      </div>
    </>
  );
}
