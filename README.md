# 🗄️ Text-to-SQL AI

**Transform natural language questions into SQL queries and get instant results from your PostgreSQL database.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-316192?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Groq](https://img.shields.io/badge/Groq-LLM-F55036?style=flat-square)](https://console.groq.com/)

[Features](#-key-features) · [Architecture](#-system-architecture) · [Quick Start](#-quick-start) · [API Reference](#-api-documentation) · [Testing](#-testing)

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Demo](#-demo)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Technology Stack](#-technology-stack)
- [How It Works](#-how-it-works)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation and Setup](#-installation-and-setup)
- [PostgreSQL Database Configuration](#-postgresql-database-configuration)
- [Environment Variables](#-environment-variables)
- [Running the Application](#-running-the-application)
- [API Documentation](#-api-documentation)
- [Example Usage](#-example-usage)
- [Testing](#-testing)
- [Security Considerations](#-security-considerations)
- [Troubleshooting](#-troubleshooting)
- [Future Enhancements](#-future-enhancements)
- [Author](#-author)

---

## 🎯 Project Overview

Text-to-SQL AI is an intelligent database query system that bridges the gap between natural language and SQL. It allows users to ask questions about their data in plain English and automatically generates, validates, and executes SQL queries against a PostgreSQL database.

**What makes it special:**
- **Schema-aware clarification**: Instead of guessing ambiguous terms like "best customer," it asks you to clarify
- **RAG-enhanced generation**: Retrieves relevant schema context before generating SQL
- **Read-only security**: Enforces SELECT-only queries with multiple validation layers
- **Professional UI**: Three-panel React interface with conversation history, SQL editing, and data visualization
- **Production-ready**: Comprehensive test suite (393 tests), security hardening, and error handling

This project was developed as part of my winning solution for **Smart India Hackathon 2025 (National Winner)** 🏆

---

## 🖼️ Demo

### Application Interface

The application features a professional three-panel layout with real-time query processing and results visualization:

![Text-to-SQL AI Application Demo](assets/demo.png)

*Interactive three-panel interface: History sidebar with sessions and schema explorer · Chat panel with conversation flow · Data panel with SQL editor, results table, and charts*

---

### Query Response Types

The system intelligently handles three types of user interactions:

#### 1. ✅ Successful Queries — Direct SQL Generation

When a question is clear and unambiguous, the system generates SQL directly and executes it:

**Example:** "What is the total revenue?"

![Successful Query Example](assets/success-query.png)

**Response:**
- ✅ Green success indicator
- Generated SQL query displayed
- Schema context used shown
- Results rendered in table format
- Execution time displayed

---

#### 2. ❓ Ambiguous Queries — Clarification Required

When a question contains ambiguous terms, the system asks for clarification before generating SQL:

**Example:** "Show me the best customers."

![Clarification Query Example](assets/clarification-query.png)

**Response:**
- 🟡 Yellow clarification card
- Question asking what "best" means
- **Suggestion chips** with possible interpretations:
  - "Customers with highest total revenue"
  - "Customers with most orders"
  - "Customers with highest average order amount"
- Option to type custom clarification

Once the user selects or provides clarification, the system generates the appropriate SQL.

---

#### 3. ❌ Rejected Queries — Security Protection

When a request attempts a destructive operation (UPDATE, DELETE, INSERT, etc.), the system rejects it immediately:

**Example:** "INSERT INTO customers (name) VALUES ('Omkar');"

![Rejected Query Example](assets/rejected-query.png)

**Response:**
- 🔴 Red error indicator
- Clear security message: *"This application only supports read-only SELECT queries. Requests to insert/add data are not allowed."*
- "Try again" button to submit a new query
- No SQL generated or executed

This multi-layer security ensures the database remains read-only at all times.

---

## ✨ Key Features

### 🤖 Intelligent Query Pipeline
- **Natural language to SQL**: Powered by Groq's `openai/gpt-oss-20b` model
- **RAG-based schema retrieval**: Uses semantic embeddings (`sentence-transformers`) to find relevant columns before SQL generation
- **Hybrid search**: Combines keyword matching, semantic embeddings, and metadata filtering (RRF fusion)
- **Ambiguity detection**: Schema-aware clarification engine asks follow-up questions only when needed

### 🛡️ Security & Validation
- **Multi-layer destructive intent detection**: Natural language patterns + SQL syntax detection
- **SELECT-only enforcement**: Blocks UPDATE, DELETE, INSERT, DROP, ALTER, TRUNCATE before execution
- **SQL validator**: Final mandatory security layer validates generated queries
- **Read-only database**: Cannot modify data under any circumstances
- **Input sanitization**: Protected against SQL injection and prompt injection attacks

### 💻 Modern Frontend (React + TypeScript)
- **Three-panel layout**: History sidebar · Chat panel · Data panel
- **Conversation flow**: Natural chat interface with message bubbles and clarification cards
- **SQL editor**: Manual editing with syntax highlighting and safety indicators
- **Results visualization**: Sortable data tables + automatic chart generation (bar, line, pie)
- **Persistent history**: localStorage-based session management with search and pinning
- **Schema explorer**: Browse all tables, columns, and data types
- **Real-time health monitoring**: Database connectivity status badge

### 📊 Data Analysis
- **Smart chart suggestions**: Automatically recommends chart types based on query results
- **Interactive visualizations**: Built with Recharts (bar charts, line charts, pie charts)
- **Export-ready results**: Tables with sorting, filtering, and pagination

---

## 🏗️ System Architecture

![Text-to-SQL AI System Architecture](assets/architecture.png)

### Request Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Question (Natural Language)              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │  POST /ask                    │
              │  (FastAPI Endpoint)           │
              └──────────────┬────────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │  Intent Validator             │  ← Rejects destructive requests
              │  (Regex + SQL syntax)         │     (UPDATE, DELETE, etc.)
              └──────────────┬────────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │  RAG Metadata Search          │  ← Semantic + keyword + hybrid
              │  (Hybrid retrieval)           │     Retrieves relevant schema
              └──────────────┬────────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │  Clarification Engine         │  ← LLM judges ambiguity
              │  (Schema-aware LLM)           │     using retrieved context
              └──────────────┬────────────────┘
                             │
                   ┌─────────┴─────────┐
                   │                   │
                   ▼                   ▼
          Ambiguous?           Clear?
                   │                   │
                   ▼                   ▼
    ┌──────────────────────┐  ┌──────────────────────┐
    │ Return clarification │  │  SQL Generator        │
    │ suggestions          │  │  (LLM with schema)    │
    └──────────────────────┘  └──────────┬───────────┘
                                          │
                                          ▼
                             ┌──────────────────────────┐
                             │  SQL Validator            │  ← SELECT-only check
                             │  (Regex + keyword block)  │     Multi-statement block
                             └──────────┬────────────────┘
                                        │
                                        ▼
                             ┌──────────────────────────┐
                             │  POST /execute            │
                             │  (Query Executor)         │
                             └──────────┬────────────────┘
                                        │
                                        ▼
                             ┌──────────────────────────┐
                             │  PostgreSQL Database      │
                             │  (Customers, Products,    │
                             │   Orders tables)          │
                             └──────────┬────────────────┘
                                        │
                                        ▼
                             ┌──────────────────────────┐
                             │  JSON Results             │
                             │  (Columns + Rows)         │
                             └──────────────────────────┘
```

### Architecture Layers

| Layer | Component | Technology | Purpose |
|-------|-----------|-----------|---------|
| **Presentation** | React Frontend | React 18 + TypeScript | User interface and interaction |
| **API** | FastAPI Server | FastAPI 0.111.0 | REST endpoints + static file serving |
| **Security** | Intent Validator | Regex patterns | Detect destructive requests |
| **AI Pipeline** | Orchestrator | Python | Coordinate RAG → Clarification → SQL |
| **Retrieval** | Hybrid Search | sentence-transformers | Schema context retrieval |
| **Generation** | SQL Generator | Groq LLM | Natural language → SQL |
| **Validation** | SQL Validator | Regex + keyword block | SELECT-only enforcement |
| **Execution** | Query Executor | SQLAlchemy | Safe query execution |
| **Storage** | PostgreSQL | PostgreSQL 16+ | Relational database |

---

## 🛠️ Technology Stack

### Backend

| Technology | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.11+ | Backend programming language |
| **FastAPI** | 0.111.0 | Modern async web framework |
| **Uvicorn** | 0.29.0 | ASGI server with hot-reload |
| **SQLAlchemy** | 2.0.25 | Database ORM and query builder |
| **psycopg2-binary** | 2.9.9 | PostgreSQL database adapter |
| **OpenAI SDK** | 1.109.1 | Groq API client (OpenAI-compatible) |
| **sentence-transformers** | 3.0.0 | Semantic embeddings for RAG |
| **PyTorch** | 2.2.2+cpu | Deep learning framework (CPU) |
| **python-dotenv** | 1.0.1 | Environment variable management |
| **slowapi** | 0.1.10 | Rate limiting middleware |
| **pytest** | 7.4.0 | Testing framework |

### Frontend

| Technology | Version | Purpose |
|-----------|---------|---------|
| **React** | 18.3.1 | UI component library |
| **TypeScript** | 5.6.3 | Type-safe JavaScript |
| **Vite** | 5.4.11 | Build tool and dev server |
| **Tailwind CSS** | 3.4.15 | Utility-first CSS framework |
| **Recharts** | 2.13.3 | Data visualization library |
| **Radix UI** | Latest | Accessible component primitives |
| **Lucide React** | 0.462.0 | Icon library |
| **Vitest** | 2.1.5 | Unit testing framework |
| **@testing-library/react** | 16.0.1 | React testing utilities |

### Database

| Technology | Version | Purpose |
|-----------|---------|---------|
| **PostgreSQL** | 16+ | Production-grade relational database |

### AI/ML

| Model | Provider | Purpose |
|-------|----------|---------|
| `openai/gpt-oss-20b` | Groq | SQL generation and clarification |
| `all-MiniLM-L6-v2` | sentence-transformers | Schema embeddings (384-dim) |

---

## 🔄 How It Works

### 1. User Submits Question
```
User: "Show me the top 5 customers by revenue"
```

### 2. Intent Validation
- Checks for destructive keywords (UPDATE, DELETE, DROP, etc.)
- Validates both natural language and SQL syntax patterns
- **Rejected example**: "Delete customer records" → Status: `rejected`

### 3. Schema Retrieval (RAG)
- Semantic search using embeddings
- Keyword-based search for exact matches
- Metadata filtering (table relationships)
- **Hybrid fusion** combines all three using Reciprocal Rank Fusion
- Returns relevant columns: `customers.name`, `orders.amount`, `orders.customer_id`

### 4. Clarification Check
- LLM analyzes question + retrieved schema
- Determines if question is **clear** or **ambiguous**
- **Clear**: Proceeds to SQL generation
- **Ambiguous**: Returns clarification suggestions
  ```json
  {
    "status": "clarification_required",
    "clarification_question": "What do you mean by 'best'?",
    "suggestions": [
      "Customer with highest total revenue",
      "Customer with most orders"
    ]
  }
  ```

### 5. SQL Generation
- LLM generates PostgreSQL query using retrieved schema context
- Validates output starts with `SELECT`
- Strips markdown fences if present

### 6. SQL Validation
- Final security check: SELECT-only enforcement
- Blocks forbidden keywords (UPDATE, DELETE, DROP, etc.)
- Prevents multi-statement queries
- Checks for dangerous functions (`pg_sleep`, `generate_series`, etc.)

### 7. Query Execution
- Executes validated query against PostgreSQL
- Returns results as JSON: `{columns: [...], rows: [...]}`
- Catches and sanitizes database errors

### 8. Frontend Display
- Renders results in sortable table
- Generates chart suggestions based on data types
- Saves to conversation history (localStorage)

---

## 📁 Project Structure

```
text-to-sql-ai/
│
├── backend/
│   ├── main.py                        # FastAPI app with all endpoints
│   ├── agents/
│   │   ├── orchestrator.py            # Pipeline coordinator
│   │   ├── clarification.py           # Schema-aware clarification LLM
│   │   ├── clarification_resolver.py  # Resolves ambiguous questions
│   │   └── sql_generator.py           # SQL generation with RAG context
│   ├── rag/
│   │   ├── schema_data.py             # Schema corpus (15 columns)
│   │   ├── metadata_search.py         # Production hybrid retriever
│   │   ├── keyword_search.py          # Keyword-based retriever
│   │   ├── semantic_search.py         # Embedding-based retriever
│   │   └── hybrid_search.py           # RRF hybrid fusion
│   ├── database/
│   │   ├── connection.py              # PostgreSQL engine configuration
│   │   ├── executor.py                # Safe query execution
│   │   └── setup.py                   # Schema creation + seed data
│   ├── security/
│   │   ├── intent_validator.py        # Destructive intent detection
│   │   └── sql_validator.py           # SELECT-only enforcement
│   └── evaluation/
│       ├── retrieval_evaluator.py     # RAG evaluation framework
│       └── retrieval_metrics.py       # Precision, recall, MRR metrics
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx                    # Root layout + routing
│   │   ├── api/                       # Typed fetch wrappers
│   │   │   ├── ask.ts                 # POST /ask
│   │   │   ├── clarify.ts             # POST /clarify
│   │   │   ├── execute.ts             # POST /execute
│   │   │   ├── health.ts              # GET /health
│   │   │   └── schema.ts              # GET /schema
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx        # History + schema explorer
│   │   │   │   ├── ChatPanel.tsx      # Conversation interface
│   │   │   │   └── DataPanel.tsx      # SQL editor + results
│   │   │   ├── chat/
│   │   │   │   ├── MessageBubble.tsx  # User/assistant messages
│   │   │   │   ├── ClarificationCard.tsx  # Suggestion chips
│   │   │   │   └── EmptyState.tsx     # Starter suggestions
│   │   │   ├── data/
│   │   │   │   ├── SqlEditor.tsx      # Editable SQL with highlight
│   │   │   │   ├── ResultsTable.tsx   # Sortable data table
│   │   │   │   └── ChartView.tsx      # Bar/line/pie charts
│   │   │   └── sidebar/
│   │   │       ├── HistoryList.tsx    # Session list
│   │   │       ├── SchemaExplorer.tsx # Table/column browser
│   │   │       └── HealthBadge.tsx    # DB status indicator
│   │   ├── hooks/
│   │   │   ├── useConversation.ts     # Conversation state management
│   │   │   ├── useQueryExecution.ts   # SQL execution logic
│   │   │   └── useHistory.ts          # localStorage persistence
│   │   ├── lib/
│   │   │   ├── historyStorage.ts      # Session CRUD operations
│   │   │   ├── chartSuggestion.ts     # Auto chart type detection
│   │   │   └── sqlValidation.ts       # Frontend SQL checks
│   │   └── types/
│   │       ├── api.ts                 # API request/response types
│   │       └── conversation.ts        # Turn state types
│   ├── dist/                          # Production build output
│   ├── package.json                   # Node dependencies
│   └── vite.config.ts                 # Build configuration
│
├── test/
│   ├── test_intent_validator.py       # 66 security tests
│   ├── test_sql_validator.py          # 53 validation tests
│   ├── test_production_errors.py      # 78 regression tests
│   ├── test_remaining_security_bug.py # 33 security edge cases
│   ├── test_orchestrator.py           # 12 pipeline tests
│   ├── test_clarification.py          # LLM clarification tests
│   ├── test_hybrid_search.py          # RAG retrieval tests
│   └── ...                            # 393 tests total
│
├── data/
│   └── evaluation/
│       └── retrieval_dataset.json     # RAG evaluation queries
│
├── .env.example                       # Environment template
├── requirements.txt                   # Python dependencies
├── README.md                          # This file
└── assets/
    ├── demo.png                       # Application screenshot
    └── architecture.png               # System diagram
```

---

## ✅ Prerequisites

Before starting, ensure you have:

| Requirement | Version | Download |
|------------|---------|----------|
| **Python** | 3.11+ | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 20+ | [nodejs.org](https://nodejs.org/) |
| **npm** | 10+ | Included with Node.js |
| **PostgreSQL** | 16+ | [postgresql.org](https://www.postgresql.org/download/) |
| **Git** | Latest | [git-scm.com](https://git-scm.com/) |
| **Groq API Key** | Free tier | [console.groq.com](https://console.groq.com/) |

---

## 🚀 Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Omkar023-coder/text-to-sql-ai.git
cd text-to-sql-ai
```

### 2. Create Python Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
# Install PyTorch CPU version first (required for sentence-transformers)
pip install torch==2.2.2+cpu --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
pip install -r requirements.txt
```

> **Note**: PyTorch must be installed separately from the PyTorch wheel index because the CPU-only build is not available on PyPI. If you skip the first command, pip will download the CUDA build (~2 GB).

### 4. Configure Environment Variables

Copy the example environment file:

**Windows:**
```bash
copy .env.example .env
```

**macOS/Linux:**
```bash
cp .env.example .env
```

Edit `.env` and configure the required variables (see [Environment Variables](#-environment-variables) section).

---

## 🗄️ PostgreSQL Database Configuration

### Option 1: Local PostgreSQL Installation

#### Install PostgreSQL

**Windows:**
1. Download PostgreSQL 16+ from [postgresql.org](https://www.postgresql.org/download/windows/)
2. Run the installer (includes pgAdmin 4 GUI)
3. Remember the superuser password you set during installation

**macOS (Homebrew):**
```bash
brew install postgresql@16
brew services start postgresql@16
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

#### Create Database

Open pgAdmin 4 or use the command line:

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE text_to_sql_ai;

# Exit psql
\q
```

#### Update DATABASE_URL

Edit your `.env` file:

```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/text_to_sql_ai
```

Replace `yourpassword` with your PostgreSQL superuser password.

### Option 2: Cloud PostgreSQL (Railway, Render, Supabase)

1. Sign up for a free PostgreSQL service
2. Create a new PostgreSQL database
3. Copy the connection string provided
4. Update `.env`:

```env
DATABASE_URL=postgresql://user:password@host:5432/dbname?sslmode=require
```

### Initialize Database Schema and Seed Data

Run the setup script to create tables and insert sample data:

```bash
python -m backend.database.setup
```

**What this does:**
- Creates `customers`, `products`, and `orders` tables
- Inserts 10 sample customers
- Inserts 5 sample products
- Inserts 12 sample orders
- **Idempotent**: Safe to run multiple times (uses `ON CONFLICT DO NOTHING`)

**Verify database connection:**

```bash
# Test connection
psql -U postgres -d text_to_sql_ai -c "SELECT COUNT(*) FROM customers;"
```

Expected output: `10`

### Database Schema

```sql
-- Customers table
CREATE TABLE customers (
    id          SERIAL         PRIMARY KEY,
    name        TEXT           NOT NULL,
    email       TEXT           UNIQUE NOT NULL,
    city        TEXT,
    signup_date DATE           NOT NULL
);

-- Products table
CREATE TABLE products (
    id       SERIAL          PRIMARY KEY,
    name     TEXT            UNIQUE NOT NULL,
    category TEXT,
    price    NUMERIC(12, 2)  NOT NULL
);

-- Orders table
CREATE TABLE orders (
    id          SERIAL          PRIMARY KEY,
    customer_id INTEGER         NOT NULL REFERENCES customers(id),
    product_id  INTEGER         NOT NULL REFERENCES products(id),
    order_date  DATE            NOT NULL,
    quantity    INTEGER         NOT NULL,
    amount      NUMERIC(12, 2)  NOT NULL,
    seed_id     TEXT            UNIQUE
);
```

---

## 🔐 Environment Variables

Create a `.env` file in the project root with the following variables:

### Required Variables

```env
# Groq API Key (REQUIRED)
# Get a free API key at: https://console.groq.com
GROQ_API_KEY=your_actual_groq_api_key_here

# PostgreSQL Database URL (REQUIRED)
# Format: postgresql://<user>:<password>@<host>:<port>/<database>
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/text_to_sql_ai

# CORS Allowed Origins (REQUIRED for production)
# Development default: http://localhost:5173
# Production: Replace with your deployed frontend URL
CORS_ORIGINS=http://localhost:5173
```

### Optional Variables (Rate Limiting)

```env
# Rate limiting per IP address (requests per minute)
RATE_LIMIT_ASK=20/minute
RATE_LIMIT_CLARIFY=20/minute
RATE_LIMIT_EXECUTE=60/minute
```

### Security Notes

- ⚠️ **Never commit `.env` to version control**
- ✅ The `.env` file is already in `.gitignore`
- ✅ API keys are server-side only (never sent to browser)
- ✅ Database credentials are never exposed in API responses
- ✅ Use strong passwords for production databases
- ✅ Enable SSL/TLS for cloud PostgreSQL connections (`?sslmode=require`)

---

## ▶️ Running the Application

### Production Mode (Recommended)

#### 1. Build the Frontend

```bash
cd frontend
npm install
npm run build
cd ..
```

This creates an optimized production build in `frontend/dist/`.

#### 2. Start the Backend Server

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

#### 3. Open in Browser

```
http://127.0.0.1:8000
```

The FastAPI server serves both:
- API endpoints at `/ask`, `/clarify`, `/execute`, etc.
- React frontend (static files from `frontend/dist/`)

### Development Mode (Hot Reload)

For active development with automatic reloading:

**Terminal 1 — Backend with hot reload:**
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend dev server:**
```bash
cd frontend
npm run dev
```

**Open:**
```
http://localhost:5173
```

The Vite dev server (port 5173) proxies all API calls to the FastAPI backend (port 8000).

### Interactive API Documentation

FastAPI provides auto-generated interactive docs:

**Swagger UI:**
```
http://127.0.0.1:8000/docs
```

**ReDoc:**
```
http://127.0.0.1:8000/redoc
```

---

## 📡 API Documentation

### Base URL
```
http://127.0.0.1:8000
```

### Endpoints

#### `POST /ask`

Submit a natural-language question.

**Request Body:**
```json
{
  "question": "How many customers do we have?"
}
```

**Response (SQL Generated):**
```json
{
  "status": "sql_generated",
  "question": "How many customers do we have?",
  "sql": "SELECT COUNT(*) AS total_customers FROM customers;",
  "retrieved_schema": ["customers.id", "customers.name", "customers.email"]
}
```

**Response (Clarification Required):**
```json
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

**Response (Rejected - Destructive Intent):**
```json
{
  "status": "rejected",
  "reason": "This application only supports read-only SELECT queries. Requests to update/modify data are not allowed.",
  "original_question": "Delete customer records"
}
```

---

#### `POST /clarify`

Submit a clarification answer to resolve an ambiguous question.

**Request Body:**
```json
{
  "original_question": "Show me the best customer.",
  "user_answer": "The customer with the highest total revenue"
}
```

**Response:**
```json
{
  "status": "sql_generated",
  "original_question": "Show me the best customer.",
  "user_answer": "The customer with the highest total revenue",
  "final_question": "Show the customer with the highest total revenue.",
  "sql": "SELECT c.name, SUM(o.amount) AS total_revenue FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.id, c.name ORDER BY total_revenue DESC LIMIT 1;",
  "retrieved_schema": ["customers.name", "orders.amount", "orders.customer_id"]
}
```

---

#### `POST /execute`

Execute a validated SQL SELECT query.

**Request Body:**
```json
{
  "sql": "SELECT COUNT(*) AS total_customers FROM customers;"
}
```

**Response:**
```json
{
  "status": "success",
  "columns": ["total_customers"],
  "rows": [[10]]
}
```

**Error Response (Non-SELECT):**
```json
{
  "detail": "Only SELECT queries are allowed."
}
```

---

#### `GET /health`

Check API and database health.

**Response:**
```json
{
  "status": "ok",
  "database": "connected",
  "model": "openai/gpt-oss-20b"
}
```

---

#### `GET /schema`

Get database schema metadata (tables, columns, data types).

**Response:**
```json
{
  "tables": [
    {
      "name": "customers",
      "columns": [
        {"name": "id", "data_type": "INTEGER", "description": "Primary key"},
        {"name": "name", "data_type": "TEXT", "description": "Customer full name"},
        {"name": "email", "data_type": "TEXT", "description": "Unique email address"},
        {"name": "city", "data_type": "TEXT", "description": "Customer city"},
        {"name": "signup_date", "data_type": "DATE", "description": "Account creation date"}
      ]
    },
    {
      "name": "products",
      "columns": [
        {"name": "id", "data_type": "INTEGER", "description": "Primary key"},
        {"name": "name", "data_type": "TEXT", "description": "Product name"},
        {"name": "category", "data_type": "TEXT", "description": "Product category"},
        {"name": "price", "data_type": "NUMERIC", "description": "Product price"}
      ]
    },
    {
      "name": "orders",
      "columns": [
        {"name": "id", "data_type": "INTEGER", "description": "Primary key"},
        {"name": "customer_id", "data_type": "INTEGER", "description": "Foreign key to customers"},
        {"name": "product_id", "data_type": "INTEGER", "description": "Foreign key to products"},
        {"name": "order_date", "data_type": "DATE", "description": "Order creation date"},
        {"name": "quantity", "data_type": "INTEGER", "description": "Number of units ordered"},
        {"name": "amount", "data_type": "NUMERIC", "description": "Total order value"}
      ]
    }
  ]
}
```

---

## 💡 Example Usage

### Simple Queries

```text
"How many customers do we have?"
→ SELECT COUNT(*) AS total_customers FROM customers;

"Show me all products."
→ SELECT * FROM products;

"What is the total revenue?"
→ SELECT SUM(amount) AS total_revenue FROM orders;

"List customers from Pune."
→ SELECT name, email FROM customers WHERE city = 'Pune';
```

### Aggregation Queries

```text
"Show the top 5 customers by revenue."
→ SELECT c.name, SUM(o.amount) AS total_revenue
  FROM customers c
  JOIN orders o ON c.id = o.customer_id
  GROUP BY c.id, c.name
  ORDER BY total_revenue DESC
  LIMIT 5;

"Which products sold the most?"
→ SELECT p.name, SUM(o.quantity) AS total_sold
  FROM products p
  JOIN orders o ON p.id = o.product_id
  GROUP BY p.id, p.name
  ORDER BY total_sold DESC;

"What is the total revenue by city?"
→ SELECT c.city, SUM(o.amount) AS city_revenue
  FROM customers c
  JOIN orders o ON c.id = o.customer_id
  GROUP BY c.city
  ORDER BY city_revenue DESC;
```

### Ambiguous Queries (Triggers Clarification)

```text
"Show me the best customer."
↓
❓ What do you mean by 'best'?
   • The customer with the highest total revenue
   • The customer with the most orders

"Which products generated the most sales?"
↓
❓ What do you mean by 'most sales'?
   • Highest total revenue
   • Most units sold
```

### Rejected Queries (Security)

```text
"Delete all customers"
→ ❌ Rejected: This application only supports read-only SELECT queries.

"UPDATE customers SET city = 'Mumbai'"
→ ❌ Rejected: Requests to update/modify data are not allowed.

"DROP TABLE orders"
→ ❌ Rejected: Requests to drop data are not allowed.
```

---

## 🧪 Testing

### Backend Tests (Python)

Run the full test suite (393 tests):

```bash
python -m pytest -v
```

**Quiet mode (summary only):**
```bash
python -m pytest -q
```

**Run specific test file:**
```bash
python -m pytest test/test_intent_validator.py -v
```

**Run with coverage report:**
```bash
python -m pytest --cov=backend --cov-report=html
```

### Test Categories

| Test Suite | Tests | Coverage |
|-----------|-------|----------|
| `test_intent_validator.py` | 66 | Destructive intent detection |
| `test_sql_validator.py` | 53 | SQL validation and security |
| `test_production_errors.py` | 78 | Regression tests for production bugs |
| `test_remaining_security_bug.py` | 33 | SQL syntax detection edge cases |
| `test_clarification.py` | 24 | LLM clarification engine |
| `test_orchestrator.py` | 12 | Pipeline coordination |
| `test_hybrid_search.py` | 18 | RAG retrieval accuracy |
| Other tests | 109 | Database, API endpoints, etc. |
| **Total** | **393** | **Comprehensive coverage** |

### Frontend Tests (TypeScript)

Run Vitest unit tests:

```bash
cd frontend
npm run test
```

**Watch mode:**
```bash
npm run test:watch
```

**UI mode:**
```bash
npx vitest --ui
```

### Type Checking

```bash
cd frontend
npx tsc --noEmit
```

### Build Verification

```bash
cd frontend
npm run build
```

Expected output:
```
✓ built in 11.03s
dist/assets/index-C2Mc4w-I.js   725.50 kB │ gzip: 210.59 kB
```

---

## 🔒 Security Considerations

### Implemented Security Measures

| Layer | Protection | Implementation |
|-------|-----------|----------------|
| **Intent Validation** | Detects destructive requests before processing | Regex patterns for UPDATE, DELETE, INSERT, DROP, etc. |
| **SQL Syntax Detection** | Catches SQL statements in natural language | Patterns like `UPDATE...SET`, `DELETE FROM`, `INSERT INTO` |
| **Clarification Validation** | Re-validates resolved questions | Checks both original + clarified questions |
| **SQL Validator** | Final mandatory security layer | Blocks non-SELECT statements + dangerous functions |
| **Read-Only Enforcement** | Database permissions | Application enforces SELECT-only; no write operations |
| **API Key Isolation** | Server-side only | GROQ_API_KEY never sent to browser or stored in localStorage |
| **Input Sanitization** | SQLAlchemy parameterized queries | Prevents SQL injection |
| **Rate Limiting** | Per-IP throttling | 20/min for LLM endpoints, 60/min for queries |
| **Error Sanitization** | Generic error messages | No internal stack traces or implementation details exposed |
| **CORS** | Explicit origin whitelist | No wildcard origins; environment-configured |

### Security Layers

```
User Input
    ↓
[Intent Validator]      ← Blocks destructive natural language
    ↓
[Clarification Engine]  ← Re-validates resolved questions
    ↓
[SQL Generator]         ← Validates output starts with SELECT
    ↓
[SQL Validator]         ← Final enforcement: SELECT-only + keyword block
    ↓
[Database Executor]     ← Parameterized queries via SQLAlchemy
    ↓
PostgreSQL (Read-Only)
```

### Known Limitations & Recommendations

| Issue | Current Status | Recommended Improvement |
|-------|----------------|------------------------|
| **Authentication** | ❌ Not implemented | Add user login, session management, JWT tokens |
| **Authorization** | ❌ Not implemented | Row-level security, multi-tenancy |
| **Query History Privacy** | ⚠️ localStorage (device-local only) | Server-side session storage with encryption |
| **Rate Limiting** | ✅ IP-based (basic) | User-based limits, quota tracking |
| **Audit Logging** | ❌ Not implemented | Log all queries, IP addresses, timestamps |
| **SSL/TLS** | ⚠️ Not enforced | Require HTTPS in production |
| **Database Backups** | ⚠️ Manual | Automated backups with point-in-time recovery |
| **Secrets Management** | ⚠️ `.env` file | Use secrets manager (AWS Secrets, HashiCorp Vault) |

### Deployment Checklist

Before deploying to production:

- [ ] Enable SSL/TLS (HTTPS only)
- [ ] Use strong PostgreSQL passwords
- [ ] Set `DATABASE_URL` with `?sslmode=require` for cloud databases
- [ ] Rotate API keys regularly
- [ ] Configure proper CORS origins (no `*` wildcard)
- [ ] Enable PostgreSQL connection pooling
- [ ] Set up database backups
- [ ] Monitor rate limit exhaustion
- [ ] Implement logging and alerting
- [ ] Add user authentication
- [ ] Review and test all security layers

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. Database Connection Error

**Error:**
```
ValueError: DATABASE_URL is not set.
```

**Solution:**
- Verify `.env` file exists in project root
- Check `DATABASE_URL` format: `postgresql://user:pass@host:port/dbname`
- Test PostgreSQL connection: `psql -U postgres -d text_to_sql_ai`

---

#### 2. Groq API Key Error

**Error:**
```
ValueError: GROQ_API_KEY is not set.
```

**Solution:**
- Get API key from [console.groq.com](https://console.groq.com/)
- Add to `.env`: `GROQ_API_KEY=your_key_here`
- Restart the server

---

#### 3. Module Import Error

**Error:**
```
ModuleNotFoundError: No module named 'backend'
```

**Solution:**
- Activate virtual environment first
- Ensure you're in project root directory
- Reinstall dependencies: `pip install -r requirements.txt`

---

#### 4. PyTorch CPU Version Error

**Error:**
```
ERROR: Could not find a version that satisfies the requirement torch==2.2.2+cpu
```

**Solution:**
Install PyTorch separately before requirements.txt:
```bash
pip install torch==2.2.2+cpu --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

---

#### 5. Frontend Build Failure

**Error:**
```
npm ERR! code ENOENT
```

**Solution:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

---

#### 6. Port Already in Use

**Error:**
```
ERROR: [Errno 48] Address already in use
```

**Solution:**
- Kill existing process on port 8000:
  ```bash
  # Windows
  netstat -ano | findstr :8000
  taskkill /PID <PID> /F
  
  # macOS/Linux
  lsof -ti:8000 | xargs kill -9
  ```
- Or use a different port:
  ```bash
  uvicorn backend.main:app --port 8001
  ```

---

#### 7. Empty Database

**Error:**
```
Query execution failed. Check your SQL and try again.
```

**Solution:**
Run database setup:
```bash
python -m backend.database.setup
```

Verify data exists:
```bash
psql -U postgres -d text_to_sql_ai -c "SELECT COUNT(*) FROM customers;"
```

---

#### 8. CORS Error in Browser

**Error:**
```
Access to fetch at 'http://127.0.0.1:8000/ask' from origin 'http://localhost:5173' has been blocked by CORS policy
```

**Solution:**
- Add frontend URL to `.env`:
  ```env
  CORS_ORIGINS=http://localhost:5173
  ```
- Restart backend server

---

### Debug Mode

Enable detailed logging:

```bash
# Backend
export LOG_LEVEL=DEBUG  # macOS/Linux
set LOG_LEVEL=DEBUG     # Windows

python -m uvicorn backend.main:app --log-level debug
```

---

## 🚀 Future Enhancements

### Planned Features (Not Yet Implemented)

| Feature | Status | Priority | Description |
|---------|--------|----------|-------------|
| **User Authentication** | 📋 Planned | High | Login/signup, JWT tokens, session management |
| **Multi-User Support** | 📋 Planned | High | Isolated query history per user |
| **Database Connections** | 📋 Planned | Medium | Connect to custom PostgreSQL databases |
| **Query History Sync** | 📋 Planned | Medium | Server-side storage with cloud sync |
| **Advanced Charts** | 📋 Planned | Medium | Scatter plots, heatmaps, geographic maps |
| **Query Optimization** | 📋 Planned | Medium | EXPLAIN ANALYZE, index suggestions |
| **Export Results** | 📋 Planned | Low | CSV, Excel, JSON export |
| **Natural Language Results** | 📋 Planned | Low | LLM-generated summaries of query results |
| **Query Templates** | 📋 Planned | Low | Save and reuse common queries |
| **Collaborative Features** | 📋 Planned | Low | Share queries, team workspaces |

### Technical Improvements

- [ ] Upgrade to streaming LLM responses for faster interactivity
- [ ] Implement connection pooling for PostgreSQL
- [ ] Add Redis caching for frequently accessed schema metadata
- [ ] Optimize bundle size (code splitting, lazy loading)
- [ ] Add end-to-end tests with Playwright
- [ ] Implement GraphQL API option
- [ ] Add WebSocket support for real-time updates
- [ ] Containerize with Docker + Docker Compose
- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Deploy to cloud (AWS, GCP, Azure, Render, Railway)

---

## 👨‍💻 Author

**Omkar Sitaram Waghmare**

- **Branch**: Computer Engineering
- **College**: MIT Academy of Engineering, Pune
- **Achievement**: Smart India Hackathon 2025 - National Winner 🏆
- **GitHub**: [@Omkar023-coder](https://github.com/Omkar023-coder)
- **LinkedIn**: [Omkar Waghmare](https://www.linkedin.com/in/omkar-waghmare-7b3ba827b/)

---

## 📄 License

This project is for **educational and portfolio purposes**. Feel free to use it as a reference for learning or building your own projects.

---

## 🙏 Acknowledgments

- **Groq** for providing fast and free LLM inference
- **FastAPI** for the excellent web framework
- **sentence-transformers** for semantic embeddings
- **Recharts** for beautiful data visualizations
- **Radix UI** for accessible components
- **PostgreSQL** for reliable database performance

---

<div align="center">

**⭐ If you found this project helpful, please consider giving it a star!**

[Report Bug](https://github.com/Omkar023-coder/text-to-sql-ai/issues) · [Request Feature](https://github.com/Omkar023-coder/text-to-sql-ai/issues)

Made with ❤️ by Omkar Waghmare

</div>
