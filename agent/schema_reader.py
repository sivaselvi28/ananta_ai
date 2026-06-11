"""
schema_reader.py — Reads SQLite table schema and returns a formatted string
including column definitions AND foreign key relationships so the LLM
can generate correct JOIN queries.
"""

import sqlite3


def get_schema(db_path: str) -> str:
    """
    Connect to the SQLite DB and return a formatted schema string that includes:
      - All tables with column names + types
      - Foreign key relationships (for JOIN awareness)

    Example output:
        TABLE employees: id INTEGER, name TEXT, department TEXT, salary REAL, hire_date TEXT, city TEXT
        TABLE sales: id INTEGER, employee_id INTEGER, product TEXT, amount REAL, sale_date TEXT, region TEXT
        TABLE departments: id INTEGER, name TEXT, budget REAL, manager_id INTEGER

        RELATIONSHIPS (Foreign Keys):
        sales.employee_id → employees.id
    """
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()

    # All user-created tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cur.fetchall()]

    schema_parts = []
    fk_lines     = []

    for table in tables:
        # Column definitions
        cur.execute(f"PRAGMA table_info({table})")
        columns = cur.fetchall()
        col_defs = ", ".join(
            f"{col[1]} {col[2] if col[2] else 'TEXT'}"
            for col in columns
        )
        schema_parts.append(f"TABLE {table}: {col_defs}")

        # Foreign key relationships
        cur.execute(f"PRAGMA foreign_key_list({table})")
        fks = cur.fetchall()
        for fk in fks:
            # fk: (id, seq, table, from, to, on_update, on_delete, match)
            fk_lines.append(f"  {table}.{fk[3]} → {fk[2]}.{fk[4]}")

    conn.close()

    result = "\n".join(schema_parts)

    if fk_lines:
        result += "\n\nRELATIONSHIPS (Foreign Keys):\n" + "\n".join(fk_lines)

    # Always append the full join guide (covers implicit text-based joins too)
    result += (
        "\n\nJOIN GUIDE:"
        "\n  sales.employee_id → employees.id           (INNER JOIN sales s ON s.employee_id = e.id)"
        "\n  employees.department → departments.name    (INNER JOIN departments d ON e.department = d.name)"
        "\n  departments.manager_id → employees.id      (JOIN employees e ON d.manager_id = e.id)"
    )

    return result
