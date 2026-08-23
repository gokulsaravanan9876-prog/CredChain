# CredChain

### Student-Owned Academic Credential Passport

## 🚀 Live Demo

# CredChain — Frontend

Student-owned academic credential passport. Three portals (Student / Institution / Verifier) in one codebase, built against the Figma screens with mocked data — no backend required to run.

## Run it

```bash
npm install
npm run dev
```

Open the URL Vite prints (usually `http://localhost:5173`). A **"Demo" role switcher** floats bottom-right — use it to jump between all three portals without real auth.

```bash
npm run build     # production build to dist/
npx tsc -b        # type-check only
npx oxlint        # lint
```

I could not run a browser in the sandbox this was built in (network egress is locked down, so Playwright/Chromium couldn't download) — this has been verified via a clean TypeScript build, a clean production Vite build, and a lint pass, but **you should do the first visual pass yourself** before treating any screen as final. See the QA checklist at the bottom.

## Project structure

```
src/
  types.ts               — shared data model (single source of truth)
  lib/
    mockStore.ts          — in-memory mock data (Rahul Kumar, XYZ University, ABC Technologies)
    api.ts                — mock API layer; swap function BODIES for real fetch() calls later,
                             signatures/return shapes are already what a real backend needs
    utils.ts               — icon lookups, status color/tone helpers
  components/
    ui/                    — Badge, Button, Card, StatCard, IconTile, CheckRow, EmptyState,
                             FilterPills, SearchInput, PageHeader (shared everywhere)
    layout/                — Sidebar, TopBar, AppShell, RoleSwitcher (dev-only), nav.config.ts
    Stub.tsx                — placeholder for unspecified screens (Settings, etc.)
  portals/
    student/                — Dashboard, Credentials, CredentialDetail, Applications (AI),
                             Companies, CompanyDetail, Requests, ShareFlow, ShareConfirmation, Activity
    institution/             — Dashboard, Students, Credentials, IssueCredential,
                             CredentialIssued, Requests, Activity
    verifier/                — Dashboard, Candidates, VerificationResult (+ live tamper-test
                             demo controls), RequestCredentials, Verified, Activity
  App.tsx                   — all routing
```

## Backend handoff (tomorrow)

Everything in `src/lib/api.ts` returns a `Promise` and already has the shape a real endpoint needs. To wire up the real backend:

1. Replace the body of each function in `api.ts` with a `fetch()` call to the real endpoint.
2. Leave the function signature and return type alone — every component imports from `api.ts`, not from `mockStore.ts` directly, so nothing else needs to change.
3. Real auth replaces the `RoleSwitcher` — once that exists, delete `<RoleSwitcher />` from `App.tsx` and derive the logged-in `User` from your auth state instead of the hardcoded `rahul` / `iyer` / `anjali` constants.

## The live-demo centerpiece

`/verifier/verify/cand-1` (Rahul Kumar's row → Review) is wired for a real live tamper-test:

1. Shows VERIFIED for Rahul's shared credentials.
2. A "Demo controls" panel lets you edit the transcript's CGPA and click **Re-run Verification**.
3. Changing it away from `8.7` flips the result to INVALID in real time, with the original-vs-presented CGPA diff shown.
4. **Reset to original** puts it back to `8.7` / VERIFIED.

This only works for Rahul (`cand-1`) since he's the only candidate with real backing credential records in the mock data — the other three candidates on the dashboard render a simplified static result based on their preset status.

## Known gaps / things I inferred rather than copied

These were either broken in the source Figma export or simply not designed — flagging so you can correct my judgment calls before the backend locks in around this shape:

- **AI Application Assistant, incoming Credential Request, and Credential Shared confirmation** — these three screens rendered a giant checkmark icon instead of real content in the Figma export. Rebuilt using the correct check-row pattern from your working screens (transcript detail, sharing flow).
- **Institution portal** — only the "Credential Issued" confirmation screen existed in Figma. Dashboard, Students, Credentials list, Issue form, Requests, and Activity are all built from scratch, matching the other two portals' visual system but with no design reference to check against.
- **Institution "Requests"** — left as an honest empty state. There's no designed flow for students requesting issuance/corrections from their institution; I didn't want to invent a whole approval workflow that isn't specified anywhere.
- **Credential status vocabulary** — reconciled to `verified | pending | revoked` (credential's own state) and `VERIFIED | INVALID | REVOKED` (a verifier's point-in-time check result), per your confirmation. "Needs Attention" on the verifier dashboard maps to the same underlying state as "Invalid," just a softer list label.
- **No real documents/PDFs** — the document preview panel is a styled placeholder, not a real file viewer.
- **QR code is real** (a scannable QR pointing at a fake share URL) rather than a static gray box, since it costs nothing and demos better.

## QA checklist — please verify against your Figma file

- [ ] Colors: I eyeballed the indigo/purple/green/amber/red palette from screenshots. If you have exact hex values from Figma's Inspect panel, send them and I'll swap the tokens in `src/index.css` (`@theme` block) — it's a five-minute change, isolated to one file.
- [ ] Spacing/density: my judgment on padding and card sizing, not pixel-measured from Figma.
- [ ] Sidebar nav icons — I chose icons per nav label (Dashboard, Credentials, Applications, etc.); confirm they match what's actually in Figma's icon set if that matters to you.
- [ ] Company Intelligence / AI Insight copy — the source-attribution pattern ("Source: ... · Updated 2026") is carried through from your screens; confirm the placeholder source text is what you want before a real data source is wired in.
