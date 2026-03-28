"use client";

import { useState } from "react";

interface QuizQuestion {
  id: number;
  type: "multiple_choice" | "true_false" | "short_answer";
  question: string;
  options?: string[];
  correct: string;
  explanation: string;
}

interface QuizData {
  title: string;
  questions: QuizQuestion[];
}

function tryParseQuiz(content: string): QuizData | null {
  try {
    // Try raw JSON first
    const parsed = JSON.parse(content.trim());
    if (parsed.title && Array.isArray(parsed.questions)) return parsed;
  } catch {
    // Try extracting JSON from markdown code fence
    const match = content.match(/```(?:json)?\s*\n?([\s\S]*?)\n?\s*```/);
    if (match) {
      try {
        const parsed = JSON.parse(match[1].trim());
        if (parsed.title && Array.isArray(parsed.questions)) return parsed;
      } catch {
        /* not valid JSON */
      }
    }
  }
  return null;
}

function QuestionCard({ q, index }: { q: QuizQuestion; index: number }) {
  const [selected, setSelected] = useState<string | null>(null);
  const [revealed, setRevealed] = useState(false);
  const [shortAnswer, setShortAnswer] = useState("");

  const isCorrect =
    q.type === "short_answer"
      ? shortAnswer.trim().toLowerCase() === q.correct.toLowerCase()
      : selected === q.correct;

  const handleSelect = (option: string) => {
    if (revealed) return;
    const value =
      q.type === "true_false" ? option : option.match(/^([A-Z])\)/)?.[1] ?? option;
    setSelected(value);
  };

  const handleReveal = () => setRevealed(true);

  return (
    <div className="rounded-xl border border-white/8 bg-white/[0.02] overflow-hidden">
      {/* Question header */}
      <div className="px-4 py-3 border-b border-white/5 flex items-center gap-3">
        <span className="shrink-0 w-6 h-6 rounded-full bg-violet-600/20 text-violet-400 text-xs font-medium flex items-center justify-center">
          {index + 1}
        </span>
        <span className="text-sm font-medium text-zinc-200">{q.question}</span>
      </div>

      {/* Options */}
      <div className="px-4 py-3 flex flex-col gap-2">
        {q.type === "short_answer" ? (
          <input
            type="text"
            value={shortAnswer}
            onChange={(e) => setShortAnswer(e.target.value)}
            disabled={revealed}
            placeholder="Type your answer..."
            className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-zinc-200 placeholder:text-zinc-500 outline-none focus:border-violet-500/50 disabled:opacity-50"
          />
        ) : (
          (q.options ?? []).map((opt) => {
            const optKey =
              q.type === "true_false"
                ? opt
                : opt.match(/^([A-Z])\)/)?.[1] ?? opt;
            const isSelected = selected === optKey;
            const isAnswer = optKey === q.correct;

            let style = "border-white/8 bg-white/[0.02] hover:bg-white/5";
            if (revealed && isAnswer) {
              style = "border-emerald-500/30 bg-emerald-500/10";
            } else if (revealed && isSelected && !isAnswer) {
              style = "border-red-500/30 bg-red-500/10";
            } else if (isSelected) {
              style = "border-violet-500/30 bg-violet-500/10";
            }

            return (
              <button
                key={opt}
                onClick={() => handleSelect(opt)}
                disabled={revealed}
                className={`text-left px-3 py-2 rounded-lg border text-sm text-zinc-300 transition-colors ${style} disabled:cursor-default`}
              >
                {opt}
              </button>
            );
          })
        )}
      </div>

      {/* Reveal / Result */}
      <div className="px-4 py-3 border-t border-white/5">
        {!revealed ? (
          <button
            onClick={handleReveal}
            disabled={q.type === "short_answer" ? !shortAnswer.trim() : !selected}
            className="text-xs font-medium text-violet-400 hover:text-violet-300 disabled:text-zinc-600 disabled:cursor-not-allowed transition-colors"
          >
            Reveal answer
          </button>
        ) : (
          <div className="flex flex-col gap-1.5">
            <span
              className={`text-xs font-medium ${isCorrect ? "text-emerald-400" : "text-red-400"}`}
            >
              {isCorrect ? "Correct!" : `Incorrect — answer: ${q.correct}`}
            </span>
            {q.explanation && (
              <p className="text-xs text-zinc-500 leading-relaxed">
                {q.explanation}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function QuizRenderer({ content }: { content: string }) {
  const quiz = tryParseQuiz(content);
  if (!quiz) return null;

  return (
    <div className="flex flex-col gap-3 w-full">
      <h3 className="text-base font-semibold text-zinc-100">{quiz.title}</h3>
      {quiz.questions.map((q, i) => (
        <QuestionCard key={q.id ?? i} q={q} index={i} />
      ))}
    </div>
  );
}

export { tryParseQuiz };
