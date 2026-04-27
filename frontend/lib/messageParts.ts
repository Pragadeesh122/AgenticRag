import type {
  AssistantMessageStatus,
  Message,
  MessagePart,
  RetrievalSource,
  ThinkingEntry,
  ToolCall,
} from "./types";

function cloneParts(parts: MessagePart[]): MessagePart[] {
  return parts.map((part) => ({ ...part }));
}

export function getDefaultAssistantStatus(message: Pick<Message, "role" | "content">): AssistantMessageStatus | undefined {
  if (message.role !== "assistant") return undefined;
  return message.content
    ? { type: "complete", reason: "stop" }
    : { type: "running" };
}

export function stringifyToolArgs(args?: Record<string, unknown>): string {
  if (!args || Object.keys(args).length === 0) return "{}";
  try {
    return JSON.stringify(args, null, 2);
  } catch {
    return "{}";
  }
}

export function appendTextPart(parts: MessagePart[], text: string): MessagePart[] {
  if (!text) return parts;
  const next = cloneParts(parts);
  const last = next.at(-1);
  if (last?.type === "text") {
    last.text += text;
    return next;
  }
  next.push({ type: "text", text });
  return next;
}

export function appendReasoningPart(parts: MessagePart[], text: string): MessagePart[] {
  if (!text) return parts;
  const next = cloneParts(parts);
  const last = next.at(-1);
  if (last?.type === "reasoning") {
    last.text += (last.text ? "\n" : "") + text;
    return next;
  }
  next.push({ type: "reasoning", text });
  return next;
}

export function appendToolCallPart(parts: MessagePart[], toolCall: ToolCall): MessagePart[] {
  return [
    ...cloneParts(parts),
    {
      type: "tool-call",
      toolCallId: toolCall.id,
      toolName: toolCall.name,
      args: toolCall.args ?? {},
      argsText: stringifyToolArgs(toolCall.args),
    },
  ];
}

export function appendDataPart(parts: MessagePart[], name: string, data: unknown): MessagePart[] {
  return [...cloneParts(parts), { type: "data", name, data }];
}

export function markRunningToolParts(
  parts: MessagePart[],
  status: ToolStatusLike,
  error?: string
): MessagePart[] {
  return parts.map((part) => {
    if (part.type !== "tool-call" || part.result !== undefined || part.isError) {
      return part;
    }

    if (status === "done") {
      return { ...part, result: { status: "done" } };
    }

    return {
      ...part,
      result: { status: "error", message: error ?? "Tool execution failed" },
      isError: true,
    };
  });
}

type ToolStatusLike = "done" | "error";

function toSourcePart(source: RetrievalSource, index: number): Extract<MessagePart, { type: "source" }> {
  const pageSuffix = source.page ? `#page=${source.page}` : "";
  return {
    type: "source",
    sourceType: "url",
    id: `${source.source}:${source.page ?? "na"}:${index}`,
    url: `source://${encodeURIComponent(source.source)}${pageSuffix}`,
    title: source.page ? `${source.source} (p. ${source.page})` : source.source,
  };
}

export function appendSourceParts(parts: MessagePart[], sources: RetrievalSource[]): MessagePart[] {
  const next = cloneParts(parts);
  const existing = new Set(
    next
      .filter((part): part is Extract<MessagePart, { type: "source" }> => part.type === "source")
      .map((part) => part.id)
  );

  sources.forEach((source, index) => {
    const part = toSourcePart(source, index);
    if (!existing.has(part.id)) {
      existing.add(part.id);
      next.push(part);
    }
  });

  return next;
}

export function extractTextFromParts(parts: MessagePart[]): string {
  return parts
    .filter((part): part is Extract<MessagePart, { type: "text" }> => part.type === "text")
    .map((part) => part.text)
    .join("");
}

export function deriveToolCallsFromParts(parts: MessagePart[]): ToolCall[] {
  return parts.flatMap((part) => {
    if (part.type !== "tool-call") return [];
    return [
      {
        id: part.toolCallId,
        name: part.toolName,
        status: part.isError ? "error" : part.result !== undefined ? "done" : "running",
        args: part.args,
      },
    ];
  });
}

export function deriveThinkingEntriesFromParts(parts: MessagePart[]): ThinkingEntry[] {
  return parts.flatMap((part): ThinkingEntry[] => {
    if (part.type === "reasoning") {
      return [{ type: "text" as const, content: part.text }];
    }
    if (part.type === "tool-call") {
      return [{
        type: "tool" as const,
        toolCall: {
          id: part.toolCallId,
          name: part.toolName,
          status: part.isError ? "error" : part.result !== undefined ? "done" : "running",
          args: part.args,
        },
      }];
    }
    return [];
  });
}

export function deriveSourcesFromParts(parts: MessagePart[]): RetrievalSource[] {
  return parts.flatMap((part) => {
    if (part.type !== "source") return [];
    return [{
      source: part.title ?? part.url,
      page: null,
      score: 0,
    }];
  });
}

export function buildAssistantPartsFromLegacy(message: Pick<Message, "content" | "toolCalls" | "thinkingEntries" | "sources">): MessagePart[] {
  let parts: MessagePart[] = [];

  for (const entry of message.thinkingEntries) {
    if (entry.type === "text") {
      parts = appendReasoningPart(parts, entry.content);
    } else {
      parts = appendToolCallPart(parts, entry.toolCall);
      if (entry.toolCall.status === "done") {
        parts = markRunningToolParts(parts, "done");
      } else if (entry.toolCall.status === "error") {
        parts = markRunningToolParts(parts, "error");
      }
    }
  }

  if (parts.length === 0 && message.toolCalls.length > 0) {
    for (const toolCall of message.toolCalls) {
      parts = appendToolCallPart(parts, toolCall);
      if (toolCall.status === "done") {
        parts = markRunningToolParts(parts, "done");
      } else if (toolCall.status === "error") {
        parts = markRunningToolParts(parts, "error");
      }
    }
  }

  if (message.content) {
    parts = appendTextPart(parts, message.content);
  }

  if (message.sources.length > 0) {
    parts = appendSourceParts(parts, message.sources);
  }

  return parts;
}
