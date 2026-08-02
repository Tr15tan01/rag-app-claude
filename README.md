# Archive — Production RAG App

Ask questions about your own PDF documents and get answers grounded in,
and cited back to, the exact page they came from.

**Stack**
- Backend: FastAPI (Python), async SQLAlchemy, Aiven PostgreSQL + pgvector
- Auth: email/password (JWT) + Google OAuth
- LLM: Claude (Anthropic API) for generation, Voyage AI (or OpenAI) for embeddings
- Frontend: Next.js 14 (App Router), Tailwind, NextAuth
- Guardrails: file-type/size limits, prompt-injection screening, per-user row-level data isolation, rate limiting, security headers

---

## 1. Set up Aiven PostgreSQL

1. Create a PostgreSQL service at [aiven.io](https://aiven.io/) (any plan with pgvector support — Aiven enables the `vector` extension on all current PG plans).
2. From the service's **Overview** page, copy the connection details.
3. Build your `DATABASE_URL` in this form (Aiven requires SSL):
   ```
   postgresql+asyncpg://avnadmin:<PASSWORD>@<HOST>:<PORT>/defaultdb?ssl=require
   ```
4. You don't need to manually create tables or the `vector` extension — the backend does this automatically on startup (`init_db()` in `app/database.py`). For a real production deploy, switch to Alembic migrations instead of auto-create (see section 6).

## 2. Set up Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → **APIs & Services → Credentials**.
2. Create an **OAuth 2.0 Client ID** (type: Web application).
3. Add authorized redirect URIs:
   - Local: `http://localhost:3000/api/auth/callback/google`
   - Production: `https://your-domain.com/api/auth/callback/google`
4. You'll get a **Client ID** and **Client Secret**. The Client ID is used in *both* the backend and frontend `.env` files; the Client Secret is used only in the frontend.

## 3. Get your API keys

- **Anthropic API key** (generation): [console.anthropic.com](https://console.anthropic.com/)
- **Voyage AI API key** (embeddings, recommended — Anthropic's embedding partner): [dash.voyageai.com](https://dash.voyageai.com/). Alternatively set `EMBEDDING_PROVIDER=openai` and provide `OPENAI_API_KEY` instead — if you do, also change `EMBEDDING_DIM` to `1536`.

## 4. Configure environment files

```bash
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local
```

Fill in every value in both files — `DATABASE_URL`, `SECRET_KEY` (generate with `openssl rand -hex 32`), `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`, `ANTHROPIC_API_KEY`, `VOYAGE_API_KEY`, and `NEXTAUTH_SECRET` (also `openssl rand -hex 32`).

**Never commit `.env` or `.env.local` to git** — both are already covered by `.gitignore`.

## 5. Run locally

**Option A — Docker Compose (recommended):**
```bash
docker compose up --build
```
Backend on `http://localhost:8000` (docs at `/docs`), frontend on `http://localhost:3000`.

**Option B — run each service directly:**
```bash
# Backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000`, create an account (or sign in with Google), upload a PDF from the sidebar, and start asking questions once it shows "ready".

## 6. Deploy to a real server

This app is deploy-target agnostic — any host that runs Docker containers works (Render, Railway, Fly.io, a plain VPS with Docker, AWS ECS, etc.). General steps:

1. **Database**: your Aiven Postgres instance is already production-ready — no change needed, just use the same `DATABASE_URL` (or a separate prod database on the same Aiven service).
2. **Before your first prod deploy**, switch from `init_db()` auto-create to Alembic migrations:
   ```bash
   cd backend
   pip install alembic  # already in requirements.txt
   alembic init alembic
   # configure alembic/env.py to import Base from app.database and use DATABASE_URL
   alembic revision --autogenerate -m "initial schema"
   alembic upgrade head
   ```
   Then remove the `await init_db()` call from `app/main.py`'s lifespan and run migrations as a deploy step instead.
3. **Backend**: build and push the Docker image (`backend/Dockerfile`), deploy it, and set all `backend/.env` values as real environment variables on your host (not a checked-in file). Set `ENVIRONMENT=production`.
4. **Frontend**: deploy to Vercel (simplest for Next.js) or as a container using a similar `Dockerfile` pattern. Set `NEXTAUTH_URL` to your real domain and update the Google OAuth redirect URI accordingly.
5. **CORS**: update `ALLOWED_ORIGINS` in the backend `.env` to your real frontend domain (comma-separated if you have more than one, e.g. staging + prod).
6. **HTTPS**: put both services behind HTTPS (most hosts do this automatically; if self-hosting on a VPS, use nginx + Let's Encrypt or Caddy). The backend already sends `Strict-Transport-Security` when `ENVIRONMENT=production`.

## Project structure

```
rag-app/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app, middleware, security headers
│   │   ├── config.py        # env-based settings
│   │   ├── database.py      # async SQLAlchemy + pgvector setup
│   │   ├── models.py        # User, Document, Chunk
│   │   ├── schemas.py       # Pydantic request/response models
│   │   ├── security.py      # password hashing, JWT
│   │   ├── dependencies.py  # current-user auth dependency
│   │   ├── guardrails.py    # upload validation, prompt-injection screening
│   │   ├── routers/         # auth, documents, chat endpoints
│   │   └── services/        # PDF processing, embeddings, RAG engine
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── app/                 # Next.js App Router pages
│   ├── components/          # Navbar, ChatWindow, DocumentUpload, AuthProvider
│   ├── lib/                 # auth.ts (NextAuth config), api.ts (backend client)
│   ├── package.json
│   └── .env.local.example
└── docker-compose.yml
```

## Guardrails included

- **Upload validation**: PDF-only (extension + content-type), 20MB size cap, page-count cap, encrypted-PDF rejection.
- **Prompt-injection defense**: user queries are screened for known jailbreak phrasing; retrieved document content is wrapped in explicit `<source_N>` delimiters and the model is instructed to treat it as data, never instructions — this is the real defense, since a malicious PDF could otherwise embed hidden instructions.
- **Per-user data isolation**: every chunk/document query is filtered by `owner_id` at the database level — there's no code path where one user's documents are retrievable by another.
- **Rate limiting**: chat endpoint capped (default 20 requests/minute/IP, configurable).
- **Auth**: bcrypt password hashing, short-lived JWT access tokens + longer-lived refresh tokens, constant-shape login errors (doesn't reveal whether an email is registered).
- **Security headers**: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, HSTS in production, on both frontend and backend.
- **No leaked internals**: unhandled backend exceptions return a generic message, never a stack trace.

## Before going further with real users

This is a solid, working foundation — but treat it as a starting point, not a final security audit:
- Add centralized logging/monitoring (e.g. Sentry) for both services.
- Consider a dedicated content-moderation pass on generated answers if this will be public-facing.
- Add automated tests (the structure is test-friendly — routers depend on injectable `get_db`/`get_current_user`).
- Review Aiven's connection pooling limits if you expect high concurrency, and tune `pool_size`/`max_overflow` in `database.py` accordingly.
