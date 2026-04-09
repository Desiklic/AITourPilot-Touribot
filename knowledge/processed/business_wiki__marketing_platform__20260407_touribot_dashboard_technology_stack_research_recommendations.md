# 20260407-touribot-dashboard-technology-stack-research-recommendations

*Source: Business Wiki / marketing-platform/20260407-touribot-dashboard-technology-stack-research-recommendations.html*

## Executive Summary

This report answers 8 technical questions required to build the TouriBot Dashboard — a campaign command center for museum outreach with CRM pipeline, AI chat, analytics, calendar, task board, and settings views. All recommendations favor the developer's existing stack: Next.js, Tailwind CSS, Vercel hosting, and Python backend.

**Recommended core stack:**
- **Framework:** Next.js 15 (App Router) + shadcn/ui as the base component system
- **Drag-and-drop:** @dnd-kit/core + @dnd-kit/sortable (v6+)
- **Chat:** Vercel AI SDK v6 useChat hook, with a FastAPI SSE backend
- **Charts:** Recharts v3.8+ (already bundled in shadcn/ui Charts)
- **Calendar:** FullCalendar v6 for React (event-aware) or react-big-calendar v1
- **Data fetching:** TanStack Query v5 for REST; native EventSource for SSE streams
- **Backend:** FastAPI 0.135 + sse-starlette 3.3 + aiosqlite
- **Theme:** next-themes with Tailwind class strategy

---

## 1. Next.js Dashboard Frameworks & Templates

### The Best Starting Point: shadcn/ui

shadcn/ui is the strongest choice for this project. It is not a traditional npm library — it is a collection of copy-paste React components built on Radix UI primitives and styled with Tailwind CSS. With 112k+ GitHub stars, it is the dominant React component system in 2026.

**Why shadcn/ui for TouriBot Dashboard:**
- Ships pre-built dashboard blocks you can scaffold instantly: `npx shadcn add dashboard-01`
- The dashboard-01 block includes a **sidebar, area charts, and a data table** — exactly the layout needed
- Built-in **Calendar** component (date picker via React DayPicker)
- **Sidebar** component with collapsible-to-icons mode (sidebar-07 block)
- **Data Table** built on TanStack Table v8 — handles sorting, filtering, pagination for 50–150 leads
- **Charts** built on Recharts — area, bar, line, pie, radar, radial charts all available
- `npx shadcn add` installs only what you need — no bundle bloat

**Bootstrap command:**
```
npx create-next-app@latest touribot-dashboard
npx shadcn init
npx shadcn add dashboard-01 sidebar-07 table calendar
```

### Alternatives Evaluated

**Tremor** — Open-source React component library joining Vercel. Excellent for pure analytics dashboards (KPI cards, donut charts, area charts, filter components). Has 35+ components. Best used as a **complement** to shadcn/ui for the analytics view, not as the primary framework.

**Refine (@refinedev/core v5.0.12, released April 2026)** — A React meta-framework for CRUD-heavy apps. Ships a fully-functional CRM demo application. Supports Next.js SSR. Best for teams that want auto-generated CRUD UIs and backend-agnostic connectors. **Overhead is high** for a single-developer local tool. Revisit if the dashboard needs to support multiple users with access control.

**HeroUI (v3.0.2)** — 75+ components, built with Tailwind v4 and React Aria. A full replacement for shadcn/ui if Radix UI primitives are a concern, but adds complexity. Not recommended unless specific accessibility requirements demand React Aria.

**Vercel v0** — Vercel's AI-powered UI generator. Generates shadcn/ui components from prompts. Useful for quickly prototyping specific views (e.g., the kanban board or the chat interface). Financial and crypto dashboard templates have 20k–28k views. Use v0 to generate initial component drafts, then customize.

### Tailwind CSS Templates

For a custom look without a component library, **Tailwind UI** (paid, ~$300) offers professional dashboard templates. The free alternative is using shadcn/ui blocks as the template foundation.

---

## 2. CRM Pipeline Visualization

### Drag-and-Drop: @dnd-kit (Primary Recommendation)

**@dnd-kit/core + @dnd-kit/sortable** is the right choice for the TouriBot kanban board.

- **react-beautiful-dnd is officially deprecated** (Atlassian archived the repo). The npm package is marked deprecated.
- **@dnd-kit** provides `useSortable`, `DndContext`, and `SortableContext` — the three primitives for a kanban board where leads move between pipeline stages.
- Supports drag between lists, vertical and horizontal movement, touch and pointer events.
- First-class React support via hooks.
- Framework-agnostic core — no React-specific lock-in.

**@hello-pangea/dnd v18.0.1** (released February 2025) — a community-maintained fork of react-beautiful-dnd, keeping the `DragDropContext / Droppable / Draggable` API. Actively maintained by Gabriel Santerre and Reece Carolan. **Use this if your team already knows react-beautiful-dnd** and wants minimal migration cost. It explicitly supports movement between lists, which is the core kanban requirement. Grid layouts are not yet supported.

**Pragmatic drag and drop** (by Atlassian, powers Trello and Jira) — ~4.7kB core, headless, framework-agnostic. The most powerful option but requires more implementation work. Recommended only if the kanban needs to scale to thousands of cards with virtualization.

### Kanban vs. Table View for 50–150 Leads

For a 50–150 lead CRM at the museum outreach scale, **provide both views with a toggle**:

- **Kanban view** for daily workflow — visualizing which leads are in which pipeline stage at a glance. Works well at this scale (3–6 columns, 10–40 cards each). Industry standard: HubSpot, Pipedrive, folk.app all default to kanban for active pipeline management.
- **Table view** for bulk operations — sorting by last contact date, filtering by museum type, exporting. shadcn/ui Data Table (TanStack Table v8) handles this with built-in sort, filter, and pagination.

The toggle pattern (a pair of icon buttons: grid/list) is a single state variable that conditionally renders `<KanbanBoard>` or `<LeadsTable>`.

### Pipeline Stages for Museum Outreach

Typical stages: **Prospect → Contacted → Replied → Demo Scheduled → Proposal Sent → Won / Lost**

Each card should show: museum name, city, contact name, last activity date, and a color-coded status dot.

---

## 3. Chat Interface Patterns

### Vercel AI SDK v6 (Primary Recommendation)

The **Vercel AI SDK v6** (`ai`, `@ai-sdk/react`) is the production standard for React chat UIs in 2026. It runs on Next.js App Router natively.

**Key hooks:**
- `useChat` — manages the full message lifecycle: send, stream, display, persist. Returns `messages`, `input`, `handleSubmit`, `status`, `stop`, `regenerate`.
- `useCompletion` — for single-turn text completions (e.g., email draft suggestions).
- `useObject` — for streaming structured objects (e.g., auto-filling a lead record from a conversation).

**Backend pattern (Next.js route handler):**
```
// app/api/chat/route.ts
import { streamText } from 'ai'
import { openai } from '@ai-sdk/openai'

export async function POST(req) {
  const { messages } = await req.json()
  const result = streamText({ model: openai('gpt-4o'), messages })
  return result.toUIMessageStreamResponse()
}
```

**Frontend:**
```
const { messages, input, handleSubmit, status } = useChat({
  api: '/api/chat',
  id: threadId  // unique thread identifier for multi-thread support
})
```

**IMPORTANT for TouriBot:** TouriBot's AI runs in Python, not TypeScript. The `useChat` hook's `api` option can point to any URL — including a FastAPI endpoint at `http://localhost:8001/chat/stream`. The Python backend must respond with SSE in the AI SDK's Data Stream Protocol format, OR you use the simpler `streamProtocol: 'text'` option and return plain text/event-stream.

### Thread Management

- Each conversation gets a unique `id` passed to `useChat({ id: threadId })`.
- Store threads in SQLite as a `conversations` table with `id`, `museum_id`, `created_at`, `title`.
- Store messages in a `messages` table with `conversation_id`, `role`, `content`, `created_at`.
- Load thread history from the API and pass to `useChat` via `initialMessages` prop.
- A sidebar list of threads sorted by last activity mirrors the ChatGPT/Claude pattern.

### Streaming AI Responses

**SSE is the right protocol for AI chat streaming**, not WebSocket. The reasons:
- SSE is unidirectional (server → client) — which is all you need for LLM token streaming.
- SSE uses standard HTTP — no special proxy configuration needed for local dev or Vercel.
- Built-in reconnection and keep-alive.
- The Vercel AI SDK's Data Stream Protocol uses SSE format.

WebSocket is appropriate for bidirectional real-time communication (e.g., collaborative editing, live presence). It is overkill for a chat interface where only the user sends messages and the server streams tokens.

### Reference Chat UI Implementations

- **ChatGPT Next Web** — Next.js + TypeScript, client-side storage, stream-based responses, ~100kB initial load. Good reference for thread sidebar + streaming message patterns.
- **Chatbot UI** — Next.js + Supabase, database-driven message persistence. Good reference for multi-device persistence patterns.
- **LobeChat** — More complex agent-based architecture, branching conversations, artifact support. Useful for inspiration on advanced features.

---

## 4. Real-Time Data & WebSocket/SSE Patterns

### Python Backend → Next.js Frontend

**Architecture: FastAPI + sse-starlette on a separate port (8001), with Next.js fetching via TanStack Query + native EventSource.**

For a local tool, run two processes:
1. `next dev` on port 3000 (or `next start` in production)
2. `uvicorn main:app --port 8001` for the FastAPI API server

Add a `next.config.js` rewrite to proxy API calls through Next.js:
```
rewrites: [{ source: '/api/backend/:path*', destination: 'http://localhost:8001/:path*' }]
```

### SSE Streaming from FastAPI

**sse-starlette v3.3.4** (released March 2026) is the production package for SSE in FastAPI. It handles W3C compliance, client disconnect detection, keep-alive pings, and graceful shutdown.

```python
from sse_starlette.sse import EventSourceResponse
import asyncio

@app.get('/chat/stream')
async def chat_stream(message: str):
    async def generate():
        async for token in touribot.stream(message):
            yield {'data': token}
    return EventSourceResponse(generate())
```

On the React side, use the native `EventSource` API or the `useChat` hook with `streamProtocol: 'text'`:
```
const source = new EventSource('/api/backend/chat/stream?message=hello')
source.onmessage = (e) => appendToken(e.data)
```

### TanStack Query v5 for REST Data

For non-streaming data (leads list, analytics, calendar events), **TanStack Query v5** is the recommended data fetching layer:
- Automatic background refetch (configurable `refetchInterval` for near-real-time updates)
- Query invalidation after mutations (e.g., move a lead to a new stage → invalidate leads query)
- Optimistic updates for drag-and-drop kanban without waiting for the server
- Compatible with Next.js App Router via `QueryClientProvider` in a client boundary

**SWR** (by Vercel) is a simpler alternative with a smaller API surface. For a local dashboard with moderate complexity, either works. TanStack Query wins on features for a multi-view dashboard with interdependent queries.

### WebSocket (When to Use)

Use WebSocket for:
- **Live collaboration** (multiple users editing the same kanban board)
- **Push notifications** from TouriBot when a new reply arrives (email webhook triggers)

FastAPI WebSocket pattern (native, no extra packages):
```python
@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    manager.add(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.remove(websocket)
```

**For TouriBot's initial version, SSE is sufficient.** Add WebSocket only when multi-user collaboration is required.

---

## 5. Statistics & Charts

### Recharts v3.8.1 (Primary Recommendation)

**Recharts** is the chart library built into shadcn/ui Charts. Since shadcn/ui is the base component system, using Recharts avoids adding a second charting dependency.

- Current version: **3.8.1** (released March 25, 2025, last patch focused on tooltip stability and memory leak fixes)
- Chart types available via shadcn/ui: Area, Bar, Line, Pie, Radar, Radial
- All charts are React components using SVG rendering
- Responsive via `ResponsiveContainer`
- Good for all standard outreach analytics charts

**Note:** Recharts does not have a built-in funnel chart. For pipeline funnel visualization (lead count per stage), use a **horizontal bar chart** sorted by stage order — this is the standard approach (HubSpot, Pipedrive both use this).

### Key Metrics for a Museum Outreach Dashboard

**Campaign Metrics:**
- Total emails sent (daily/weekly bar chart)
- Reply rate percentage (line chart over time)
- Open rate (if tracked via pixel/link click)
- Positive reply rate vs. bounce/unsubscribe rate

**Pipeline Metrics:**
- Lead count per stage (funnel bar chart)
- Stage conversion rates (leads moving from Contacted → Replied → Demo)
- Average days in each stage (bottleneck identification)
- Win rate (Proposal Sent → Won)

**Activity Metrics:**
- Follow-ups completed vs. overdue (progress/radial chart)
- Demos scheduled this month
- New leads added per week

### Chart.js as Alternative

Chart.js v4 (Canvas-based, 8 chart types including funnel via plugin) is a valid alternative if SVG charts have performance issues at scale. The `react-chartjs-2` wrapper integrates it into React. However, since Recharts is already bundled with shadcn/ui, switching to Chart.js adds bundle weight for marginal benefit.

---

## 6. Calendar Component

### FullCalendar v6 for React (Primary Recommendation)

**FullCalendar v6** is the right choice for displaying a real calendar with events (follow-up dates, demo schedules, email send dates).

- React package: `@fullcalendar/react` + `@fullcalendar/daygrid` + `@fullcalendar/timegrid`
- MIT licensed, v7.0.0-beta.8 available
- Supports month view, week view, day view, agenda/list view
- Events with titles, colors, start/end times
- `dateClick` callback for creating new events
- `eventClick` callback for viewing/editing events
- Custom event rendering via `eventContent` prop

```
import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'

<FullCalendar
  plugins={[dayGridPlugin]}
  initialView='dayGridMonth'
  events={followUpEvents}
  eventContent={renderEventContent}
/>
```

**Event types for TouriBot calendar:**
- Follow-up due (yellow/amber)
- Demo scheduled (green)
- Email campaign send date (blue)
- Response deadline (red)

### react-big-calendar (Alternative)

**react-big-calendar** is the most-downloaded React calendar library. Supports month, week, day, and agenda views. More customizable styling than FullCalendar. The latest version is actively maintained. Use this if FullCalendar's CSS is hard to override with Tailwind.

### shadcn/ui Calendar Component (Not Sufficient)

The shadcn/ui Calendar component is a **date picker only** (built on React DayPicker). It shows a month grid for selecting dates but **cannot display events**. Do not use this as the primary calendar view — use it only for date input fields (e.g., scheduling a follow-up date in a lead detail modal).

### Google Calendar Integration

For syncing TouriBot calendar events to Google Calendar, use the Google Calendar API v3. Requires OAuth 2.0. For a local tool, a service account with domain-wide delegation is the simplest approach. This is a Phase 2 feature — not required for the MVP.

---

## 7. Dark / Light Theme

### next-themes (The Standard Solution)

**next-themes** is the universally recommended theme solution for Next.js + Tailwind CSS. "Perfect dark mode in 2 lines of code."

**Setup:**
```
npm install next-themes
```

In `app/layout.tsx`:
```
import { ThemeProvider } from 'next-themes'

export default function RootLayout({ children }) {
  return (
    <html suppressHydrationWarning>
      <body>
        <ThemeProvider attribute='class' defaultTheme='system' enableSystem>
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
```

The `attribute='class'` setting applies `class='dark'` to the `<html>` element when dark mode is active, enabling Tailwind's `dark:` prefix utilities throughout the app.

**In `tailwind.config.ts`:**
```
darkMode: 'class'
```

**Theme toggle component (shadcn/ui pattern):**
```
import { useTheme } from 'next-themes'
const { theme, setTheme } = useTheme()
<Button onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
  {theme === 'dark' ? <Sun /> : <Moon />}
</Button>
```

**Key features:**
- No flash on page load (SSR-safe via `suppressHydrationWarning`)
- Respects `prefers-color-scheme` system preference
- Cross-tab synchronization
- Stores preference in localStorage

### Theme-Aware Component Design

All shadcn/ui components use CSS variables defined in `:root` and `.dark` selectors. This means theme support is automatic for any shadcn/ui component. Custom components should use semantic color tokens (`bg-background`, `text-foreground`, `border-border`) rather than raw Tailwind color values (`bg-white`, `text-gray-900`).

---

## 8. Python Backend API Design

### FastAPI (Clear Winner Over Flask)

**FastAPI v0.135.3** (released April 1, 2026) is the right choice for TouriBot's API layer.

**FastAPI advantages over Flask:**
- **Async-native:** handles concurrent chat streams without blocking
- **Built-in WebSocket support:** no extra package
- **Automatic OpenAPI docs** at `/docs` — useful for debugging during development
- **Pydantic validation** — request/response models are type-safe
- **SSE streaming** via sse-starlette is clean and well-supported
- Performance comparable to Node.js

**Flask advantages:** Simpler for pure synchronous REST APIs. If TouriBot's Python code is fully synchronous and the developer prefers Flask, it works — but you lose async streaming support.

### SQLite Access in FastAPI

TouriBot's `leads.db` and `memory.db` are SQLite databases. For an async FastAPI app:

**Option A: aiosqlite (simple, direct)**
```python
import aiosqlite

@app.get('/leads')
async def get_leads():
    async with aiosqlite.connect('leads.db') as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM leads ORDER BY created_at DESC') as cur:
            rows = await cur.fetchall()
            return [dict(row) for row in rows]
```

**Option B: SQLAlchemy async (more structure)**
Use `sqlalchemy[asyncio]` with `aiosqlite` as the driver. Better for larger schemas with relationships. Adds complexity — not required for a local tool.

**Recommended for TouriBot:** Option A (aiosqlite) for simplicity. The schema is small and reads are straightforward.

### REST API Endpoint Structure

```
GET  /leads                    — list all leads (query: stage, search, limit)
PUT  /leads/{id}/stage         — move lead to new pipeline stage
GET  /leads/{id}/conversations — list chat threads for a lead
GET  /conversations/{id}/messages  — load message history
POST /chat                     — send message, stream response via SSE
GET  /analytics/summary        — email stats, reply rates, pipeline counts
GET  /calendar/events          — follow-ups, demos, scheduled sends
GET  /tasks                    — pending tasks (follow-ups due, emails to review)
PUT  /tasks/{id}/complete       — mark task done
```

### CORS Configuration

Since Next.js (port 3000) calls FastAPI (port 8001) during local development:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_methods=['*'],
    allow_headers=['*'],
)
```

### Authentication

For a **local tool** used by a single developer on localhost: **no authentication needed** for the MVP. Add basic auth (HTTP Basic or a shared API key in `.env.local`) only if the dashboard will be exposed on a local network or Vercel.

If deploying to Vercel for remote access: use **NextAuth.js** (GitHub or Google OAuth) on the Next.js side, and validate a session token on the FastAPI side.

---

## Implementation Roadmap

### Phase 1: Scaffold (Day 1)
- `create-next-app` + shadcn/ui init
- Install: `@dnd-kit/core @dnd-kit/sortable @fullcalendar/react @fullcalendar/daygrid next-themes @tanstack/react-query ai @ai-sdk/react`
- FastAPI backend: `pip install fastapi uvicorn sse-starlette aiosqlite`
- Base layout: sidebar + tabbed navigation + theme toggle

### Phase 2: Core Views (Week 1)
- CRM Pipeline: kanban with @dnd-kit + table toggle via TanStack Table
- Analytics: shadcn/ui Chart components (bar + line + pie) pulling from FastAPI
- Calendar: FullCalendar with event types color-coded

### Phase 3: Chat & Tasks (Week 2)
- Chat interface: useChat hook + FastAPI SSE endpoint + thread sidebar
- Task board: shadcn/ui DataTable + status filters
- Settings: model selector, theme toggle, API key input

### Phase 4: Polish & Deploy (Week 3)
- Vercel deployment with environment variables
- FastAPI deployed to Render.com or Fly.io
- Add authentication (NextAuth.js) for Vercel access

---

## Package Version Reference

| Package | Version | Purpose |
|---|---|---|
| next | 15.x | App Router, RSC, routing |
| shadcn/ui | (CLI-managed) | Component system |
| @dnd-kit/core | 6.x | Drag-and-drop primitives |
| @dnd-kit/sortable | 8.x | Sortable kanban cards |
| @hello-pangea/dnd | 18.0.1 | Alternative to @dnd-kit |
| @tanstack/react-query | 5.x | Data fetching + caching |
| @tanstack/react-table | 8.x | Data table (via shadcn/ui) |
| recharts | 3.8.1 | Charts (via shadcn/ui Charts) |
| @fullcalendar/react | 6.x | Event calendar |
| ai | 6.x (Vercel AI SDK) | Chat streaming hooks |
| @ai-sdk/react | 6.x | useChat, useCompletion |
| next-themes | latest | Dark/light theme |
| fastapi | 0.135.3 | Python REST + WebSocket |
| sse-starlette | 3.3.4 | SSE streaming for FastAPI |
| aiosqlite | latest | Async SQLite for FastAPI |
| uvicorn | latest | FastAPI ASGI server |
