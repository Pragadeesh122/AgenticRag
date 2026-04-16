# Frontend Overview

## Related Frontend Docs

- [Streaming](streaming.md) — SSE event flow, message lifecycle, streaming state updates
- [Components](components.md) — markdown rendering, quiz/chart/mermaid components, UI composition

## Stack

- **Next.js 16** — App Router with React Server Components
- **React 19** — with `useState`/`useEffect` for state management (no global store)
- **TypeScript** — strict mode
- **Tailwind CSS v4** — utility-first styling
- **Fonts** — Geist Sans (body), Geist Mono (code), Instrument Serif (landing accents)

## Route Structure

| Path | Component | Description |
|------|-----------|-------------|
| `/` | `LandingPage` | Marketing landing page |
| `/chat` | `ChatPage` | General chat with tools |
| `/auth/signin` | Sign-in page | Email/password + Google OAuth |
| `/auth/forgot-password` | Forgot password page | Recovery request flow |
| `/auth/reset-password` | Reset password page | Recovery completion flow |
| `/projects/[id]` | `ProjectPage` | Project chat with document upload and agent selection |
| `/settings` | Settings page | Account security, password change, password recovery |

## Component Tree

```
RootLayout (fonts, Providers)
├── LandingPage (white theme, animated demo)
├── ChatPage (dark theme)
│   ├── Sidebar (session list, create/delete)
│   └── ChatArea
│       ├── MessageBubble[]
│       │   ├── ThinkingBlock (tool calls, reasoning)
│       │   ├── QuizRenderer (structured quiz JSON)
│       │   ├── ChartRenderer
│       │   │   ├── MermaidDiagram
│       │   │   ├── LineChart / RadarChart
│       │   │   └── ComparisonTable
│       │   └── Streamdown (markdown rendering)
│       └── ChatInput (textarea + submit)
└── ProjectPage (dark theme)
    ├── ProjectSidebar (documents, upload, search, sessions)
    └── ChatArea (same as above + agent selector + sources)
```

## Authentication

Cookie-based JWT authentication via FastAPI-Users:

1. `proxy.ts` guards protected routes like `/chat`, `/projects/*`, and `/settings`
2. Protected route pages fetch their initial data on the Next.js server via `lib/server-api.ts`
3. The `AuthProvider` still manages browser-side auth state after hydration
4. Login sets an `httponly` cookie (`app_token`) — no tokens in localStorage
5. All browser API calls include `credentials: "include"` to send the cookie

Google OAuth redirects through `/auth/google/authorize` → Google → `/api/auth/callback/google`.

## API Communication

The frontend uses a hybrid access pattern:

- **Browser-side interactive calls** go directly to FastAPI through `lib/api.ts`
- **Initial protected page loads** fetch from FastAPI on the Next.js server through `lib/server-api.ts`

`apiFetch()` in `lib/api.ts` strips the `/api` prefix from paths and sends requests to the backend URL (`NEXT_PUBLIC_API_URL`):

```
apiFetch("/api/chat/stream", ...)         → FastAPI: POST /chat/stream
apiFetch("/api/chat/sessions", ...)       → FastAPI: /chat/sessions
apiFetch("/auth/login", ...)              → FastAPI: POST /auth/login
```

On the SSR path, the Next.js server forwards the incoming cookie to FastAPI using `INTERNAL_API_URL` when running inside Docker. SSE streams are still read directly from the FastAPI response in the browser.

All persistence (sessions, messages, projects) is handled by SQLAlchemy in the backend — no ORM or database access in the frontend.

## State Management

No global state library. Each page component manages its own state:

- **`ChatPage`** — sessions list, active session, messages, streaming state
- **`ProjectPage`** — same, plus documents list, selected agent, retrieval sources, and retrieval-only project search results

Session switching, message sending, and streaming are all coordinated through React state in the page component, passed down as props.

## Design System

### Chat UI (dark theme)

| Token | Value |
|-------|-------|
| Background | `#1a1a1a` |
| Text | Zinc scale (`zinc-200` body, `zinc-400` secondary) |
| Accent | Emerald `#10b981` |
| User messages | Violet background (`violet-600/15`) with rounded corners |
| Assistant messages | Full-width, no background |
| Markdown | Streamdown with Shiki syntax highlighting |

### Landing Page (white theme)

| Token | Value |
|-------|-------|
| Background | `#ffffff` |
| Primary text | `#0a0a0a` |
| Secondary text | `#525252` |
| Hero | Animated mesh blobs (violet/indigo/cyan) with backdrop blur |
| CTA | Solid black primary, gray ghost secondary |
| Bento grid | White cards with `#e5e7eb` gap lines |

## See Also

- [Streaming](streaming.md)
- [Components](components.md)
