# Frontend Overview

## Stack

- **Next.js 15** — App Router with React Server Components
- **React 19** — with `useState`/`useEffect` for state management (no global store)
- **TypeScript** — strict mode
- **Tailwind CSS v4** — utility-first styling
- **Fonts** — Geist Sans (body), Geist Mono (code), Instrument Serif (landing accents)

## Route Structure

| Path | Component | Description |
|------|-----------|-------------|
| `/` | `LandingPage` | Marketing page (unauthenticated) or redirect to `/chat` |
| `/chat` | `ChatPage` | General chat with tools |
| `/auth/signin` | Sign-in page | Email/password + Google OAuth |
| `/projects/[id]` | `ProjectPage` | Project chat with document upload and agent selection |
| `/settings` | Settings page | User memory management, password change |

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
    ├── ProjectSidebar (session list)
    ├── DocumentsPanel (upload, status, delete)
    └── ChatArea (same as above + agent selector + sources)
```

## Authentication

Cookie-based JWT authentication via FastAPI-Users:

1. The `AuthProvider` component wraps the app and manages auth state
2. On page load, it calls `GET /users/me` to check authentication
3. If unauthenticated, the landing page is shown
4. Login sets an `httponly` cookie (`app_token`) — no tokens in localStorage
5. All API calls include `credentials: "include"` to send the cookie

Google OAuth redirects through `/auth/google/authorize` → Google → `/api/auth/callback/google`.

## API Communication

The frontend talks to two backends:

### Direct to FastAPI (Python)

`apiFetch()` in `lib/api.ts` makes direct calls to the Python backend for:
- Auth (login, register, OAuth)
- Session management (create, restore, delete backend sessions)
- Memory management (get, update)
- Project CRUD

### Through Next.js API Routes (proxy)

SSE streaming and Prisma-backed persistence go through Next.js API routes:
- `/api/chat/stream` — proxies SSE to `POST /chat/stream` on FastAPI
- `/api/chat/sessions` — CRUD on `ChatSession` via Prisma
- `/api/chat/sessions/[id]/messages` — message persistence via Prisma
- `/api/chat/messages/[id]` — metadata PATCH (quiz state, agent name)
- `/api/projects/[id]/chat` — proxies SSE to `POST /projects/{id}/chat`

Why proxy? The Next.js routes handle cookie forwarding and add the Prisma persistence layer. The browser never connects to FastAPI directly.

## State Management

No global state library. Each page component manages its own state:

- **`ChatPage`** — sessions list, active session, messages, streaming state
- **`ProjectPage`** — same, plus documents list, selected agent, retrieval sources

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
