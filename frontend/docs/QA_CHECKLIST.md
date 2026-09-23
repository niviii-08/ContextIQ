# ContextIQ Frontend — QA Checklist

Scope: `contextiq-frontend` standalone app running against mock data
(`NEXT_PUBLIC_USE_MOCK=true`) unless otherwise noted. Scenarios marked
**[Live]** apply once a real backend is connected.

## 1. Authentication **[Live]**

> No auth UI exists yet in this deliverable; these scenarios apply once an
> `authApi` + login screen are added following the same service pattern.

- [ ] Unauthenticated user hitting a protected route is redirected to login
- [ ] Valid credentials store a token and grant access
- [ ] Invalid credentials show a clear, non-technical error
- [ ] Expired/invalid token on any API call surfaces a 401 → app redirects to login rather than showing a raw error screen
- [ ] Logout clears the token and returns to a logged-out state
- [ ] Token is never logged to the console or exposed in the DOM

## 2. Tasks

- [ ] Task list loads and displays all mock tasks on `/tasks`
- [ ] Status filter tabs (All/Pending/In progress/Paused/Completed/Forgotten) correctly filter the list
- [ ] Creating a task with all required fields (title, category, context) succeeds and the new task appears at the top of the list
- [ ] Creating a task with a missing required field shows an inline validation error and does **not** call the API
- [ ] Priority selector defaults to Medium and can be changed
- [ ] Estimated minutes accepts only numeric input
- [ ] Clicking a task title opens the Task Detail dialog with correct metadata (context, category, priority, forgotten count, completion streak)
- [ ] Task Detail dialog is closeable via the close button, Escape key, and overlay click
- [ ] **Start** is only available for `PENDING` tasks and transitions status to `IN_PROGRESS`
- [ ] **Pause** is only available for `IN_PROGRESS` tasks and transitions to `PAUSED`
- [ ] **Resume** is only available for `PAUSED` tasks and transitions back to `IN_PROGRESS`
- [ ] **Complete** is only available for `IN_PROGRESS` tasks and transitions to `COMPLETED`
- [ ] **Mark forgotten** is available for Pending/In progress/Paused tasks, transitions to `FORGOTTEN`, and increments `forgottenCount`
- [ ] Completing a task increments `completionStreak`; marking forgotten resets it to 0
- [ ] No status action buttons render for `COMPLETED` or `FORGOTTEN` tasks

## 3. Task Events

- [ ] Every status-changing action (start/pause/resume/complete/forgotten) produces a corresponding `TaskEvent` with the correct `type`
- [ ] Task Detail dialog's "Event history" list shows events for that task, most recent first
- [ ] A task with no events shows the empty message, not a blank list
- [ ] Event timestamps render in the user's local time in a readable format

## 4. Analytics (Dashboard)

- [ ] `/` (Dashboard) shows the Friction Score gauge, and it renders 0–100 with correct color coding (green <40, amber 40–69, red ≥70)
- [ ] All six overview metrics render: Friction Score, Tasks completed, Tasks forgotten, Context switches, Interruption time, Recovery cost
- [ ] Delta indicators (vs. yesterday) show correct direction (up/down arrow) and correct good/bad color per metric
- [ ] Minutes are formatted as `Xh Ym` / `Xm` consistently

## 5. ML Predictions (Forget Risk)

- [ ] `/predictions` and the dashboard's Forget Risk section both render prediction cards
- [ ] Risk badge (LOW/MEDIUM/HIGH) color matches `riskScore` bucket (≥70 High, 40–69 Medium, <40 Low)
- [ ] Progress bar fill width matches `riskScore`
- [ ] All listed `reasons` render with label + detail text
- [ ] Filter tabs (All/High/Medium/Low) correctly filter predictions client-side via the API's `riskLevel` param
- [ ] Filtering to a risk level with zero matches shows the empty state, not a blank grid

## 6. Recommendations ("One More Thing")

- [ ] `/recommendations` and the dashboard both show pending recommendations
- [ ] Card shows context name, reliable tasks (chips), and suggested tasks with reasons
- [ ] Clicking **Add** calls `recommendationApi.accept`, shows a confirmation message, and removes the card from the pending list on refetch
- [ ] Clicking **Dismiss** calls `recommendationApi.dismiss`, shows a confirmation message, and removes the card from the pending list on refetch
- [ ] Buttons show a pending/disabled state while the request is in flight
- [ ] Confirmation message is announced to screen readers (`aria-live="polite"`)
- [ ] Accepting/dismissing all recommendations shows the empty state

## 7. Behaviour Insights

- [ ] `/insights` shows one card per insight type present in the data (friction source, frequently forgotten, high-interruption context, strongest association)
- [ ] Each card shows a priority badge (LOW/MEDIUM/HIGH) and, where present, a metric label + value
- [ ] Insight icon matches insight type (flame/repeat/radar/link)

## 8. Context Intelligence

- [ ] `/context` shows four summary metric cards: focus time, interruption time, context switches, recovery cost
- [ ] Focus-vs-interruption bar chart renders one bar pair per hour bucket with a legend
- [ ] Interruption category donut chart renders one segment per category with a legend
- [ ] "Most affected task category" card shows the correct value
- [ ] Charts have an accessible label (`role="img"` + `aria-label`) for screen reader users
- [ ] Charts render correctly at both desktop and mobile widths (no overflow/clipping)

## 9. Feedback

- [ ] `feedbackApi.submit` accepts `targetType` of `PREDICTION`, `RECOMMENDATION`, `INSIGHT`, or `GENERAL`
- [ ] Submitting feedback without a comment succeeds (comment is optional)
- [ ] **[Live]** Submitted feedback is retrievable/auditable on the backend for model evaluation

## 10. Responsive UI

- [ ] At ≥1024px (`lg`), the left sidebar is visible and the bottom nav is hidden
- [ ] Below 1024px, the bottom nav is visible and the sidebar is hidden
- [ ] All metric grids reflow from 3–4 columns (desktop) to 1–2 columns (mobile) without horizontal scrolling
- [ ] Task list, prediction cards, recommendation cards, and insight cards all remain readable and tappable at 375px width
- [ ] Dialogs (Task Detail) remain within the viewport and are scrollable if content overflows on small screens
- [ ] Bottom nav does not overlap page content (verify trailing padding on scrollable pages)
- [ ] All interactive elements have a visible focus ring and are reachable via Tab in a logical order
- [ ] Color contrast of text against backgrounds meets WCAG AA in both light and dark tokens

## 11. API Failures

- [ ] Every data-driven section (Overview, Forget Risk, Context Intelligence, Recommendations, Insights, Task list) shows a loading skeleton before data arrives
- [ ] Every data-driven section shows a distinct error state (with `role="alert"`) when the service returns an error, instead of a blank screen
- [ ] Error states include a **Try again** button that re-triggers the fetch
- [ ] A slow/timed-out request (>10s) surfaces a "Request timed out" message rather than hanging indefinitely
- [ ] A malformed/non-JSON error response from the backend does not crash the app — it falls back to the generic error message
- [ ] Network failures (offline) surface a "Network error" message
- [ ] Retrying after a transient failure successfully loads data once the underlying call succeeds

## 12. Cross-cutting

- [ ] No secrets or API keys are present in the client bundle (`.env.example` documents required vars; no hardcoded tokens in source)
- [ ] `npm run build` completes with no TypeScript errors
- [ ] `npm run lint` completes with no errors
- [ ] `npm run test` passes all suites
- [ ] Switching `NEXT_PUBLIC_USE_MOCK` to `false` with no backend running produces clean error states everywhere (not crashes) — validates the error-handling path end to end
