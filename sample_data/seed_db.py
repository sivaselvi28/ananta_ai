"""
seed_db.py — Creates and seeds the company.db SQLite database.
Run once: python sample_data/seed_db.py
"""

import sqlite3
import os
import random
from datetime import date, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "company.db")


def random_date(start_year=2018, end_year=2024) -> str:
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    return (start + timedelta(days=random.randint(0, delta))).isoformat()


def seed():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ── departments ─────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE departments (
            id         INTEGER PRIMARY KEY,
            name       TEXT    NOT NULL,
            budget     REAL    NOT NULL,
            manager_id INTEGER
        )
    """)

    departments = [
        (1, "Engineering",    1_500_000, 3),
        (2, "Sales",          800_000,   7),
        (3, "Marketing",      600_000,   12),
        (4, "HR",             400_000,   15),
        (5, "Finance",        700_000,   18),
        (6, "Operations",     550_000,   5),
        (7, "Product",        900_000,   9),
        (8, "Legal",          350_000,   20),
    ]
    cur.executemany("INSERT INTO departments VALUES (?,?,?,?)", departments)

    # ── employees ────────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE employees (
            id         INTEGER PRIMARY KEY,
            name       TEXT    NOT NULL,
            department TEXT    NOT NULL,
            salary     REAL    NOT NULL,
            hire_date  TEXT    NOT NULL,
            city       TEXT    NOT NULL
        )
    """)

    dept_names = [d[1] for d in departments]
    cities = ["New York", "San Francisco", "Austin", "Chicago",
              "Seattle", "Boston", "Denver", "Miami", "Atlanta", "Los Angeles"]
    first_names = ["Alice", "Bob", "Carol", "David", "Eva", "Frank",
                   "Grace", "Henry", "Irene", "Jack", "Karen", "Leo",
                   "Mia", "Nathan", "Olivia", "Paul", "Quinn", "Rachel",
                   "Steve", "Tina", "Uma", "Victor", "Wendy", "Xavier"]
    last_names  = ["Smith", "Johnson", "Williams", "Brown", "Jones",
                   "Garcia", "Miller", "Davis", "Wilson", "Moore",
                   "Taylor", "Anderson", "Thomas", "Jackson", "White"]

    employees = []
    random.seed(42)
    for i in range(1, 26):
        name  = f"{random.choice(first_names)} {random.choice(last_names)}"
        dept  = random.choice(dept_names)
        sal   = round(random.uniform(55_000, 180_000), 2)
        hdate = random_date(2018, 2023)
        city  = random.choice(cities)
        employees.append((i, name, dept, sal, hdate, city))

    cur.executemany("INSERT INTO employees VALUES (?,?,?,?,?,?)", employees)

    # ── sales ─────────────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE sales (
            id          INTEGER PRIMARY KEY,
            employee_id INTEGER NOT NULL,
            product     TEXT    NOT NULL,
            amount      REAL    NOT NULL,
            sale_date   TEXT    NOT NULL,
            region      TEXT    NOT NULL,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    """)

    products = ["Laptop", "Software License", "Cloud Subscription",
                "Consulting Package", "Support Plan", "Mobile Device",
                "Server Hardware", "Security Suite", "Analytics Tool"]
    regions  = ["North", "South", "East", "West", "Central"]

    sales = []
    for i in range(1, 51):
        emp_id  = random.randint(1, 25)
        product = random.choice(products)
        amount  = round(random.uniform(500, 50_000), 2)
        sdate   = random_date(2022, 2024)
        region  = random.choice(regions)
        sales.append((i, emp_id, product, amount, sdate, region))

    cur.executemany("INSERT INTO sales VALUES (?,?,?,?,?,?)", sales)

    conn.commit()
    conn.close()
    print(f"✅  Database seeded at: {DB_PATH}")
    print(f"   departments : {len(departments)} rows")
    print(f"   employees   : {len(employees)} rows")
    print(f"   sales       : {len(sales)} rows")


if __name__ == "__main__":
    seed()
