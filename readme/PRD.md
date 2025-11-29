# Chineye AI — Product Requirements Document (PRD)

## 1. Overview
- Chineye AI is a privacy‑minded AI chat application with user accounts, secure login (JWT), chat messaging, and saved history. It ships as a simple monorepo: static frontend + Python FastAPI backend exposed via a serverless entrypoint on Vercel.

## 2. Objectives
- Deliver a clear, usable chat experience that works well on mobile and desktop.
- Keep the stack simple (HTML/CSS/JS + FastAPI + Supabase) for fast iteration.
- Ensure deployability on a free‑friendly platform (Vercel + Supabase free tier).

## 3. Personas
- "Curious Learner": wants quick answers and a clean UI, no setup hassles.
- "Busy Professional": needs reliable login, good mobile experience, saved chats.
- "Builder/Presenter": needs a straightforward demo app for slides and teaching.

## 4. Key User Stories
- As a user, I can sign up with email, username, and password.
- As a user, I can log in and receive a token to access chat features.
- As a user, I can send a message and receive an AI response.
- As a user, I can view my previous messages and responses in history.
- As a user, I can log out to invalidate my session client‑side.
- As a visitor, I can subscribe to a newsletter.

## 5. Scope
In‑scope:
- Responsive landing and chat pages (mobile and desktop).
- Signup/login/logout, protected chat routes.
- Store and retrieve chat history per user.
- Newsletter form.

Out‑of‑scope (initial release):
- Role management, admin dashboards.
- Payments and billing.
- Fine‑grained model selection and prompt engineering UI.
- Analytics/telemetry beyond minimal logging.

## 6. Functional Requirements
### 6.1 Authentication
- POST `/api/signup`: accepts username, email, password; hashes and stores credentials.
- POST `/api/login`: verifies credentials; returns JWT token and username.
- POST `/api/logout`: client‑side token removal; server returns confirmation.

### 6.2 Chat
- POST `/api/send-message`: accepts prompt; requires `Authorization: Bearer <token>`.
- Stores user message and assistant response to `chat_history`.
- Returns `MessageResponse` with assistant message.

### 6.3 History
- GET `/api/history`: requires auth; returns list of `ChatHistoryEntry`.

### 6.4 Newsletter
- POST `/api/newsletter`: accepts `{ email }`; stores or forwards to mailing list service.

### 6.5 Health & Root
- GET `/`: root info for sanity checks.
- GET `/health`: returns `{ status: 'ok' }` for monitoring.

## 7. Non‑Functional Requirements
- Performance: basic responsiveness; page loads under 2 seconds on typical devices.
- Security: passwords hashed, tokens verified; HTTPS enforced on Vercel.
- Reliability: endpoints return clear error messages and stable JSON formats.
- Maintainability: small, readable codebase with minimal dependencies.

## 8. UX & UI Requirements
- Landing page: hero text, CTA buttons, feature cards, newsletter section.
- Chat page: header with app title and user controls; sidebar with history; messages area; sticky footer with input.
- Mobile: single vertical scroll, dropdown user menu (greeting + logout), reduced font sizes, input visible above keyboard.
- Dark mode: optional; maintain legibility and consistent palettes.

## 9. Acceptance Criteria (Examples)
- Signup with valid inputs returns 200 and user info; invalid inputs return 400 with details.
- Login returns 200 with `access_token` and `username` for valid credentials; 401 otherwise.
- `send-message` with a valid token stores a user/assistant pair and returns a message string.
- History returns a list of entries for the authenticated user.
- Newsletter returns 200 with a message confirmation.
- On mobile, no horizontal scroll; only one vertical scrollbar; input remains visible when keyboard opens.

## 10. Data Model (Simplified)
- `users`: `id(UUID)`, `email(uniq)`, `username(uniq)`, `password_hash`, `created_at`.
- `chat_history`: `id(serial)`, `user_id(UUID)`, `message(text)`, `response(text)`, `timestamp`.

## 11. API Contracts (Brief)
- `POST /api/signup`
  - Request: `{ username, email, password }`
  - Response: `{ message, email, username }`
- `POST /api/login`
  - Request: `{ email, password }`
  - Response: `{ access_token, token_type, username }`
- `POST /api/send-message` (auth)
  - Request: `{ message }`
  - Response: `{ message: <assistant_response> }`
- `GET /api/history` (auth)
  - Response: `{ history: [ { message, response, timestamp } ] }`
- `POST /api/logout` (auth)
  - Response: `{ message }`
- `POST /api/newsletter`
  - Request: `{ email }`
  - Response: `{ message }`

## 12. Tools Used
- **Frontend:**
  - HTML5/CSS3 (`theme.css` for styles), Vanilla JavaScript (`app.js`)
  - Font Awesome for icons
- **Backend:**
  - Python 3.8+, FastAPI, Uvicorn
  - Pydantic models, JWT utilities (`auth.py`)
  - Supabase client (`database.py`) for PostgreSQL persistence
- **Infrastructure/Deployment:**
  - Vercel: `api/index.py` exposes FastAPI app (ASGI)
  - `api/requirements.txt` includes `backend/requirements.txt`
  - `vercel.json` routes `/api/*` to Python function, serves `frontend/*` as static
- **Utilities:**
  - `dotenv` for environment variables
  - `readme/START_SERVERS.txt` with quick dev commands

## 13. Environment Variables
- See `backend/.env.example` and copy to `backend/.env`.
- Typical values: `SUPABASE_URL`, `SUPABASE_KEY`, `SECRET_KEY`, `PORT`.

## 14. Risks & Mitigations
- CORS: use same‑origin routing on Vercel (`/api`) to minimize issues.
- Token storage: tokens in `localStorage`; advise secure contexts and logout control.
- DB connectivity: ensure Supabase keys are correct; use `/test-db` to verify.

## 15. Success Metrics
- Signups per day; chat messages per session; return visits.
- Mobile engagement rate and time‑to‑first‑message.
- Error rates (auth failures, 500s) below acceptable thresholds.

## 16. Rollout Plan
- Phase 1: MVP feature parity (auth, chat, history, newsletter).
- Phase 2: UX refinements (formatting, shortcuts, improved history browsing).
- Phase 3: Integrations (export, sharing, optional analytics).

## 17. Appendix: Dev & Ops
- Local dev: `uvicorn` backend on `:8000`, Python static server on `:3000`.
- Health check: `/api/health` on production; `/health` for basic status.
- Monitoring: start with basic logs; optionally add structured logging.