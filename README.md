# GradePilot

GradePilot is a transcript analysis and GPA planning tool. Upload a university transcript PDF, review extracted courses and GANO (cumulative GPA), then run planning scenarios in one place.

The product is a local two-process app: a **Next.js** UI and a **FastAPI** backend. Transcript text is parsed in Python. **Academic arithmetic (GPA, plans, projections) lives in deterministic Python engines.** The browser displays results; it does not compute GPA.

Typical flow: PDF upload → parse and optional credit/ECTS weighting → current GPA and semester view → course impact, target plans, manual grade scenarios, and a future-semester projection.

---

## Why GradePilot?

A transcript already lists courses, credits, and letter grades. What students still do by hand is the math around that list:

- current cumulative GPA
- how much one course improvement would move the average
- which grade changes reach a target GPA
- what GPA a future semester would need

GradePilot keeps those calculations in one tool, with a single Python implementation as the source of truth.

---

## Features

What the current codebase actually does:

- **PDF transcript upload** (drag-and-drop or file picker), after acknowledging privacy and terms
- **Known + generic parsing** — Çankaya University transcripts have a dedicated parser; other layouts go through a generic extractor and may ask you to confirm courses
- **Credit / ECTS weighting** — when the parser cannot assume a GPA weight field, you choose which numeric field to use
- **Current cumulative GPA (GANO)** from the 4.00 letter scale used in `core/grade_scale.py` (`AA`–`FF`)
- **Semester GPA** rows from the same engines
- **Grade distribution** on the dashboard (counts of letter grades already returned by the API)
- **Course impact** — projected GPA if one course’s grade changes
- **Automatic target GPA planner** — suggested grade changes toward a target, with strategy and max-grade constraints
- **Manual grade scenario planner** — apply your own letter-grade edits
- **Future semester simulation** — add planned courses and estimated grades
- **Required semester GPA** — minimum term GPA to hit a target cumulative GPA given a future credit load
- **Repeated courses** — cumulative GPA uses the latest attempt (by source order); historical attempts stay in the full course list
- **Dark / light theme** (saved in `localStorage`, respects system preference on first visit)
- **Responsive UI** (desktop nav + mobile drawer)
- **Turkish-first interface** (`lang="tr"`, Turkish copy and legal pages)
- **Privacy and terms pages** (`/gizlilik`, `/kullanim-kosullari`)
- **Upload and API controls** — size/page limits, PDF magic-byte check, rate limits, CORS, security headers

There is **no** user authentication, **no** application database, **no** cloud object storage, and **no** AI/LLM in the transcript path. Parsed courses and results live in the browser session until you reset or refresh.

An optional **CLI** (`app.py` at the repo root) exposes the same Python engines in a terminal menu. The web app is the primary interface.

---

## How It Works

1. The student uploads a transcript PDF in the Next.js app.
2. The API streams the file to a server-generated temp path and validates it as a PDF.
3. `pdfplumber` extracts text; the detector chooses the Çankaya parser or the generic path.
4. If GPA weighting is ambiguous, the UI asks which credit field to use and re-analyzes.
5. Courses are normalized into domain models (code, name, grades, credits, semester, source order).
6. Later screens send those courses to FastAPI academic endpoints; Python engines compute GPA and plans.
7. FastAPI returns structured JSON (Pydantic response models).
8. Next.js renders dashboards and planners from that JSON.

**Principle:** GPA and related academic outcomes are computed in Python (`core/` via `services/`). The frontend must not reimplement those formulas.

---

## Architecture

```
Browser
   |
Next.js (web/)
   |
FastAPI (api/)
   |
Services (services/)
   |
Core engines (core/)  +  Transcript parser (parsers/)
```

| Path | Role |
| --- | --- |
| `api/` | HTTP layer: upload, academic routes, CORS, rate limit, cache and security headers |
| `core/` | Deterministic GPA, semester, impact, scenario, target, future-term, and required-GPA engines |
| `parsers/` | Format detection, Çankaya parser, generic parser, weighting options |
| `models/` | Course and parse-result domain types |
| `services/` | Application layer: transcript processing and academic use cases |
| `input/` | PDF validation and safe temp-file handling |
| `tests/` | pytest suite for engines, parsers, and API behavior |
| `web/` | Next.js App Router UI |

`app.py` is a thin CLI over `services/` and `core/`, not a second calculation stack.

---

## Tech Stack

Versions below match the repo files, not guesses.

**Backend** (`requirements.txt`, API `0.1.0` in `api/main.py`)

- Python
- FastAPI `>=0.115.0`
- Uvicorn `[standard]` `>=0.32.0`
- Pydantic (request/response models in `api/schemas.py`; pulled in with FastAPI)
- python-multipart `>=0.0.12` (file uploads)
- pdfplumber `>=0.11.0`
- httpx `>=0.27.0` (API tests)
- pytest `>=8.0.0`

**Frontend** (`web/package.json`)

- Next.js `16.3.4`
- React `19.2.8` / react-dom `19.2.8`
- TypeScript `^5`
- Tailwind CSS `^4` (`@tailwindcss/postcss`)
- `next/font` — Plus Jakarta Sans and Sora

**Tooling**

- ESLint `^9` with `eslint-config-next` `16.3.4`
- Git

---

## Security & Privacy

These are **current implementation choices**, not a security guarantee.

- Uploaded PDFs are written to process-owned temp files (`gradepilot_upload_`, then a validated copy `gradepilot_pdf_`). Both paths are deleted when processing finishes or fails.
- GradePilot does not persist transcripts in a database or object store. After analyze, the UI keeps course JSON in client state for the session.
- Responses under `/api/` set `Cache-Control: no-store`.
- Upload limits: **10 MB**, **50 pages**, PDF signature `%PDF-` (magic bytes). Fake extensions and non-PDF bytes are rejected.
- In-memory rate limiting (per API process): default **5** analyze requests and **30** calculation requests per client per **60s** window (`Retry-After` on `429`). Limits are configurable via environment variables.
- CORS is an explicit origin list (default `http://localhost:3000` and `http://127.0.0.1:3000`). `*` is ignored.
- API security headers: `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options: DENY`, `Permissions-Policy`. HSTS is **off** unless `GRADEPILOT_ENABLE_HSTS=1` (HTTPS-only deployments).
- The Next.js app also sends CSP and related headers (`web/next.config.ts`).
- No third-party analytics in the current UI. Transcripts are not sent to an external AI/LLM service.
- Configuration that should not be committed (CORS, rate limits, API origin) is meant to live in environment files. There are no application secrets in the default stack.

Rate limits are **process-local**. Multiple Uvicorn workers do not share one limiter.

---

## Project Structure

```
GradePilot/
├── api/                 # FastAPI app and HTTP adapters
├── core/                # GPA and planning engines
├── input/               # PDF validation
├── models/              # Domain models
├── parsers/             # Transcript formats
├── services/            # Use cases
├── tests/               # Backend tests
├── web/                 # Next.js frontend
├── app.py               # Optional CLI
├── requirements.txt
└── README.md
```

---

## Running Locally

Two processes: API on **127.0.0.1:8000**, UI on **localhost:3000**. Do not point the app at port 8001 for normal development.

### Backend (PowerShell, repo root)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

Useful environment variables (see `.env.example`):

| Variable | Purpose |
| --- | --- |
| `GRADEPILOT_CORS_ORIGINS` | Comma-separated frontend origins |
| `GRADEPILOT_RATE_LIMIT_ANALYZE` / `GRADEPILOT_RATE_LIMIT_CALCULATION` | Per-window limits |
| `GRADEPILOT_TRUST_PROXY` | Only `1` behind a proxy you control that sets `X-Forwarded-For` |
| `GRADEPILOT_ENABLE_API_DOCS` | `/docs` (default on locally; turn off in production) |
| `GRADEPILOT_ENABLE_HSTS` | Leave `0` on local HTTP |

Health check: `GET http://127.0.0.1:8000/health`

### Frontend (PowerShell)

```powershell
cd web
npm install
Copy-Item .env.example .env.local
npm run dev
```

Default API origin is `http://127.0.0.1:8000`. Override with `NEXT_PUBLIC_API_BASE_URL` in `web/.env.local` only if needed.

Open [http://localhost:3000](http://localhost:3000). The home route redirects to `/transkript` or `/genel-bakis` depending on whether a transcript is loaded.

### Tests and frontend checks

From the repo root (venv active):

```powershell
python -m pytest
```

From `web/`:

```powershell
npx tsc --noEmit
npx eslint --max-warnings=0
npm run build
```

---

## Current Scope and Possible Next Work

**In scope today:** local PDF analysis, session-only UI state, Çankaya + generic parsing, and Python-backed planning on a fixed letter scale.

**Not in the product today:** accounts, saved transcripts, multi-tenant hosting, extra university format packs as first-class parsers, or LLM-assisted parsing.

Reasonable follow-ups if the project continues:

- Additional **known** transcript formats (keep generic parsing as fallback)
- Clearer confirmation UX for generic extracts
- Persistence only if you add a real store and a privacy model — not a small toggle
- Auth only if persistence or multi-user hosting is actually needed
- Shared rate limiting if you run more than one API worker
- Production deployment notes (HTTPS, `GRADEPILOT_CORS_ORIGINS`, docs off, HSTS at the proxy)

---

## License

No license file is included in this repository. Treat the code as source-available unless you add an explicit license.
