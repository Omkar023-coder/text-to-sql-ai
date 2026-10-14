<div align="center">

# 🗄️ Text-to-SQL AI

**Ask questions about your database in plain English — get instant SQL and results.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Groq](https://img.shields.io/badge/Groq-LLM-F55036?style=flat-square)](https://console.groq.com/)
[![License](https://img.shields.io/badge/License-Educational-green?style=flat-square)](#license)

[Features](#features) · [Architecture](#architecture) · [Quick Start](#quick-start) · [API Reference](#api-reference) · [Example Queries](#example-queries)

</div>

---

## What is this?

Text-to-SQL AI converts natural-language questions into validated SQL queries, executes them against a SQLite database, and visualizes the results — all from a professional three-panel React interface.

It handles **ambiguous questions** through a schema-aware clarification engine: instead of guessing what "best customer" means, it asks you first.

```
"Show me the best customer."
       ↓
  ❓ What do you mean by 'best'?
     • The customer with the highest total revenue
     • The customer with the most orders
       ↓
  ✅ SELECT c.name, SUM(o.amount) AS total_revenue
       FROM customers c
       JOIN orders o ON c.id = o.customer_id
       GROUP BY c.name
       ORDER BY total_revenue DESC
       LIMIT 1;
```

---

## Features

### 🔍 Query Pipeline
- **Natural language → SQL** via Groq LLM (`openai/gpt-oss-20b`)
- **Schema-aware RAG retrieval** — fetches the most relevant schema columns before generation
- **Clarification engine** — asks follow-up questions only when genuinely ambiguous
- **SELECT-only enforcement** — every query is validated before execution; DROP, DELETE, INSERT, UPDATE and others are always rejected
- **Read-only database** — cannot modify data under any circumstances

### 🖥️ Frontend
- Three-panel layout: History sidebar · Chat panel · Data panel
- Clarification cards with one-click suggestion chips
- SQL editor with manual edit support and a safety indicator badge
- Results table with column sorting, search, and pagination
- **Bar, line, and pie charts** with automatic chart-type suggestion
- Schema explorer showing all tables and columns
- Database health status badge

### 📚 History
- Persistent session history stored in **localStorage** (survives page refresh)
- Sessions group multiple queries from one conversation
- Click any past query to restore its SQL and results instantly — no re-execution
- Pin important sessions, delete individual entries, or clear all history
- Full-text search across session titles and query text

---

## Pipeline

```
┌──────────────────────────────────────────────────┐
│                  User Question                    │
└──────────────────────────┬───────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  Metadata RAG Search   │  ← Retrieves relevant schema columns
              └────────────┬───────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  Clarification Engine  │  ← Asks follow-up if ambiguous
              └────────────┬───────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │    SQL Generation      │  ← LLM generates SELECT query
              └────────────┬───────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │    SQL Validation      │  ← SELECT-only enforcement
              └────────────┬───────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │    SQL Execution       │  ← Runs against SQLite
              └────────────┬───────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  Table + Chart Results │
              └────────────────────────┘
```

---

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                      Browser (React SPA)                        │
│                                                                  │
│  ┌───────────────┬─────────────────────┬──────────────────────┐ │
│  │   Sidebar     │     Chat Panel      │     Data Panel       │ │
│  │               │                     │                      │ │
│  │  History      │  User messages      │  SQL editor          │ │
│  │  Sessions     │  Clarification      │  Execute button      │ │
│  │  Schema       │  SQL bubbles        │  Results table       │ │
│  │  Health       │  Error states       │  Bar/Line/Pie charts │ │
│  └───────────────┴─────────────────────┴──────────────────────┘ │
└──────────────────────────────┬─────────────────────────────────┘
                               │  HTTP / JSON
┌──────────────────────────────▼─────────────────────────────────┐
│                FastAPI  (backend/main.py)                        │
│                                                                  │
│   POST /ask    POST /clarify    POST /execute                    │
│   GET  /health  GET  /schema    GET  /                           │
└───────┬─────────────────────────────────────────────┬──────────┘
        │                                             │
┌───────▼──────────────┐              ┌───────────────▼──────────┐
│  Agent Pipeline      │              │  SQLite Database          │
│                      │              │                           │
│  orchestrator.py     │              │  customers  (10 rows)     │
│  clarification.py    │              │  products   (5 rows)      │
│  sql_generator.py    │              │  orders     (12 rows)     │
│  metadata_search.py  │              │                           │
│  sql_validator.py    │              └───────────────────────────┘
└──────────────────────┘
```

---

## Tech Stack

### Backend
| | Technology | Version | Purpose |
|---|---|---|---|
| 🐍 | Python | 3.11+ | Backend language |
| ⚡ | FastAPI | 0.111.0 | HTTP API framework |
| 🗄️ | SQLAlchemy | 2.0.25 | Database ORM |
| 📦 | SQLite | 3 | Demo database |
| 🤖 | Groq API | — | LLM inference (clarification + SQL gen) |
| 🔢 | sentence-transformers | 3.0.0 | Semantic schema embeddings |
| 🔑 | python-dotenv | 1.0.1 | Environment variable loading |

### Frontend
| | Technology | Version | Purpose |
|---|---|---|---|
| ⚛️ | React | 18 | UI framework |
| 🔷 | TypeScript | 5 | Type safety |
| ⚡ | Vite | 5 | Build tool + dev server |
| 🎨 | Tailwind CSS | 3 | Utility-first styling |
| 📊 | Recharts | 2 | Data visualization |
| 🎯 | Radix UI | — | Accessible component primitives |
| 🖼️ | Lucide React | — | Icon set |

### Testing
| | Tool | Purpose |
|---|---|---|
| 🧪 | pytest | Backend unit & integration tests |
| ⚡ | Vitest | Frontend unit tests |
| 🎭 | @testing-library/react | React hook + component testing |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+ and npm
- Groq API key — free tier at [console.groq.com](https://console.groq.com)

### 1. Clone

```bash
git clone https://github.com/your-username/text-to-sql-ai.git
cd text-to-sql-ai
```

### 2. Python environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` and set your key:

```env
GROQ_API_KEY=your_actual_groq_api_key_here
```

### 5. Set up the database

```bash
python -m backend.database.setup
```

Creates `text_to_sql.db` with 10 customers, 5 products, and 12 orders.

### 6. Build the frontend

```bash
cd frontend
npm install
npm run build
cd ..
```

### 7. Start the server

```bash
python -m uvicorn backend.main:app --reload
```

### 8. Open in browser

```
http://127.0.0.1:8000
```

> The FastAPI process serves both the API and the built React frontend from a single port.

---

## Development Mode

For active frontend development with hot-reload, run two terminals simultaneously:

**Terminal 1 — Backend**
```bash
python -m uvicorn backend.main:app --reload
```

**Terminal 2 — Frontend**
```bash
cd frontend
npm run dev
```

Then open `http://localhost:5173`. The Vite dev server proxies all API calls to port 8000.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ Yes | API key from [console.groq.com](https://console.groq.com). Used server-side only — never sent to the browser. |

Copy `.env.example` to `.env` to get started. See `.env.example` for the template.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the React frontend |
| `GET` | `/health` | API and database connectivity status |
| `GET` | `/schema` | Table and column metadata for the schema explorer |
| `POST` | `/ask` | Submit a natural-language question |
| `POST` | `/clarify` | Submit a clarification answer |
| `POST` | `/execute` | Execute a validated SQL SELECT query |

### POST `/ask`

```json
// Request
{ "question": "How many customers do we have?" }

// Response — direct SQL
{
  "status": "sql_generated",
  "question": "How many customers do we have?",
  "sql": "SELECT COUNT(*) FROM customers;",
  "retrieved_schema": ["customers.id", "customers.name"]
}

// Response — clarification needed
{
  "status": "clarification_required",
  "original_question": "Show me the best customer.",
  "clarification_question": "What do you mean by 'best'?",
  "suggestions": [
    "The customer with the highest total revenue",
    "The customer with the most orders"
  ]
}
```

### POST `/execute`

```json
// Request
{ "sql": "SELECT COUNT(*) FROM customers;" }

// Response
{
  "columns": ["COUNT(*)"],
  "rows": [[10]]
}
```

> Interactive API docs available at `http://127.0.0.1:8000/docs` when the server is running.

---

## Example Queries

The demo database has customers, products, and orders. Try these:

**Simple lookups**
```
How many customers do we have?
Show me all products.
What is the total revenue?
Where do our customers live?
```

**Aggregations**
```
Show the top 5 customers by revenue.
Which products sold the most?
What is the total revenue by city?
How many orders does each customer have?
```

**Clarification triggers** *(these are intentionally ambiguous — the system will ask a follow-up)*
```
Show me the best customer.
Which products generated the most sales?
Who is our most valuable customer?
```

---

## Database Schema

```sql
customers  →  id, name, email, city, signup_date
products   →  id, name, category, price
orders     →  id, customer_id, product_id, order_date, quantity, amount
```

10 customers · 5 products · 12 orders · all dates in 2026

---

## Project Structure

```
text-to-sql-ai/
│
├── backend/
│   ├── main.py                        FastAPI app — all API endpoints
│   ├── agents/
│   │   ├── orchestrator.py            Pipeline coordinator
│   │   ├── clarification.py           Schema-aware clarification LLM
│   │   ├── clarification_resolver.py  Ambiguity resolver LLM
│   │   └── sql_generator.py           SQL generation with RAG context
│   ├── rag/
│   │   ├── schema_data.py             Schema corpus (15 columns)
│   │   ├── metadata_search.py         Primary production retriever
│   │   ├── keyword_search.py          Keyword-based retriever
│   │   ├── semantic_search.py         Embedding-based retriever
│   │   └── hybrid_search.py           RRF hybrid retriever
│   ├── database/
│   │   ├── connection.py              SQLAlchemy engine (path-safe)
│   │   ├── executor.py                Query execution
│   │   └── setup.py                   Schema creation + demo seed data
│   ├── security/
│   │   └── sql_validator.py           SELECT-only enforcement
│   └── evaluation/
│       └── retrieval_evaluator.py     RAG evaluation framework
│
├── frontend/
│   └── src/
│       ├── App.tsx                    Root layout + session lifecycle
│       ├── api/                       Typed fetch wrappers
│       ├── components/
│       │   ├── layout/                Sidebar, ChatPanel, DataPanel
│       │   ├── chat/                  Message bubbles, clarification card
│       │   ├── data/                  SQL editor, results table, charts
│       │   └── sidebar/               History, schema explorer, health
│       ├── hooks/                     useConversation, useQueryExecution, useHistory
│       ├── lib/                       historyStorage, chartSuggestion, sqlValidation
│       └── types/                     TypeScript definitions
│
├── test/                              Backend test suite (86 tests)
├── data/evaluation/                   RAG evaluation datasets
├── .env.example                       Environment variable template
├── requirements.txt                   Pinned Python dependencies
└── text_to_sql.db                     SQLite database (created by setup.py)
```

---

## Security

| Control | Detail |
|---|---|
| Read-only architecture | Only SELECT queries are executed — the database cannot be modified |
| SQL validation | All queries pass through `sql_validator.py` before execution |
| Blocked statements | DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE, CREATE, REPLACE, ATTACH, DETACH |
| Multi-statement protection | Queries with early semicolons are rejected |
| API key isolation | `GROQ_API_KEY` is server-side only — never reaches the browser |
| No secrets in history | localStorage stores only questions, SQL, results, and timestamps |
| Error sanitization | Internal stack traces are never exposed in API responses |

---

## Running Tests

```bash
# Backend (86 tests)
python -m pytest --tb=no -q

# Frontend (252 tests)
cd frontend
npm run test

# TypeScript check
cd frontend
npx tsc --noEmit

# Production build check
cd frontend
npm run build
```

---

## Project Status

| Phase | Description | Status |
|---|---|---|
| Phase 7 | Retrieval + Schema-Aware Clarification | ✅ Complete |
| Phase 8 | FastAPI Backend | ✅ Complete |
| Phase 9.1 | React / TypeScript Foundation | ✅ Complete |
| Phase 9.2 | Professional Three-Panel UI | ✅ Complete |
| Phase 9.3 | Conversation Flow | ✅ Complete |
| Phase 9.4 | SQL Execution + Results Table | ✅ Complete |
| Phase 9.5 | Data Visualization (Charts) | ✅ Complete |
| Phase 9.6 | Persistent Query History | ✅ Complete |
| Phase 10.1 | Audit — Dependencies, Paths, Docs | ✅ Complete |
| Phase 10.2 | Production Hardening | 🔄 In progress |

---

## Limitations

- **Fixed demo dataset** — uses a small hardcoded SQLite database; not connected to a production database
- **Browser-local history** — localStorage is device-specific and not synced
- **No authentication** — no user login, session isolation, or access control
- **No rate limiting** — excessive requests could exhaust Groq quota
- **Single schema** — the retrieval system is calibrated to the demo schema; a different database requires updating `backend/rag/schema_data.py`
- **Bundle size** — the React bundle is ~708 KB (Recharts is the largest contributor)

---

## License

This project is for educational and portfolio purposes.
