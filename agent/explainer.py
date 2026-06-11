"""
explainer.py — Uses Groq to explain a SQL query in plain English.
"""

from groq import Groq

EXPLAIN_SYSTEM = "You are a helpful assistant that explains SQL queries in simple plain English."

EXPLAIN_PROMPT_TEMPLATE = (
    "Explain this SQL query in simple plain English in 2-3 sentences. "
    "No technical jargon:\n\n{sql}"
)

MODEL_ID = "llama-3.3-70b-versatile"


def explain_sql(sql: str, api_key: str) -> str:
    """Return a plain-English explanation of the SQL query."""
    try:
        client   = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": EXPLAIN_SYSTEM},
                {"role": "user",   "content": EXPLAIN_PROMPT_TEMPLATE.format(sql=sql)},
            ],
            temperature=0.2,
            max_tokens=256,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        return f"(Explanation unavailable: {exc})"
