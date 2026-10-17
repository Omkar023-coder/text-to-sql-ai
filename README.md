# 🗄️ Text-to-SQL AI

**Transform natural language questions into SQL queries and get instant results from your PostgreSQL database.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-316192?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)

> **Smart India Hackathon 2025 — National Winner** 🏆

---

## 📋 Project Overview

Text-to-SQL AI is an intelligent system that allows users to query a **PostgreSQL database** using natural language. Instead of writing SQL, users simply ask questions in plain English, and the application generates, validates, and executes SQL queries automatically.

**Problem it solves:**  
Non-technical users often need data from databases but don't know SQL. This application bridges that gap by converting natural language into safe, read-only SQL queries.

**Key highlights:**
- **Schema-aware clarification** — Asks for clarification when questions are ambiguous (e.g., "best customer")
- **RAG-powered SQL generation** — Retrieves relevant schema before generating SQL
- **Multi-layer security** — Blocks destructive queries (UPDATE, DELETE, DROP) at every stage
- **Professional React UI** — Three-panel interface with chat, SQL editor, and data visualization
- **Production-ready** — 393 passing tests, rate limiting, error handling

---

## 🖼️ Demo



---

### ✅ Successful Query

When a question is clear, SQL is generated and executed directly:

![Successful Query]![alt text](image.png)

**Example:** "What is the total revenue?"  
**Result:** Green success indicator, SQL displayed, results in table format

---

### ❓ Ambiguous Query — Clarification Required

When terms are unclear, the system asks for clarification:

![Clarification Query]![alt text](image-1.png)
![alt text](image-2.png)

**Example:** "Show me the best customers."  
**Response:** Yellow clarification card with suggestion chips:
- "Customers with highest total revenue"
- "Customers with most orders"
- "Customers with highest average order amount"

---

### ❌ Unsafe Query — Rejected

Destructive operations are blocked immediately:

![Rejected Query]![alt text](image-3.png)
![alt text](image-4.png)

**Example:** "DELETE FROM customers WHERE city = 'Pune';"  
**Response:** Red error indicator with security message rejecting the operation

---

## 🏗️ System Architecture

![System Architecture](assets/architecture.png)

**Workflow:**

1. **User submits question** → FastAPI endpoint receives natural language input
2. **Intent validation** → Regex patterns detect destructive requests (UPDATE, DELETE, etc.)
3. **RAG schema retrieval** → Hybrid search finds relevant columns using semantic + keyword matching
4. **Clarification check** → LLM judges if question is ambiguous
   - **Ambiguous?** → Return clarification suggestions
   - **Clear?** → Proceed to SQL generation
5. **SQL generation** → Groq LLM generates PostgreSQL query using retrieved schema
6. **SQL validation** → Final security check ensures SELECT-only
7. **Query execution** → SQLAlchemy executes against PostgreSQL
8. **Results returned** → JSON response with columns and rows

---

## ✨ Key Features

- **Natural language to SQL** — Powered by Groq's `openai/gpt-oss-20b` model
- **RAG-based schema retrieval** — Uses sentence-transformers (`all-MiniLM-L6-v2`) for semantic search
- **Hybrid search** — Combines semantic embeddings, keyword matching, and metadata filtering (RRF fusion)
- **Schema-aware clarification** — LLM asks follow-up questions when needed
- **Multi-layer security** — Intent detection + SQL validation blocks all destructive operations
- **Read-only enforcement** — Blocks UPDATE, DELETE, INSERT, DROP, ALTER, TRUNCATE
- **Three-panel React UI** — Chat interface, SQL editor with syntax highlighting, data tables and charts
- **Interactive visualizations** — Auto-generates bar charts, line charts, and pie charts using Recharts
- **Persistent history** — localStorage saves conversations and allows session management
- **Schema explorer** — Browse tables, columns, and data types in sidebar
- **Rate limiting** — Protects API endpoints (configurable per endpoint)
- **Health monitoring** — Real-time database connection status
- **Comprehensive testing** — 393 passing tests covering security, SQL generation, and API endpoints

---

## 🛠️ Tech Stack

**Backend:**
- **Python 3.11+** — Backend language
- **FastAPI 0.111.0** — Web framework
- **Uvicorn 0.29.0** — ASGI server
- **PostgreSQL 16+** — Database (via psycopg2-binary 2.9.9)
- **SQLAlchemy 2.0.25** — ORM and query builder
- **Groq API (openai/gpt-oss-20b)** — LLM for SQL generation and clarification
- **sentence-transformers 3.0.0** — Semantic embeddings (`all-MiniLM-L6-v2`)
- **PyTorch 2.2.2+cpu** — Deep learning framework
- **slowapi 0.1.10** — Rate limiting

**Frontend:**
- **React 18.3.1** — UI library
- **TypeScript 5.6.3** — Type-safe JavaScript
- **Vite 5.4.11** — Build tool
- **Tailwind CSS 3.4.15** — Styling
- **Recharts 2.13.3** — Data visualization
- **Radix UI** — Accessible components
- **Lucide React 0.462.0** — Icons

**Testing:**
- **pytest 7.4.0** — Backend testing (393 tests)
- **Vitest 2.1.5** — Frontend unit testing
- **@testing-library/react 16.0.1** — React component testing

---

## 🔄 How It Works

### Step-by-Step Flow

1. **User enters question** — Natural language input (e.g., "Show me the top 5 customers by revenue")

2. **Intent validation** — Checks for destructive keywords in both natural language and SQL syntax
   - Rejected: "Delete all customers" → Status: `rejected`

3. **RAG schema retrieval** — Retrieves relevant columns using:
   - Semantic search (embeddings)
   - Keyword matching
   - Metadata filtering
   - Returns: `customers.name`, `orders.amount`, `orders.customer_id`

4. **Clarification check** — LLM analyzes question with schema context
   - **Clear** → Proceed to SQL generation
   - **Ambiguous** → Return clarification suggestions

5. **SQL generation** — Groq LLM generates PostgreSQL SELECT query

6. **SQL validation** — Final security layer:
   - Must start with SELECT
   - Blocks forbidden keywords (UPDATE, DELETE, DROP, etc.)
   - Prevents multi-statement queries
   - Blocks dangerous functions (`pg_sleep`, `generate_series`, etc.)

7. **Query execution** — SQLAlchemy executes validated query against PostgreSQL

8. **Frontend display** — Results rendered in table, charts auto-generated, conversation saved

---

## 📦 How to Run

### Prerequisites

| Requirement | Version | Download |
|------------|---------|----------|
| Python | 3.11+ | [python.org](https://www.python.org/downloads/) |
| PostgreSQL | 16+ | [postgresql.org](https://www.postgresql.org/download/) |
| Node.js | 20+ | [nodejs.org](https://nodejs.org/) |
| Groq API Key | Free tier | [console.groq.com](https://console.groq.com/) |

---

### 1. Clone Repository

```bash
git clone https://github.com/Omkar023-coder/text-to-sql-ai.git
cd text-to-sql-ai
```

---

### 2. Set Up Python Environment

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

---

### 3. Install Dependencies

```bash
# Install PyTorch CPU version first (required for sentence-transformers)
pip install torch==2.2.2+cpu --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
pip install -r requirements.txt
```

> **Note:** PyTorch must be installed from the PyTorch wheel index first to get the CPU-only build. Skipping this step will download the CUDA build (~2 GB).

---

### 4. Configure Environment Variables

**Windows:**
```bash
copy .env.example .env
```

**macOS/Linux:**
```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
# Get free API key at: https://console.groq.com
GROQ_API_KEY=your_groq_api_key_here

# PostgreSQL connection string
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/text_to_sql_ai

# CORS (use http://localhost:5173 for development)
CORS_ORIGINS=http://localhost:5173
```

---

### 5. Set Up PostgreSQL Database

#### Install PostgreSQL

**Windows:**
1. Download from [postgresql.org](https://www.postgresql.org/download/windows/)
2. Run installer (includes pgAdmin 4)
3. Remember the postgres password

**macOS:**
```bash
brew install postgresql@16
brew services start postgresql@16
```

**Linux:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

#### Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE text_to_sql_ai;

# Exit
\q
```

#### Initialize Schema and Seed Data

```bash
python -m backend.database.setup
```

**This creates:**
- `customers` table (10 sample customers)
- `products` table (5 sample products: Laptop, Mouse, Keyboard, Monitor, Headphones)
- `orders` table (12 sample orders)

**Verify:**
```bash
psql -U postgres -d text_to_sql_ai -c "SELECT COUNT(*) FROM customers;"
```
Expected output: `10`

---

### 6. Build Frontend (Production Mode)

```bash
cd frontend
npm install
npm run build
cd ..
```

---

### 7. Start the Application

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Open in browser:**
```
http://127.0.0.1:8000
```

The FastAPI server serves both the API and the React frontend.

---

### Development Mode (Optional)

For hot-reload during development:

**Terminal 1 — Backend:**
```bash
python -m uvicorn backend.main:app --reload
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

**Open:** `http://localhost:5173`

---

### Interactive API Docs

**Swagger UI:**  
`http://127.0.0.1:8000/docs`

**ReDoc:**  
`http://127.0.0.1:8000/redoc`

---

## 💬 Example Queries

Try these questions after running the application:

### Clear Questions (Direct SQL Generation)

```
"What is the total revenue?"
"Show me all customers from Pune"
"How many orders were placed in August 2026?"
"What is the average order amount?"
"Show me the top 5 products by quantity sold"
```

### Ambiguous Questions (Clarification Required)

```
"Show me the best customers"
→ Clarifies: "Best by revenue? By order count? By average order value?"

"Give me top products"
→ Clarifies: "Top by sales quantity? By revenue? By price?"
```

### Unsafe Questions (Rejected)

```
"DELETE FROM customers WHERE city = 'Pune'"
→ Rejected: Read-only SELECT queries only

"UPDATE products SET price = 10000 WHERE name = 'Laptop'"
→ Rejected: UPDATE not allowed

"DROP TABLE orders"
→ Rejected: DROP not allowed
```

---

## 🧪 Testing

Run the test suite:

```bash
pytest
```

**Test coverage:**
- 393 passing tests
- Security validation (66 tests)
- SQL validator (53 tests)
- Regression tests (78 tests)
- Integration tests (orchestrator, clarification, RAG)

---

## 👤 Author

**Omkar Sitaram Waghmare**  
Computer Engineering Student  
MIT Academy of Engineering, Pune

**Achievement:** Smart India Hackathon 2025 — National Winner 🏆

**LinkedIn:** [linkedin.com/in/omkar-waghmare-7b3ba827b](https://www.linkedin.com/in/omkar-waghmare-7b3ba827b/)

---

## 📄 License

This project is open-source and available for educational and portfolio purposes.der_date", "data_type": "DATE", "description": "Order creation date"},
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
