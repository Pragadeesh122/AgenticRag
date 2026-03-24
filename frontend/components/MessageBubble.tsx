"use client";

import {useMemo} from "react";
import {Streamdown} from "streamdown";
import "streamdown/styles.css";
import type {Message} from "@/lib/types";
import ToolIndicator from "./ToolIndicator";

/**
 * Preprocess LLM output to fix common markdown issues before Streamdown renders it.
 * LLMs often omit newlines between headings, lists, and paragraphs.
 */
function normalizeMarkdown(text: string): string {
  // Phase 0: Fix code fences — LLM often puts ``` on the same line as content
  const normalized = text
    // Closing ``` stuck to end of code line: "content```" -> "content\n```"
    .replace(/([^\n`])```/g, "$1\n```")
    // Opening ```lang stuck to next line: "```pythoncode" -> "```python\ncode"
    .replace(/```(\w+)([^\n])/g, "```$1\n$2")
    // Fix headings missing space after # (e.g., "###1." -> "### 1.")
    .replace(/^(#{1,6})([^\s#])/gm, "$1 $2")
    // Newline before ## or ### headings that appear mid-text
    .replace(/([^\n#])(#{1,6}\s)/g, "$1\n$2")
    // Newline before "- **" (bold list items) appearing mid-text
    .replace(/([^\n])(- \*\*)/g, "$1\n$2")
    // Newline after colon followed by "- " (list after label)
    .replace(/:- /g, ":\n- ")
    // Newline between adjacent plain list items after sentence-ending punctuation
    .replace(/([.!?])- /g, "$1\n- ")
    // Split "text- Item" patterns (capital letter = likely new list item)
    .replace(/([a-zA-Z0-9])- ([A-Z])/g, "$1\n- $2")
    // Split table rows: "||" marks row boundary (end of row | start of next row)
    .replace(/\|\|/g, "|\n|");

  // Phase 2: Insert blank lines at content-type transitions
  const lines = normalized.split("\n");
  const result: string[] = [];

  const isListLine = (l: string) => {
    const t = l.trim();
    return (
      t.startsWith("- ") ||
      t.startsWith("* ") ||
      t.startsWith("• ") ||
      /^\d+\.\s/.test(t)
    );
  };
  const isHeadingLine = (l: string) => /^\s*#{1,6}\s/.test(l);

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const prev = i > 0 ? lines[i - 1] : null;

    if (prev !== null && prev.trim() !== "" && line.trim() !== "") {
      if (isHeadingLine(line)) {
        result.push("");
      } else if (isHeadingLine(prev)) {
        result.push("");
      } else if (!isListLine(line) && isListLine(prev)) {
        result.push("");
      } else if (isListLine(line) && !isListLine(prev)) {
        result.push("");
      }
    }

    result.push(line);
  }

  return result.join("\n");
}

// --- Message Bubble ---

interface MessageBubbleProps {
  message: Message;
  isStreaming?: boolean;
}

export default function MessageBubble({
  message,
  isStreaming,
}: MessageBubbleProps) {
  const isUser = message.role === "user";

  const normalizedContent = useMemo(
    () => normalizeMarkdown(message.content),
    [message.content]
  );

  return (
    <div
      className={`flex flex-col gap-3 animate-message-in ${
        isUser ? "items-end" : "items-start"
      }`}>
      {/* Tool calls shown above assistant message content */}
      {!isUser && message.toolCalls.length > 0 && (
        <ToolIndicator tools={message.toolCalls} />
      )}

      {/* Message content */}
      {(message.content || isStreaming) && (
        <div
          className={`
            relative text-sm leading-relaxed
            ${
              isUser
                ? "max-w-[80%] bg-violet-600/15 border border-violet-500/10 text-zinc-100 rounded-2xl rounded-br-sm px-4 py-3"
                : "w-full text-zinc-200"
            }
          `}>
          {isUser ? (
            <p className='whitespace-pre-wrap wrap-break-word'>
              {message.content}
            </p>
          ) : (
            <div className='chat-prose'>
              <Streamdown
                mode={isStreaming ? "streaming" : "static"}
                parseIncompleteMarkdown
                controls={{code: {copy: true, download: false}}}
                lineNumbers={false}>
                {normalizedContent}
              </Streamdown>
            </div>
          )}
        </div>
      )}

      {/* Streaming indicator when no content yet and no tools running */}
      {!isUser &&
        isStreaming &&
        !message.content &&
        message.toolCalls.length === 0 && (
          <div className='flex items-center gap-1.5 py-1'>
            <span
              className='w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse'
              style={{animationDelay: "0ms"}}
              aria-hidden='true'
            />
            <span
              className='w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse'
              style={{animationDelay: "150ms"}}
              aria-hidden='true'
            />
            <span
              className='w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse'
              style={{animationDelay: "300ms"}}
              aria-hidden='true'
            />
          </div>
        )}
    </div>
  );
}
