# ContextIQ — Frontend

ContextIQ is a **Personal Behaviour Intelligence System**. It's not a todo
app — it helps a person understand:

1. What they're likely to forget
2. Where they lose attention
3. How context switching affects them
4. What tasks they repeatedly forget in specific contexts
5. Their hidden daily friction

This package is a **complete, standalone frontend** for ContextIQ. It runs
fully on mock data with zero backend dependency, and is built so that
connecting a real backend/ML system later is a configuration change, not a
rewrite. See [`docs/INTEGRATION_BLUEPRINT.md`](docs/INTEGRATION_BLUEPRINT.md)
for the exact contract the backend must satisfy.

## Tech stack

- **Next.js 16** (App Router) + **TypeScript** (strict mode)
- **Tailwind CSS v4** with a custom design-token system (light/dark)
- Hand-built **shadcn/ui-style** components on top of Radix primitives + CVA
- **Recharts** for data visualization
- **Vitest** + **Testing Library** for tests

## Quick start

```bash
npm install
cp .env.example .env.local   # defaults already work — mock mode is on
npm run dev                  # http://localhost:3000
```

The app is fully demoable immediately: Dashboard → Tasks → Context
Intelligence → Predictions → Recommendations → Behaviour Insights, all
backed by realistic mock data, no backend required.

## Commands

| Command | Purpose |
|---|---|
| `npm run dev` | Start the dev server |
| `npm run build` | Production build (also runs the TypeScript checker) |
| `npm start` | Serve the production build |
| `npm run lint` | ESLint |
| `npx tsc --noEmit` | Standalone TypeScript check |
| `npm run test` | Run the full Vitest suite once |
| `npm run test:watch` | Run Vitest in watch mode |

## Project structure

```
contextiq-frontend/
├── app/                        # Next.js App Router routes
│   ├── layout.tsx              # Root layout + AppShell
│   ├── page.tsx                # Dashboard ("/")
│   ├── globals.css             # Design tokens (light/dark CSS variables)
│   ├── not-found.tsx
│   ├── tasks/page.tsx
│   ├── context/page.tsx
│   ├── predictions/page.tsx
│   ├── recommendations/page.tsx
│   └── insights/page.tsx
├── components/
│   ├── ui/                     # shadcn-style primitives (button, card, dialog, ...)
│   ├── layout/                 # AppShell, Sidebar, MobileNav, Topbar
│   ├── shared/                 # RiskBadge, ErrorState, EmptyState
│   ├── dashboard/               # Friction gauge, metric cards, overview section
│   ├── tasks/                  # Task list, create form, actions, detail dialog
│   ├── analytics/              # Context Intelligence charts + view
│   ├── predictions/            # Forget Risk cards + panel
│   ├── recommendations/        # "One More Thing" cards + panel
│   └── insights/               # Behaviour insight cards + panel
├── lib/
│   ├── api/
│   │   ├── client.ts            # fetch wrapper, error normalization, mock switch
│   │   ├── index.ts              # barrel export of all *Api services
│   │   └── services/             # tasksApi, analyticsApi, predictionApi,
│   │                              # contextApi, recommendationApi, insightsApi,
│   │                              # feedbackApi — each: interface + mock + live impl
│   ├── nav.ts                    # nav item config shared by sidebar/mobile nav
│   └── utils.ts                  # cn(), formatMinutes(), formatDelta(), ...
├── hooks/
│   └── use-api-data.ts           # loading/error/success wrapper around *Api calls
├── types/
│   └── index.ts                  # ALL integration contracts (Task, Prediction, ...)
├── mock/
│   ├── tasks.mock.ts
│   └── analytics.mock.ts         # summary, context metrics, predictions,
│                                   # recommendations, insights, associations
├── tests/                        # Vitest + Testing Library specs
├── docs/
│   ├── QA_CHECKLIST.md
│   └── INTEGRATION_BLUEPRINT.md
├── public/
├── .env.example
└── package.json
```

## API integration contract (summary)

Every component talks only to a typed service object — never to `fetch`
directly:

```ts
import { tasksApi, analyticsApi, predictionApi, contextApi,
         recommendationApi, insightsApi, feedbackApi } from "@/lib/api";
```

Each service has one TypeScript interface with two implementations (mock and
live), chosen automatically based on `NEXT_PUBLIC_USE_MOCK`:

```ts
export interface TasksApi {
  list(filters?: { status?: TaskStatus; context?: string }): Promise<ApiResult<Task[]>>;
  getById(id: string): Promise<ApiResult<Task>>;
  create(input: CreateTaskInput): Promise<ApiResult<Task>>;
  updateStatus(id: string, status: TaskStatus): Promise<ApiResult<Task>>;
  recordEvent(id: string, type: TaskEventType): Promise<ApiResult<TaskEvent>>;
  listEvents(taskId: string): Promise<ApiResult<TaskEvent[]>>;
}
```

All results resolve to `ApiResult<T> = { data: T | null; error: ApiError | null }`,
so every consuming component handles loading/error/empty/success uniformly
via the `useApiData` hook. Full endpoint-by-endpoint request/response/error
schemas are in [`docs/INTEGRATION_BLUEPRINT.md`](docs/INTEGRATION_BLUEPRINT.md).

## Mock data structure

Mock data lives entirely under `/mock` and is isolated from the service
logic in `lib/api/services/*`:

- `mock/tasks.mock.ts` — `mockTasks: Task[]`, `mockTaskEvents: TaskEvent[]`
- `mock/analytics.mock.ts` — `mockDailySummary`, `mockContextMetrics`,
  `mockAssociations`, `mockPredictions`, `mockRecommendations`, `mockInsights`

Mutating mock endpoints (`tasksApi.create`, `updateStatus`, `recordEvent`,
`recommendationApi.accept/dismiss`) keep an in-memory copy of the seed data
per service module so the UI behaves statefully within a session, without
needing a real database.

## Design system

A cool-neutral "instrumentation" palette (not a generic AI-chatbot look):
single signal-blue accent for primary actions/focus, a dedicated 3-step risk
scale (`risk-low` / `risk-medium` / `risk-high`) reused everywhere risk,
priority, or friction is communicated, and monospace numerals so metrics
read like instrument readings. All tokens are CSS variables in
`app/globals.css` with a `.dark` variant already defined.

## QA

See [`docs/QA_CHECKLIST.md`](docs/QA_CHECKLIST.md) for the full manual test
scenario checklist (tasks, events, analytics, ML predictions, recommendations,
insights, feedback, responsive UI, API failure handling).

Automated coverage (`npm run test`) includes: dashboard rendering
(success + error), task creation (success + validation), prediction
rendering (success + empty), recommendation add/dismiss interactions, the
API client's mock/error-normalization behavior, and the shared
empty/error-state components.

## Connecting a real backend

1. Implement the endpoints described in `docs/INTEGRATION_BLUEPRINT.md`.
2. Set `NEXT_PUBLIC_API_BASE_URL` and `NEXT_PUBLIC_USE_MOCK=false` in
   `.env.local`.
3. Run `npm run build && npm run test` — no component changes are required.
