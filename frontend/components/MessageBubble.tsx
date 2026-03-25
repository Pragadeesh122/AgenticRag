"use client";

import {useMemo} from "react";
import {Streamdown} from "streamdown";
import {code} from "@streamdown/code";
import "streamdown/styles.css";
import type {Message} from "@/lib/types";
import ToolIndicator from "./ToolIndicator";

const streamdownPlugins = {code};

/**
 * Preprocess LLM output to fix common markdown issues before Streamdown renders it.
 * LLMs often omit newlines between headings, lists, and paragraphs.
 */
/**
 * Fix code blocks where the LLM concatenates statements onto a single line.
 * Only operates on content between ``` fences — safe from false positives.
 */
/**
 * Add indentation to code that was split from a single line.
 * Only runs on lines that have no leading whitespace (i.e. were concatenated).
 */
function addIndentation(code: string): string {
  const lines = code.split("\n");
  const result: string[] = [];
  let indent = 0;

  // Top-level: resets indent to 0
  const topLevel = /^(from |import |class |export |const |let |var |function |interface |type |app\.|\/\/|#|package |use |mod |struct |impl |trait |pub )/;
  // Decorators: reset to 0
  const isDecorator = (s: string) => s.startsWith("@");
  // Function definitions across languages: reset to 0
  const isFuncDef = (s: string) => /^(async )?def |^func |^fn |^pub fn /.test(s);
  // Ends with colon = opens a block
  const endsWithColon = (s: string) => /:\s*$/.test(s) && !/['"][^'"]*:\s*$/.test(s);

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trimStart();

    // Skip empty lines or already-indented lines
    if (trimmed === "" || line !== trimmed) {
      result.push(line);
      if (line !== trimmed && endsWithColon(trimmed)) {
        indent = Math.floor((line.length - trimmed.length) / 2) + 1;
      }
      continue;
    }

    // Decorators, top-level, and function defs all reset to indent 0
    if (isDecorator(trimmed) || topLevel.test(trimmed) || isFuncDef(trimmed)) {
      indent = 0;
      result.push(trimmed);
      if (endsWithColon(trimmed)) {
        indent = 1;
      }
      continue;
    }

    // Closing braces: dedent
    if (trimmed === "}" || trimmed === "});" || trimmed === "});") {
      indent = Math.max(0, indent - 1);
      result.push("  ".repeat(indent) + trimmed);
      continue;
    }

    // Body statements or anything else inside a block
    if (indent > 0) {
      result.push("  ".repeat(indent) + trimmed);
    } else {
      result.push(trimmed);
    }

    // Opening brace or colon increases indent
    if (trimmed.endsWith("{")) {
      indent++;
    } else if (endsWithColon(trimmed)) {
      indent++;
    }
  }

  return result.join("\n");
}

/**
 * Insert blank lines between logical code sections for readability.
 * Adds spacing before class/function/decorator blocks and after import groups.
 */
function addBlankLines(code: string): string {
  const lines = code.split("\n");
  const result: string[] = [];

  const isImport = (s: string) => /^(from |import |use |package )/.test(s.trimStart());
  const isClassOrFunc = (s: string) => /^(class |def |async def |func |fn |pub fn |struct |impl |trait )/.test(s.trimStart());
  const isDecorator = (s: string) => s.trimStart().startsWith("@");
  const isComment = (s: string) => /^\s*(\/\/|#)/.test(s);
  const isBlank = (s: string) => s.trim() === "";
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const prev = i > 0 ? lines[i - 1] : null;

    if (prev !== null && !isBlank(prev) && !isBlank(line)) {
      // Blank line before decorator/class/function if previous line isn't a decorator
      if ((isDecorator(line) || isClassOrFunc(line)) && !isDecorator(prev)) {
        result.push("");
      }
      // Blank line when transitioning from imports to non-imports
      else if (isImport(prev) && !isImport(line)) {
        result.push("");
      }
      // Blank line before a comment that precedes a function/class
      else if (isComment(line) && i + 1 < lines.length && (isClassOrFunc(lines[i + 1]) || isDecorator(lines[i + 1]))) {
        result.push("");
      }
    }

    result.push(line);
  }

  return result.join("\n");
}

function fixCodeBlocks(text: string): string {
  return text.replace(
    /(```\w*\n)([\s\S]*?)(```)/g,
    (_match, open: string, code: string, close: string) => {
      // Phase 1: Split concatenated statements onto separate lines
      const split = code
        // Split before single-line comments: // or #
        .replace(/([^\n:\/])(\/\/\s)/g, "$1\n$2")
        .replace(/([^\n#])(#\s)/g, "$1\n$2")
        // Split before Python/JS/Go/Rust keywords
        .replace(/([^\n])((?:from|import|class|def|async def|return|if|elif|else|for|while|try|except|finally|with|raise|yield|assert)\s)/g, "$1\n$2")
        // Split before decorators: @app.get, @router, etc.
        .replace(/([^\n])(@\w)/g, "$1\n$2")
        // Split before export/const/let/var/function (JS/TS)
        .replace(/([^\n])((?:export|const|let|var|function|interface|type)\s)/g, "$1\n$2")
        // Split before Go keywords: func, package, type, var
        .replace(/([^\n])((?:func|package)\s)/g, "$1\n$2")
        // Split before Rust keywords: fn, let, pub, use, struct, impl, mod, trait
        .replace(/([^\n])((?:fn |pub |use |struct |impl |mod |trait |match |loop |mut )\s*)/g, "$1\n$2")
        // Split before print/console.log/fmt.
        .replace(/([^\n])((?:print|console\.|fmt\.)\s*)/g, "$1\n$2")
        // Split before app.use/app.get/app.post etc. (but not after @ decorator)
        .replace(/([^\n@])(app\.(?:use|get|post|put|delete|patch|listen)\()/g, "$1\n$2")
        // Split before http.HandleFunc/http.ListenAndServe (Go)
        .replace(/([^\n])(http\.(?:HandleFunc|ListenAndServe|Handle)\()/g, "$1\n$2")
        // Split after closing }) or }); followed by content
        .replace(/(}\))\s*([a-zA-Z\/])/g, "$1\n$2")
        .replace(/(}\);)\s*([a-zA-Z\/])/g, "$1\n$2")
        // Split after closing } followed by a keyword
        .replace(/(})\s*((?:from|import|class|def|const|let|var|function|export|async|func|fn|pub|http|app)\s)/g, "$1\n$2")
        // Split block body after => { or ) { when followed by code
        .replace(/((?:\) =>|=>|\))\s*\{)\s*([a-zA-Z])/g, "$1\n  $2")
        // Split after semicolons followed by code (statement boundaries)
        .replace(/(;)\s*([a-zA-Z\/])/g, "$1\n$2")
        // Split before closing } after a statement (e.g. "next(); })" or "return x; }")
        .replace(/(;)\s*(}\)?;?)/g, "$1\n$2")
        // Split Python type-hint fields: "str name:" or "float price:" or "int quantity:"
        .replace(/\b(str|int|float|bool|bytes|None|Any|Optional|List|Dict|Set|Tuple|list|dict|set|tuple)(\s*(?:\[.*?\])?\s+)([a-z_]\w*\s*[=:])/g, "$1\n$3")
        // Split bash commands concatenated together (e.g. "pip install foobarcmd --flag")
        .replace(/\b(pip install [^\n]+?)((?:python|python3|uvicorn|node|npm|npx|cargo|go run|java|ruby|perl|dotnet)\s)/g, "$1\n$2")
        .replace(/\b(npm (?:install|init)[^\n]*?)((?:node|npx|npm run|npm start)\s)/g, "$1\n$2");

      // Phase 2: Add indentation based on block structure
      // Phase 3: Insert blank lines between logical sections
      const fixed = addBlankLines(addIndentation(split));
      return open + fixed + close;
    }
  );
}

function normalizeMarkdown(text: string): string {
  // Phase 0: Fix code fences — LLM often puts ``` on the same line as content
  const normalized = text
    // Closing ``` stuck to end of code line: "content```" -> "content\n```"
    .replace(/([^\n`])```/g, "$1\n```")
    // Closing ``` stuck to start of next content: "```## heading" -> "```\n## heading"
    .replace(/```([^\n`\w])/g, "```\n$1")
    // Closing ``` stuck to start of next code block: "``````ts" -> "```\n```ts"
    .replace(/```(\n?)```/g, "```\n```")
    // Opening ```lang stuck to next line: "```tsimport" -> "```ts\nimport"
    // Use a known-language list to avoid greedy \w+ eating the code
    .replace(/```(python|py|javascript|js|typescript|ts|java|cpp|c|cs|csharp|ruby|rb|go|rust|rs|bash|sh|shell|zsh|sql|html|css|scss|json|yaml|yml|xml|php|swift|kotlin|scala|r|perl|lua|dart|elixir|haskell|ocaml|jsx|tsx|markdown|md|diff|graphql|toml|ini|env|dotenv|dockerfile|docker|makefile|cmake|powershell|ps1|matlab|plaintext|text|txt|vue|svelte|astro|prisma|proto|nginx|conf|cfg|log)([^\n])/gi, "```$1\n$2")
    // Fix headings missing space after # (e.g., "###1." -> "### 1.")
    .replace(/^(#{1,6})([^\s#])/gm, "$1 $2")
    // Newline before ## or ### headings that appear mid-text
    .replace(/([^\n#])(#{1,6}\s)/g, "$1\n$2")
    // Newline before "- **" (bold list items) appearing mid-text
    .replace(/([^\n])(- \*\*)/g, "$1\n$2")
    // Newline after colon followed by "- " (list after label)
    .replace(/:- /g, ":\n- ")
    // Newline between adjacent plain list items after punctuation
    .replace(/([.!?,;])- /g, "$1\n- ")
    // Split "text- Item" patterns (letter/digit/paren before dash = likely new list item)
    .replace(/([a-zA-Z0-9)\]])- /g, "$1\n- ")
    // Split concatenated numbered list items: "step1. Next" or "step2. Another"
    .replace(/([a-zA-Z])(\d+\.\s)/g, "$1\n$2")
    // Split numbered list items after digits (e.g. "$31,062.85 2. Noise" or "852. Noise")
    .replace(/([0-9])\s*(\d+\.\s)/g, "$1\n$2")
    // Split numbered list items after bold-wrapped text (e.g. "**31,062.85**2. **Noise")
    .replace(/(\*\*)\s*(\d+\.\s)/g, "$1\n$2")
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

  // Phase 3: Fix concatenated statements inside code blocks
  return fixCodeBlocks(result.join("\n"));
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
                plugins={streamdownPlugins}
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
