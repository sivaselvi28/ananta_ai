"""
safety_check.py — ANANTA AI read-only safety enforcement.

Two layers of protection:
  1. Intent check  — scans the USER'S QUESTION for destructive intent BEFORE
                     calling the AI. Catches cases like "delete student table"
                     where the AI might otherwise rewrite it as a SELECT.
  2. SQL check     — scans the GENERATED SQL for forbidden keywords AFTER the
                     AI produces output, as a second line of defence.
"""

import re

# ── Forbidden SQL keywords (used in both checks) ─────────────────────────────
BLOCKED_SQL_KEYWORDS = [
    "DROP", "DELETE", "INSERT", "UPDATE", "ALTER",
    "CREATE", "TRUNCATE", "REPLACE", "ATTACH", "DETACH",
    "PRAGMA", "VACUUM", "RENAME",
]

# ── Destructive intent phrases in natural language ────────────────────────────
# These catch what a user MEANS even before the AI touches the prompt.
DESTRUCTIVE_INTENT_PATTERNS = [
    # delete / remove / drop
    r"\bdelete\b", r"\bremove\b", r"\bdrop\b", r"\berase\b", r"\bwipe\b",
    r"\bpurge\b", r"\bclear\b",
    # modify / change / update
    r"\bupdate\b", r"\bmodify\b", r"\bchange\b.*\b(record|row|data|value)\b",
    r"\bedit\b.*\b(record|row|data)\b", r"\bset\b.*\b(column|field|value)\b",
    # insert / add new rows
    r"\binsert\b", r"\badd\b.*\b(row|record|entry|data)\b",
    r"\bcreate\b.*\b(record|row|entry)\b",
    # schema changes
    r"\balter\b", r"\brename\b.*\b(table|column)\b",
    r"\bcreate\b.*\btable\b", r"\bdrop\b.*\btable\b",
    r"\btruncate\b",
]

_INTENT_RE = re.compile(
    "|".join(DESTRUCTIVE_INTENT_PATTERNS),
    flags=re.IGNORECASE,
)


def check_question_intent(user_question: str) -> tuple[bool, str]:
    """
    Layer 1 — scan the USER'S NATURAL LANGUAGE QUESTION for destructive intent.
    Called BEFORE the AI generates any SQL.

    Returns (True, "SAFE") if the question looks like a read/query request.
    Returns (False, reason) if the question asks to delete/modify/drop/etc.
    """
    match = _INTENT_RE.search(user_question.strip())
    if match:
        word = match.group(0)
        return False, (
            f"Request blocked: your question appears to ask for a destructive "
            f"operation (detected: '{word}'). "
            "ANANTA AI operates in read-only mode — only data retrieval "
            "questions are allowed (e.g. 'Show...', 'List...', 'What is...')."
        )
    return True, "SAFE"


def is_safe(sql: str) -> tuple[bool, str]:
    """
    Layer 2 — scan the GENERATED SQL for forbidden keywords.
    Called AFTER the AI produces a query, as a second line of defence.

    Returns (True, "SAFE") for SELECT-only queries.
    Returns (False, reason) for anything else.
    """
    cleaned = sql.strip().upper()

    # Strip SQL comments before checking
    cleaned = re.sub(r"--[^\n]*", "", cleaned)
    cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
    cleaned = cleaned.strip()

    for keyword in BLOCKED_SQL_KEYWORDS:
        pattern = rf"\b{keyword}\b"
        if re.search(pattern, cleaned):
            return False, (
                f"SQL blocked: generated query contains forbidden keyword "
                f"'{keyword}'. Only SELECT statements are allowed."
            )

    if not cleaned.startswith("SELECT"):
        return False, (
            "SQL blocked: only SELECT statements are permitted. "
            f"Query starts with: '{cleaned[:40]}'"
        )

    return True, "SAFE"
