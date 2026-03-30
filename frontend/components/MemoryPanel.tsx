"use client";

import { useState, useEffect, useCallback } from "react";
import { X } from "@phosphor-icons/react/dist/ssr/X";
import { FloppyDisk } from "@phosphor-icons/react/dist/ssr/FloppyDisk";
import { Brain } from "@phosphor-icons/react/dist/ssr/Brain";
import { fetchMemory, updateMemoryCategory } from "@/lib/api";
import type { UserMemory, MemoryCategory } from "@/lib/types";

const CATEGORIES: { key: MemoryCategory; label: string; description: string }[] = [
  {
    key: "work_context",
    label: "Work Context",
    description: "Job title, employer, team, tech stack, work projects",
  },
  {
    key: "personal_context",
    label: "Personal Context",
    description: "Name, location, education, languages, hobbies",
  },
  {
    key: "top_of_mind",
    label: "Top of Mind",
    description: "Long-running projects or learning goals",
  },
  {
    key: "preferences",
    label: "Preferences",
    description: "Code style, workflow, communication preferences",
  },
];

interface MemoryPanelProps {
  open: boolean;
  onClose: () => void;
}

export default function MemoryPanel({ open, onClose }: MemoryPanelProps) {
  const [memory, setMemory] = useState<UserMemory>({
    work_context: "",
    personal_context: "",
    top_of_mind: "",
    preferences: "",
  });
  const [draft, setDraft] = useState<UserMemory>({ ...memory });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<MemoryCategory | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchMemory();
      setMemory(data);
      setDraft(data);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) load();
  }, [open, load]);

  const handleSave = async (category: MemoryCategory) => {
    setSaving(category);
    try {
      await updateMemoryCategory(category, draft[category]);
      setMemory((prev) => ({ ...prev, [category]: draft[category] }));
    } finally {
      setSaving(null);
    }
  };

  const isDirty = (category: MemoryCategory) =>
    draft[category] !== memory[category];

  const totalEntries = CATEGORIES.filter((c) => memory[c.key].trim()).length;

  return (
    <>
      {/* Backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/40"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Panel */}
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
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 shrink-0 border-b border-white/6">
          <div className="flex items-center gap-2.5">
            <Brain size={18} weight="duotone" className="text-emerald-400" />
            <h2 className="text-sm font-semibold text-zinc-100">Memory</h2>
            <span className="text-[11px] text-zinc-500 font-medium">
              {totalEntries} / {CATEGORIES.length} active
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

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5">
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div
                className="w-5 h-5 rounded-full border-2 border-emerald-400/40 border-t-transparent animate-spin"
              />
            </div>
          ) : (
            CATEGORIES.map((cat) => (
              <div key={cat.key} className="group">
                {/* Category header */}
                <div className="mb-1.5">
                  <h3 className="text-xs font-semibold text-zinc-300 tracking-wide">
                    {cat.label}
                  </h3>
                  <p className="text-[11px] text-zinc-600 mt-0.5">
                    {cat.description}
                  </p>
                </div>

                {/* Editable textarea */}
                <textarea
                  value={draft[cat.key]}
                  onChange={(e) =>
                    setDraft((prev) => ({ ...prev, [cat.key]: e.target.value }))
                  }
                  placeholder={`No ${cat.label.toLowerCase()} stored yet...`}
                  rows={3}
                  className="w-full text-[13px] leading-relaxed text-zinc-300 placeholder-zinc-600 rounded-lg px-3 py-2.5 resize-none transition-colors"
                  style={{
                    background: "rgba(255,255,255,0.04)",
                    border: isDirty(cat.key)
                      ? "1px solid rgba(16,185,129,0.3)"
                      : "1px solid rgba(255,255,255,0.06)",
                  }}
                />

                {/* Save button — only visible when changed */}
                {isDirty(cat.key) && (
                  <div className="flex items-center gap-2 mt-1.5 animate-fade-in">
                    <button
                      onClick={() => handleSave(cat.key)}
                      disabled={saving === cat.key}
                      className="flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-medium rounded-md bg-emerald-500/15 text-emerald-400 hover:bg-emerald-500/25 transition-colors disabled:opacity-50"
                    >
                      {saving === cat.key ? (
                        <div className="w-3 h-3 rounded-full border border-emerald-400/40 border-t-transparent animate-spin" />
                      ) : (
                        <FloppyDisk size={12} />
                      )}
                      Save
                    </button>
                    <button
                      onClick={() =>
                        setDraft((prev) => ({
                          ...prev,
                          [cat.key]: memory[cat.key],
                        }))
                      }
                      className="px-2.5 py-1 text-[11px] font-medium text-zinc-500 hover:text-zinc-300 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 shrink-0 border-t border-white/6">
          <p className="text-[11px] text-zinc-600 leading-relaxed">
            Memory is automatically extracted from your conversations. You can
            view and edit what the AI remembers about you here.
          </p>
        </div>
      </div>
    </>
  );
}
