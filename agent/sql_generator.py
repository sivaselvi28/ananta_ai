"""
sql_generator.py — ANANTA AI | Groq-powered SQL generator with agent loop.

Agent loop: generate → execute → error? → fix (up to MAX_ATTEMPTS) → success
Each retry passes the full error history so the model learns from prior mistakes.
"""

import re
from groq import Groq

MODEL_ID    = "llama-3.3-70b-versatile"
MAX_ATTEMPTS = 3   # initial attempt + 2 retries

SYSTEM_PROMPT = """You are an expert SQLite SQL generator for ANANTA AI.

RULES (strict):
- Return ONLY a valid SQLite SELECT query. Nothing else.
- No markdown, no backticks, no explanation, no comments.
- Use JOINs when the question involves multiple tables.
- JOIN conditions:
    sales      ↔ employees   → ON s.employee_id = e.id
    employees  ↔ departments → ON e.department = d.name
    departments↔ employees   → ON d.manager_id = e.id  (manager lookup)
- Always use short table aliases: e (employees), s (sales), d (departments).
- Qualify every column name with its alias when joining.
- Use INNER JOIN by default; LEFT JOIN when the user asks about "all" records.
- Use GROUP BY + aggregate functions (SUM, AVG, COUNT) for totals/averages.
- Use ORDER BY + LIMIT for "top N" questions.
"""

GENERATE_TEMPLATE = (
    "Database schema:\n{schema}\n\n"
    "Question: {question}\n\n"
    "SQLite SELECT query:"
)

# Each retry entry in the conversation carries the prior error so the model
# learns from its mistakes across multiple attempts.
RETRY_TEMPLATE = (
    "Attempt {attempt} failed.\n\n"
    "Your previous SQL:\n{failed_sql}\n\n"
    "SQLite error message:\n{error}\n\n"
    "Database schema:\n{schema}\n\n"
    "Original question: {question}\n\n"
    "Write a corrected SQLite SELECT query that avoids the above error.\n"
    "Return ONLY the SQL query — no explanation, no backticks, no markdown."
)


def _clean_sql(raw: str) -> str:
    raw = re.sub(r"```(?:sql)?", "", raw, flags=re.IGNORECASE)
    raw = raw.replace("```", "").strip()
    # strip any leading/trailing non-SQL words
    lines = [l for l in raw.splitlines() if l.strip()]
    return "\n".join(lines)


def _call(api_key: str, messages: list[dict]) -> str:
    client = Groq(api_key=api_key)
    resp = client.chat.completions.create(
        model=MODEL_ID,
        messages=messages,
        temperature=0.1,
        max_tokens=512,
    )
    return resp.choices[0].message.content


def generate_sql(user_question: str, schema: str, api_key: str) -> str:
    """First attempt: NL → SQL."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": GENERATE_TEMPLATE.format(
            schema=schema, question=user_question)},
    ]
    return _clean_sql(_call(api_key, messages))


def retry_sql(
    user_question: str,
    failed_sql: str,
    error: str,
    schema: str,
    api_key: str,
    attempt: int = 1,
    history: list[dict] | None = None,
) -> str:
    """
    Retry with full conversation history so the model sees all prior errors.

    `history` is the running list of {role, content} messages from this session.
    If provided, the retry prompt is appended to it (multi-turn context).
    """
    if history is None:
        history = [{"role": "system", "content": SYSTEM_PROMPT}]

    retry_msg = RETRY_TEMPLATE.format(
        attempt=attempt,
        failed_sql=failed_sql,
        error=error,
        schema=schema,
        question=user_question,
    )
    messages = history + [{"role": "user", "content": retry_msg}]
    return _clean_sql(_call(api_key, messages))
