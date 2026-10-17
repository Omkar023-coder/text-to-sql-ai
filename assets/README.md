# Assets Folder

This folder contains visual assets for the README documentation.

## Required Images

### 1. demo.png
**Purpose**: Overview screenshot of the running Text-to-SQL AI application

**Recommended content**:
- Show the three-panel interface (Sidebar, Chat Panel, Data Panel)
- Include a sample conversation with results
- Display results table with data
- Show the full application window

**Recommended dimensions**: 1920x1080 or 1600x900

**Status**: ⚠️ **You need to capture this**

---

### 2. success-query.png
**Purpose**: Example of a successful query with green success indicator

**Recommended content**:
- User question: "What is the total revenue?" or similar
- Green checkmark success indicator
- Generated SQL displayed
- Schema context shown (e.g., "orders.amount")
- Results table with data
- Execution time displayed
- "Query executed successfully" message in green

**Recommended dimensions**: 1600x900

**How to capture**:
1. Run: `python -m uvicorn backend.main:app`
2. Open: `http://127.0.0.1:8000`
3. Ask: "What is the total revenue?"
4. Wait for results to display
5. Take screenshot showing the complete response
6. Save as `success-query.png`

**Status**: ⚠️ **You need to capture this**

---

### 3. clarification-query.png
**Purpose**: Example of an ambiguous query requiring clarification

**Recommended content**:
- User question: "Show me the best customers." or similar ambiguous query
- Yellow/orange clarification card displayed
- Question: "What metric defines 'best' for customers?"
- Multiple suggestion chips visible:
  - "Customers with highest total revenue"
  - "Customers with most orders"
  - "Customers with highest average order amount"
- "Or type your own" input field
- No SQL generated yet (still in clarification phase)

**Recommended dimensions**: 1600x900

**How to capture**:
1. Run: `python -m uvicorn backend.main:app`
2. Open: `http://127.0.0.1:8000`
3. Ask: "Show me the best customers."
4. Wait for clarification card to appear
5. **Do NOT click any suggestion yet** - capture the clarification state
6. Take screenshot showing the full clarification card
7. Save as `clarification-query.png`

**Status**: ⚠️ **You need to capture this**

---

### 4. rejected-query.png
**Purpose**: Example of a rejected destructive query with red error indicator

**Recommended content**:
- User input: "INSERT INTO customers (name) VALUES ('Omkar');" or similar destructive request
- Red error card displayed
- Error icon (⚠️ triangle or 🔴 circle)
- Message: "Something went wrong"
- Explanation: "This application only supports read-only SELECT queries. Requests to insert/add data are not allowed."
- "Try again" button visible
- No SQL generated or executed

**Recommended dimensions**: 1600x900

**How to capture**:
1. Run: `python -m uvicorn backend.main:app`
2. Open: `http://127.0.0.1:8000`
3. Type or ask: "INSERT INTO customers (name) VALUES ('Omkar');"
4. Wait for rejection error to display
5. Take screenshot showing the complete error response
6. Save as `rejected-query.png`

**Status**: ⚠️ **You need to capture this**

---

### 5. architecture.png ✅ PROVIDED
**Purpose**: System architecture diagram

**Status**: ✅ **Image provided by user - save it as `architecture.png`**

**How to save**:
1. The architecture diagram image has been provided
2. Save the image you shared as `architecture.png` in this folder
3. The image shows the complete flow:
   - User → Intent Classifier → Query Planner → Schema Retriever → Groq LLM
   - Intent validation (safe/unsafe checks)
   - Clarification flow for ambiguous queries
   - SQL Validator (SELECT-only enforcement)
   - Query Executor (SQLAlchemy) → PostgreSQL
   - Response formatting and result display

**Current image includes**:
- ✅ Intent Classifier & Safety Check (detects INSERT, UPDATE, DELETE, DROP)
- ✅ Query Planner (understands question, identifies tables/columns)
- ✅ Schema Retriever (fetches PostgreSQL schema context)
- ✅ Groq LLM (SQL Generator with retry mechanism)
- ✅ Clarification flow for ambiguous queries
- ✅ SQL Validator (yellow diamond - validates SELECT queries)
- ✅ Query Executor (SQLAlchemy)
- ✅ PostgreSQL Database (Render/Local)
- ✅ Response Generator with result formatting
- ✅ Error handling paths (red boxes)

This diagram perfectly represents your actual system architecture!

---

## Current Status

- [ ] `demo.png` - **Not yet added** (overview screenshot)
- [ ] `success-query.png` - **Not yet added** (green success response)
- [ ] `clarification-query.png` - **Not yet added** (yellow clarification card)
- [ ] `rejected-query.png` - **Not yet added** (red error response)
- [x] `architecture.png` - **✅ PROVIDED** (save the shared image as this filename)

---

## Quick Capture Guide

Run the application and capture all query types in one session:

```bash
# 1. Start the application
python -m uvicorn backend.main:app

# 2. Open browser
http://127.0.0.1:8000

# 3. Capture each scenario:

# Scenario 1: Success Query
Ask: "What is the total revenue?"
Wait for green success → Screenshot → Save as success-query.png

# Scenario 2: Clarification Query  
Ask: "Show me the best customers."
Wait for yellow clarification card → Screenshot → Save as clarification-query.png

# Scenario 3: Rejected Query
Type: "INSERT INTO customers (name) VALUES ('Test');"
Wait for red error → Screenshot → Save as rejected-query.png

# Scenario 4: Overview Demo
Navigate through the interface → Show all panels → Save as demo.png
```

---

## Image Guidelines

**Format**: PNG (preferred) or JPG
**Quality**: High resolution, clear text
**Aspect ratio**: 16:9 recommended
**File size**: Keep under 2MB per image for faster README loading
**Editing**: Optional - Add borders, drop shadows, or annotations if desired

Once you add these images, they will automatically appear in the main README.md file.
