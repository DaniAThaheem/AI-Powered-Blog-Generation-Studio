# AI-Powered Technical Blog Generation Studio

A full-stack web application that transforms a LangGraph multi-agent workflow into a production-ready blog generation platform. Users enter a topic and optionally configure audience, tone, research preferences, and reference documents. The system routes through a multi-agent pipeline—researching, planning, writing sections in parallel, generating images, and returning a polished Markdown blog.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        React Frontend                           │
│   Vite · TypeScript · Tailwind CSS · React Router · TanStack    │
│                  http://localhost:5173                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST + SSE
┌──────────────────────────▼──────────────────────────────────────-┐
│                       FastAPI Backend                            │
│                  http://localhost:8000                           │
│                                                                  │
│  ┌─────────────┐  ┌────────────────┐  ┌──────────────────────┐   │
│  │  REST API   │  │   SSE Stream   │  │  Background Executor │   │
│  │  /api/...   │  │ /api/generations│  │  GenerationRunner   │   │
│  │             │  │  /{id}/stream  │  │                      │   │
│  └─────────────┘  └────────────────┘  └──────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                  LangGraph Workflow                      │    │
│  │                                                          │    │
│  │  Router → [Research] → Orchestrator → [Workers×N] →      │    │
│  │  Merge → ImagePlanner → ImageGen → Final                 │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Services: Gemini · Tavily · Cloudinary · Pinecone               │
│  Database: SQLite (default) / PostgreSQL                         │
└─────────────────────────────────────────────────────────────────-┘
```

### LangGraph Workflow Nodes

| Node | Purpose |
|------|---------|
| **Router** | Determines research mode (`closed_book` / `hybrid` / `open_book`) via Gemini structured output |
| **Research** | Tavily web search → evidence deduplication → structured `EvidenceItem` list |
| **Orchestrator** | Gemini structured output produces a `Plan` with 5–7 ordered `Task` objects |
| **Worker × N** | Each section generated in parallel via LangGraph `Send` fan-out |
| **Merge** | Sorts workers by `task.id`, deduplicates, assembles final Markdown |
| **ImagePlanner** | Gemini decides whether ≤3 diagrams are needed; returns placeholder positions + prompts |
| **ImageGen** | Generates images, uploads to Cloudinary (or local storage), replaces placeholders |

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite 5, Tailwind CSS, React Router 6, TanStack Query |
| Backend | Python 3.13, FastAPI, uvicorn, LangGraph, LangChain |
| AI / LLM | Google Gemini (text + image), Tavily (web search) |
| Vector DB | Pinecone (with in-memory cosine-similarity fallback) |
| Object Storage | Cloudinary (with local `./storage/` fallback) |
| App Database | SQLite (default) or PostgreSQL |
| Checkpoints | LangGraph MemorySaver (default) or AsyncPostgresSaver |

---

## Project Structure

```
Langgraph_Project/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # FastAPI routers (health, generations, documents, chat …)
│   │   ├── config.py            # Pydantic Settings — all env vars
│   │   ├── db/                  # SQLAlchemy models, session factory, checkpointer factory
│   │   ├── schemas/             # Pydantic v2 request / response schemas
│   │   ├── services/            # Gemini, Tavily, Cloudinary, Pinecone, Document services
│   │   ├── workflows/
│   │   │   ├── state.py         # WorkflowState TypedDict + Pydantic models
│   │   │   ├── nodes/           # router, research, orchestrator, workers, merge, image_*
│   │   │   ├── blog_graph.py    # build_blog_graph() + get_compiled_workflow()
│   │   │   ├── rag_graph.py     # RAG chat graph
│   │   │   └── hitl_graph.py    # Human-in-the-loop approval graph
│   │   └── main.py              # App factory, lifespan, CORS, static files
│   ├── tests/                   # 11 pytest tests (health, validation, graph logic …)
│   ├── requirements.txt
│   ├── .env.example
│   └── .venv/
├── frontend/
│   ├── src/
│   │   ├── api/                 # Typed API modules (client, generations, documents …)
│   │   ├── app/                 # Router, QueryClient provider
│   │   ├── components/          # ui/ (Button, Card, Badge …) + shared/ (Markdown, Status …)
│   │   ├── features/            # dashboard, generation, workflow, blogs, chat, settings …
│   │   ├── hooks/               # useGenerationStream (SSE with reconnect)
│   │   ├── layouts/             # AppShell, Sidebar, Header
│   │   └── pages/               # All route pages (lazy-loaded)
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── .env.example
├── storage/
│   ├── documents/               # Local fallback for uploaded files
│   └── images/                  # Local fallback for generated images
└── README.md
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.10+ (tested on 3.13.7) |
| Node.js | 18+ (tested on 22.17.0) |
| npm | 9+ (tested on 11.19.0) |
| uv (optional) | any — used for fast pip installs |

---

## Environment Variables

### Backend — `backend/.env`

Copy `backend/.env.example` to `backend/.env` and fill in your credentials.

```env
# ── Required for AI features ──────────────────────────────────────
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_TEXT_MODEL=gemini-2.5-flash          # or gemini-2.5-pro
GEMINI_IMAGE_MODEL=gemini-3.1-flash-image   # Nano / Flash image via Gemini API
GEMINI_EMBEDDING_MODEL=models/gemini-embedding-2

# ── Required for web research ─────────────────────────────────────
TAVILY_API_KEY=your_tavily_api_key_here

# ── Optional: Cloudinary (images fall back to local ./storage/) ───
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret

# ── Optional: Pinecone (falls back to in-memory vector store) ─────
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=blog-rag
PINECONE_ENVIRONMENT=us-east-1-aws

# ── Optional: PostgreSQL (falls back to SQLite ./blog_studio.db) ──
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/blog_studio

# ── Optional: LangGraph PostgreSQL checkpoints ────────────────────
POSTGRES_CHECKPOINT_URL=postgresql://user:pass@localhost:5432/blog_studio

# ── App configuration ─────────────────────────────────────────────
STORAGE_DIR=./storage
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
DEBUG=false
```

> **Never commit `backend/.env` to version control.** It is listed in `.gitignore`.

### Frontend — `frontend/.env`

The frontend only needs to know the backend URL. **No secrets go here.**

```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## Installation

### Backend

```powershell
# From project root
# Using uv (recommended — much faster):
uv pip install -r backend/requirements.txt --python backend/.venv/Scripts/python.exe

# Or using standard pip inside the venv:
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

If the virtual environment does not yet exist:

```powershell
cd backend
uv venv        # creates backend/.venv
```

### Frontend

```powershell
cd frontend
npm install
```

---

## Running the Application

### 1. Start the Backend

```powershell
cd backend
.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --reload
```

On first startup the backend will:
- Create `./blog_studio.db` (SQLite) with all tables
- Create `./storage/documents/` and `./storage/images/` directories
- Log available service configuration (which APIs are connected)

**Verify:** `http://localhost:8000/api/health`

### 2. Start the Frontend

```powershell
cd frontend
npm run dev
```

**Open:** `http://localhost:5173`

---

## Running Tests

### Backend (11 tests, all passing)

```powershell
# From the project root directory:
backend\.venv\Scripts\pytest.exe backend/tests -v

# Or from the backend directory:
cd backend
.venv\Scripts\pytest.exe tests -v
```

Test coverage:
- `test_health.py` — health endpoint and DB status
- `test_validation.py` — Pydantic schema validation
- `test_router_branching.py` — Router node logic and `route_next` branching
- `test_worker_aggregation.py` — Worker state reducer correctness (the key fix from the brief)
- `test_image_handling.py` — Image placeholder cleanup and fallback
- `test_rag_pipeline.py` — Document chunking and in-memory vector store
- `test_checkpointer.py` — MemorySaver checkpoint factory

### Frontend (4 tests, all passing)

```powershell
cd frontend
npm run test
```

> **Note:** Vitest was replaced with Node.js native `--test` runner due to an out-of-memory crash on Node v22 with Vitest ≤4.x. Test files use `.mjs` extension and live in `frontend/src/test/`.

---

## Using the Application

1. **Navigate to `/generate`** — enter a topic, configure audience/tone/research options
2. **Submit** — a generation job is created and background execution begins immediately
3. **Watch progress** — the Workflow Monitor page streams real-time stage updates via SSE
4. **View the blog** — rendered Markdown, embedded images, and research sources
5. **Edit** — the built-in Markdown editor allows post-generation editing
6. **Export** — download the `.md` file directly from the blog detail page
7. **Documents** — upload PDFs to use as RAG context for future generations
8. **Chat** — RAG-powered chat against uploaded documents
9. **History** — browse and reopen all previous generations

---

## API Reference

Base URL: `http://localhost:8000`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Service health + dependency status |
| POST | `/api/generations` | Create new blog generation job |
| GET | `/api/generations` | List all generations |
| GET | `/api/generations/{id}` | Get generation details |
| GET | `/api/generations/{id}/stream` | SSE stream of workflow events |
| PATCH | `/api/generations/{id}` | Update blog markdown / title |
| DELETE | `/api/generations/{id}` | Delete generation |
| POST | `/api/documents` | Upload reference document |
| GET | `/api/documents` | List documents |
| GET | `/api/documents/{id}` | Document details + chunks |
| DELETE | `/api/documents/{id}` | Delete document |
| POST | `/api/chat` | RAG-powered chat query |
| GET | `/api/media` | List generated media assets |
| GET | `/api/settings` | Get current service configuration |

Interactive docs: `http://localhost:8000/docs`

---

## Before Deploying

Before deploying this application to staging or production, address the following security considerations:

1. **Authentication & Authorization**: The application currently has no user authentication, session management, or role-based access control. All generation history, uploaded reference documents, and configuration endpoints are open. Integrate an authentication layer (e.g. JWT, OAuth2, or FastAPI-Users) before public exposure.
2. **Public `/api/storage` Mount**: Local files in `./storage` (including uploaded reference PDFs/documents and generated images) are mounted directly via `StaticFiles(directory=settings.STORAGE_DIR)`. In production, restrict access to uploaded documents via authenticated download endpoints or offload private assets to a secured object store (such as S3, GCS, or authenticated Cloudinary delivery).
3. **CORS Restrictions**: Set `CORS_ORIGINS` in your production `.env` to your exact frontend domain(s) rather than localhost defaults.
4. **Production Database & Checkpointer**: Switch `DATABASE_URL` from SQLite to PostgreSQL with `asyncpg`, and configure `POSTGRES_CHECKPOINT_URL` for resilient, multi-worker LangGraph thread checkpoints.

---

## Known Limitations and Design Decisions

### Compiled LangGraph Execution & HITL
The workflow executes the compiled StateGraph via `workflow.astream(..., stream_mode="updates")` with LangGraph checkpointer integration (`MemorySaver` by default, or `AsyncPostgresSaver`). Node updates are mapped to the 8 UI stages and streamed to clients via SSE. Parallel section generation uses LangGraph's dynamic `Send` fan-out. Human-In-The-Loop (HITL) review uses native LangGraph `interrupt()`, storing the pending plan in the thread checkpoint and resuming via `Command(resume=decision)`.

### Startup Recovery & Vector Re-indexing
- Any generation left in `running` state when the server terminates is automatically transitioned to `failed` on startup to prevent stale UI state.
- In-memory vector stores are automatically re-indexed in a background task on server startup from persisted document chunks.
- If a configured Pinecone index is missing or unreachable, the system logs a warning, falls back to in-memory cosine similarity, and surfaces the status in `/api/health`, `/api/settings`, and the Settings UI.

### Segregated Embedding Spaces
The application avoids mixing embedding vector spaces. When Gemini embeddings are active, failures will not silently mix fallback hash vectors into the index; instead, the document is marked `failed` with a retryable status. Document retrieval queries use single batched `IN` SQL queries rather than N+1 lookups.

### Filename Sanitization & JSON Mutation Tracking
- Uploaded filenames are sanitized using `Path(filename).name` to prevent directory traversal attacks.
- All SQLAlchemy JSON columns (`stage_statuses`, `image_specs`, `warnings`, `metadata_json`) use `MutableDict` and `MutableList` so in-place mutations are tracked by the ORM unit-of-work.

### Chroma vs Pinecone
The architecture diagrams reference **Chroma** as the vector store. The implementation uses **Pinecone** with a full **in-memory cosine-similarity fallback** that activates automatically when `PINECONE_API_KEY` is not set.

### Gemini Models
The application defaults to current Gemini models:
- Text: `gemini-2.5-flash` (or `gemini-2.5-pro`)
- Image: `gemini-3.1-flash-image` (via Gemini API `response_modalities=["IMAGE"]`)
- Embeddings: `models/gemini-embedding-2`

### SQLite Default
The application defaults to SQLite with `aiosqlite` for zero-config local development. Set `DATABASE_URL` to a PostgreSQL connection string for production.

---

## External Service Credentials

| Service | Get API Key | Free Tier |
|---------|------------|-----------|
| Google Gemini | [Google AI Studio](https://aistudio.google.com/) | Yes |
| Tavily | [app.tavily.com](https://app.tavily.com/) | Yes (1000 searches/month) |
| Pinecone | [pinecone.io](https://www.pinecone.io/) | Yes (1 index, 2GB) |
| Cloudinary | [cloudinary.com](https://cloudinary.com/) | Yes (25 credits/month) |

---

## Troubleshooting

**Backend won't start**
```powershell
# Verify from the backend directory
cd backend
.venv\Scripts\python.exe -c "from app.main import app; print('OK')"
```

**Frontend shows API errors**
- Confirm `frontend/.env` has `VITE_API_BASE_URL=http://localhost:8000`
- Confirm backend is running and `http://localhost:8000/api/health` returns `{"status":"healthy"}`

**Blog generation stays in `pending`**
- Check that `GOOGLE_API_KEY` is set in `backend/.env`
- Check backend logs for errors during stage execution

**RAG chat returns no results**
- Upload a document first via `/documents`
- Confirm document status is `ready` (processing completed)
