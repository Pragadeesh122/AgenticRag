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

The frontend talks **directly** to the FastAPI backend for everything — there are no Next.js API routes or server-side proxies.

`apiFetch()` in `lib/api.ts` strips the `/api` prefix from paths and sends requests to the backend URL (`NEXT_PUBLIC_API_URL`):

```
apiFetch("/api/chat/stream", ...)         → FastAPI: POST /chat/stream
apiFetch("/api/chat/sessions", ...)       → FastAPI: /chat/sessions
apiFetch("/auth/login", ...)              → FastAPI: POST /auth/login
```

Auth cookies (`httponly`, `samesite=lax`) are sent via `credentials: "include"` on every request. SSE streams are read directly from the FastAPI response.

All persistence (sessions, messages, projects) is handled by SQLAlchemy in the backend — no ORM or database access in the frontend.

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
