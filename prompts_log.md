# Prompts Log — NL → SQL Agent

All key prompts used by the Gemini API are documented here.
Each entry shows the purpose, the exact template, and notes on usage.

---

## Prompt 1 — SQL Generation

**Purpose:** Convert a natural language question into a valid SQLite SELECT query.

**Module:** `agent/sql_generator.py → generate_sql()`

**System Instruction (sent as system_instruction to GenerativeModel):**
```
You are an expert SQL generator for SQLite.
Given the database schema and a natural language question,
generate ONLY a valid SQLite SELECT query.
Return ONLY the SQL query, no explanation, no markdown, no backticks.
```

**User Prompt Template:**
```
Schema:
{schema}

Question: {user_question}

SQL Query:
```

**Variables:**
| Variable        | Source                         |
|-----------------|--------------------------------|
| `{schema}`      | `agent/schema_reader.get_schema()` |
| `{user_question}` | User input in Streamlit text area |

**Notes:**
- Model: `gemini-1.5-flash`
- Output is cleaned with `_clean_sql()` to strip any accidental markdown fences.
- Result is passed through `safety_check.is_safe()` before execution.

---

## Prompt 2 — SQL Explanation

**Purpose:** Explain the generated SQL query in plain English for non-technical users.

**Module:** `agent/explainer.py → explain_sql()`

**Prompt Template:**
```
Explain this SQL query in simple plain English in 2-3 sentences.
No technical jargon:

{sql}
```

**Variables:**
| Variable | Source                        |
|----------|-------------------------------|
| `{sql}`  | Final (possibly retried) SQL  |

**Notes:**
- Model: `gemini-1.5-flash`
- No system instruction; single user turn.
- Displayed in `st.info()` box alongside the SQL code block.
- Falls back to `"(Explanation unavailable: ...)"` on API error.

---

## Prompt 3 — Auto-Retry (SQL Fix)

**Purpose:** Automatically fix a SQL query that failed at execution time,
creating an agent-loop pattern: generate → execute → error → fix → re-execute.

**Module:** `agent/sql_generator.py → retry_sql()`

**Prompt Template:**
```
The following SQL query for SQLite failed with error: {error}

Failed SQL:
{failed_sql}

Schema:
{schema}

Original Question: {user_question}

Generate a corrected SQLite SELECT query.
Return ONLY the SQL, no explanation, no markdown, no backticks.
```

**Variables:**
| Variable          | Source                              |
|-------------------|-------------------------------------|
| `{error}`         | Exception message from `execute_query()` |
| `{failed_sql}`    | The SQL that caused the error       |
| `{schema}`        | `agent/schema_reader.get_schema()`  |
| `{user_question}` | Original user input                 |

**Notes:**
- Model: `gemini-1.5-flash`
- Triggered automatically when `execute_query()` returns a non-None error string.
- The corrected SQL is safety-checked again before re-execution.
- If the retry also fails, the user sees an error and is prompted to rephrase.

---

## Agent Loop Diagram

```
User Question
     │
     ▼
[Gemini: generate_sql()]
     │
     ▼
[safety_check()]  ──BLOCKED──▶  Show error, stop
     │ SAFE
     ▼
[execute_query()]
     │
  ERROR ──────────────────────────────────────────┐
     │                                             │
  SUCCESS                              [Gemini: retry_sql()]
     │                                             │
     ▼                                   [safety_check()]
  Show SQL + Explanation + Table + Chart           │
                                         [execute_query()]
                                             │         │
                                          SUCCESS    ERROR
                                             │         │
                                          Show      Show final
                                         results    error msg
```

---

*Last updated: auto-maintained by application.*
