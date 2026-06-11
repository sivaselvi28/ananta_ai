"""
app.py — ANANTA AI | NL → SQL Agent
Run with: streamlit run app.py
"""

import os
import io
import json
import streamlit as st
from dotenv import load_dotenv

from agent.schema_reader import get_schema
from agent.sql_generator import generate_sql, retry_sql, MAX_ATTEMPTS
from agent.safety_check import is_safe, check_question_intent
from agent.query_executor import execute_query
from agent.explainer import explain_sql
from agent.chart_generator import auto_chart

load_dotenv()
DEFAULT_DB = os.path.join(os.path.dirname(__file__), "sample_data", "company.db")

st.set_page_config(
    page_title="ANANTA AI — NL to SQL",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
#  CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Inter:wght@400;500;600;700&display=swap');

/* ── Base ── */
html, body, [data-testid="stAppViewContainer"] {
    background: radial-gradient(ellipse at 20% 20%, #0a0f1e 0%, #050810 60%, #0a0518 100%) !important;
    font-family: 'Inter', sans-serif;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#07101a 0%,#050810 100%) !important;
    border-right: 1px solid #0d2137 !important;
}

/* ── Top brand bar ── */
.brand-bar {
    background: linear-gradient(90deg, #0a0f1e, #0d1f35, #0a0f1e);
    border-bottom: 2px solid transparent;
    border-image: linear-gradient(90deg, #00d4ff, #7b2ff7, #ff6b35, #00e676) 1;
    padding: 14px 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: -1rem -1rem 0 -1rem;
}
.brand-name {
    font-family: 'Orbitron', monospace;
    font-size: 1.6rem;
    font-weight: 900;
    background: linear-gradient(90deg, #00d4ff 0%, #7b2ff7 40%, #ff6b35 70%, #00e676 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 3px;
    text-shadow: none;
}
.brand-tagline {
    font-size: 0.72rem;
    color: #445577;
    letter-spacing: 2px;
    text-transform: uppercase;
    font-weight: 600;
}
.brand-badge {
    background: linear-gradient(90deg,#7b2ff722,#00d4ff22);
    border: 1px solid #7b2ff755;
    border-radius: 20px;
    padding: 5px 14px;
    font-size: 0.72rem;
    color: #00d4ff;
    font-weight: 700;
    letter-spacing: 1px;
}

/* ── Hero ── */
.hero-wrap {
    text-align: center;
    padding: 28px 0 10px 0;
}
.hero-nl {
    font-family: 'Orbitron', monospace;
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: 4px;
    color: #445577;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.hero-title {
    font-family: 'Orbitron', monospace;
    font-size: 2.6rem;
    font-weight: 900;
    background: linear-gradient(90deg, #00d4ff, #7b2ff7, #ff6b35);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.2;
    margin-bottom: 8px;
}
.hero-sub {
    color: #6a7f9a;
    font-size: 1rem;
    font-weight: 500;
    margin-bottom: 0;
}
.hero-arrow {
    font-size: 1.4rem;
    background: linear-gradient(90deg,#00d4ff,#7b2ff7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 900;
}

/* ── Step cards ── */
.step-card {
    border-radius: 10px;
    padding: 12px 18px;
    margin: 6px 0;
    font-size: 0.9rem;
    font-weight: 600;
    display: flex;
    align-items: flex-start;
    gap: 12px;
    line-height: 1.5;
}
.step-pending  { background:#0a1220; color:#2a3a4a; border:1px solid #0d1a28; }
.step-running  { background:#041828; color:#00d4ff; border:1px solid #00d4ff44;
                 box-shadow:0 0 12px #00d4ff22; animation:glow 1.4s infinite; }
.step-done     { background:#041a0e; color:#00e676; border:1px solid #00e67644;
                 box-shadow:0 0 8px #00e67622; }
.step-error    { background:#1a0408; color:#ff5252; border:1px solid #ff525244;
                 box-shadow:0 0 8px #ff525222; }
.step-warn     { background:#1a0e04; color:#ffab40; border:1px solid #ffab4044; }
.step-icon  { font-size:1.1rem; flex-shrink:0; margin-top:1px; }
.step-body  { display:flex; flex-direction:column; gap:2px; }
.step-label { font-weight:700; }
.step-detail{ font-size:0.78rem; opacity:0.75; font-weight:400; }

@keyframes glow { 0%,100%{opacity:1;} 50%{opacity:0.55;} }

/* ── Block explanation card ── */
.block-card {
    background: linear-gradient(135deg,#1a0408,#200810);
    border: 1px solid #ff525455;
    border-left: 4px solid #ff5254;
    border-radius: 12px;
    padding: 20px 24px;
    margin: 14px 0;
    box-shadow: 0 0 24px #ff525422;
}
.block-title {
    font-family:'Orbitron',monospace;
    font-size:1rem;
    font-weight:700;
    color:#ff5254;
    letter-spacing:1px;
    margin-bottom:10px;
    display:flex; align-items:center; gap:8px;
}
.block-reason {
    color:#ffaaaa;
    font-size:0.9rem;
    font-weight:500;
    margin-bottom:12px;
    padding:10px 14px;
    background:#ff525410;
    border-radius:8px;
    border:1px solid #ff525422;
}
.block-explain {
    color:#cc8888;
    font-size:0.85rem;
    line-height:1.7;
}
.block-safe-hint {
    margin-top:12px;
    padding:10px 14px;
    background:#041a0e;
    border:1px solid #00e67633;
    border-radius:8px;
    color:#00e676;
    font-size:0.82rem;
    font-weight:600;
}

/* ── Result cards ── */
.r-card {
    background: linear-gradient(135deg,#07101a,#0a1525);
    border: 1px solid #0d2137;
    border-radius: 14px;
    padding: 16px 20px;
}
.r-card-blue   { border-top:3px solid #00d4ff; }
.r-card-purple { border-top:3px solid #7b2ff7; }
.r-card-green  { border-top:3px solid #00e676; }
.r-card-h {
    font-size:0.75rem;
    font-weight:700;
    text-transform:uppercase;
    letter-spacing:1.5px;
    margin-bottom:10px;
}
.h-blue  {color:#00d4ff;}
.h-purple{color:#bf7fff;}
.h-green {color:#00e676;}

/* ── Table title ── */
.table-title {
    font-family:'Orbitron',monospace;
    font-size:1rem;
    font-weight:700;
    color:#e0eaff;
    letter-spacing:1px;
    margin:0 0 8px 0;
    display:flex; align-items:center; gap:8px;
}
.tbl-badge {
    font-family:'Inter',sans-serif;
    font-size:0.72rem;
    font-weight:700;
    padding:2px 10px;
    border-radius:12px;
    background:#00d4ff22;
    border:1px solid #00d4ff44;
    color:#00d4ff;
    letter-spacing:0.5px;
}

/* ── Chips ── */
div[data-testid="stButton"] > button {
    border-radius:25px !important;
    font-size:0.75rem !important;
    font-weight:600 !important;
    padding:5px 12px !important;
    background:#07101a !important;
    border:1px solid #0d2137 !important;
    color:#6a8aaa !important;
    transition:all 0.2s !important;
}
div[data-testid="stButton"] > button:hover {
    background:linear-gradient(90deg,#00d4ff18,#7b2ff718) !important;
    border-color:#00d4ff66 !important;
    color:#cce8ff !important;
    transform:translateY(-1px) !important;
    box-shadow:0 4px 12px #00d4ff22 !important;
}
div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(90deg,#7b2ff7,#00d4ff) !important;
    border:none !important;
    color:#fff !important;
    font-size:0.95rem !important;
    font-weight:700 !important;
    padding:12px 32px !important;
    border-radius:30px !important;
    box-shadow:0 4px 24px #7b2ff766 !important;
    letter-spacing:0.5px !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
    box-shadow:0 6px 32px #00d4ffaa !important;
    transform:translateY(-2px) !important;
}

/* ── Input ── */
[data-testid="stTextArea"] textarea {
    background:#07101a !important;
    border:1px solid #0d2a3a !important;
    border-radius:12px !important;
    color:#c0d8f0 !important;
    font-size:0.95rem !important;
}
[data-testid="stTextArea"] textarea:focus {
    border-color:#00d4ff88 !important;
    box-shadow:0 0 0 2px #00d4ff22 !important;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
    background:#07101a;
    border:1px solid #0d2137;
    border-radius:10px;
    padding:12px 16px;
}
[data-testid="stMetricValue"] { color:#00d4ff !important; font-weight:700 !important; }

/* ── DataFrame ── */
[data-testid="stDataFrame"] {
    border-radius:12px !important;
    border:1px solid #0d2137 !important;
    overflow:hidden !important;
}

/* ── Section labels ── */
.sec-label {
    font-size:0.7rem;
    font-weight:700;
    text-transform:uppercase;
    letter-spacing:2px;
    color:#1e3a4a;
    margin:14px 0 6px 0;
}

/* ── Sidebar schema ── */
.schema-row {
    padding:4px 0;
    border-bottom:1px solid #0d1a28;
    margin-bottom:2px;
}

hr { border-color:#0d2137 !important; }

/* Scrollbar */
::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background:#050810; }
::-webkit-scrollbar-thumb { background:#0d2a3a; border-radius:3px; }
::-webkit-scrollbar-thumb:hover { background:#1e3a4a; }

/* ── Download panel ── */
.dl-panel {
    background: linear-gradient(135deg,#07101a,#0a1525);
    border: 1px solid #0d2137;
    border-top: 3px solid #00e676;
    border-radius: 14px;
    padding: 20px 24px;
    margin-top: 14px;
}
.dl-title {
    font-family:'Orbitron',monospace;
    font-size:0.85rem;
    font-weight:700;
    color:#00e676;
    letter-spacing:1px;
    margin-bottom:14px;
    display:flex; align-items:center; gap:8px;
}
.dl-format-grid {
    display:grid;
    grid-template-columns: repeat(4,1fr);
    gap:10px;
}
.dl-format-card {
    background:#041a0e;
    border:1px solid #00e67633;
    border-radius:10px;
    padding:12px 10px;
    text-align:center;
    cursor:pointer;
}
.dl-format-card:hover { border-color:#00e676; background:#07251a; }
.dl-fmt-icon  { font-size:1.6rem; margin-bottom:4px; }
.dl-fmt-name  { color:#00e676; font-weight:700; font-size:0.85rem; }
.dl-fmt-desc  { color:#2a4a3a; font-size:0.7rem; margin-top:2px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
for k, v in [("history", []), ("selected_example", ""), ("last_result", None),
             ("last_blocked", None)]:
    if k not in st.session_state:
        st.session_state[k] = v

schema_str = get_schema(DEFAULT_DB) if os.path.exists(DEFAULT_DB) else ""

# ─────────────────────────────────────────────────────────────────────────────
#  TOP BRAND BAR
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="brand-bar">
  <div>
    <div class="brand-name">✦ ANANTA AI</div>
    <div class="brand-tagline">Intelligence · Natural Language · Data</div>
  </div>
  <div class="brand-badge">⚡ NL → SQL CONVERTER</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:16px 4px 8px 4px;'>
      <div style='font-family:Orbitron,monospace;font-size:0.85rem;font-weight:700;
                  background:linear-gradient(90deg,#00d4ff,#7b2ff7);
                  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                  background-clip:text;letter-spacing:2px;'>✦ ANANTA AI</div>
      <div style='color:#1e3a4a;font-size:0.68rem;letter-spacing:1px;
                  text-transform:uppercase;margin-top:2px;'>NL to SQL Agent</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    # Schema
    st.markdown("<div class='sec-label'>📋 Database Schema</div>", unsafe_allow_html=True)
    with st.expander("3 Tables · company.db", expanded=True):
        if schema_str:
            table_colours = {
                "employees":   {"border": "#00d4ff", "bg": "#00d4ff18", "label": "#00d4ff"},
                "sales":       {"border": "#bf7fff", "bg": "#7b2ff718", "label": "#bf7fff"},
                "departments": {"border": "#00e676", "bg": "#00e67618", "label": "#00e676"},
            }

            # ── Parse schema into tables + join lines ─────────────────────────
            tables    = []   # list of (tname, cols_str)
            join_lines = []

            for line in schema_str.split("\n"):
                line = line.strip()
                if not line:
                    continue
                if line.startswith("TABLE"):
                    tname = line.split(":")[0].replace("TABLE", "").strip()
                    cols  = line.split(":", 1)[1].strip() if ":" in line else ""
                    tables.append((tname, cols))
                elif "→" in line or line.startswith("JOIN") or line.startswith("RELATIONSHIP") or line.startswith("sales.") or line.startswith("employees.") or line.startswith("departments."):
                    join_lines.append(line)

            # ── Render each table card ────────────────────────────────────────
            for tname, cols in tables:
                tc = table_colours.get(tname, {"border":"#ffab40","bg":"#ffab4018","label":"#ffab40"})

                # Build column pills
                col_pills = ""
                for col in cols.split(","):
                    col = col.strip()
                    if col:
                        parts = col.split()
                        cname = parts[0]
                        ctype = parts[1] if len(parts) > 1 else ""
                        col_pills += (
                            f"<span style='display:inline-block;margin:2px 3px;"
                            f"background:#0d1f2d;border:1px solid #1e3a4a;"
                            f"border-radius:5px;padding:1px 7px;font-size:0.67rem;'>"
                            f"<b style='color:#c8dff0;'>{cname}</b>"
                            f"<span style='color:#4a6a8a;'> {ctype}</span></span>"
                        )

                st.markdown(
                    f"<div style='background:{tc['bg']};border:1px solid {tc['border']}44;"
                    f"border-left:3px solid {tc['border']};border-radius:8px;"
                    f"padding:8px 10px;margin:6px 0;'>"
                    f"<div style='color:{tc['label']};font-weight:700;font-size:0.82rem;"
                    f"margin-bottom:5px;letter-spacing:0.5px;'>▶ {tname}</div>"
                    f"<div style='line-height:2;'>{col_pills}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )

            # ── Render JOIN guide as a single card (same style as tables) ─────
            if join_lines:
                join_pills = ""
                for jline in join_lines:
                    # Skip the header labels like "JOIN GUIDE:" or "RELATIONSHIPS:"
                    if jline.endswith(":") or jline.upper().startswith("JOIN GUIDE") or jline.upper().startswith("RELATION"):
                        continue
                    # Each join line as a pill
                    join_pills += (
                        f"<div style='display:flex;align-items:center;gap:6px;"
                        f"padding:4px 0;border-bottom:1px solid #0d2137;'>"
                        f"<span style='color:#ffab40;font-size:0.7rem;'>🔗</span>"
                        f"<span style='color:#c8dff0;font-size:0.7rem;font-family:monospace;'>"
                        f"{jline}</span></div>"
                    )

                if join_pills:
                    st.markdown(
                        f"<div style='background:#ffab4018;border:1px solid #ffab4044;"
                        f"border-left:3px solid #ffab40;border-radius:8px;"
                        f"padding:8px 10px;margin:6px 0;'>"
                        f"<div style='color:#ffab40;font-weight:700;font-size:0.82rem;"
                        f"margin-bottom:6px;letter-spacing:0.5px;'>🔗 JOIN Relationships</div>"
                        f"{join_pills}"
                        f"</div>",
                        unsafe_allow_html=True
                    )
        else:
            st.error("DB not found — run `py sample_data/seed_db.py`")

    st.divider()

    # History
    st.markdown("<div class='sec-label'>📜 Query History</div>", unsafe_allow_html=True)
    with st.expander("Recent queries", expanded=False):
        hist = st.session_state["history"]
        if not hist:
            st.markdown("<span style='color:#1e3a4a;font-size:0.8rem;'>No queries yet.</span>",
                        unsafe_allow_html=True)
        else:
            for i, item in enumerate(reversed(hist[-5:]), 1):
                st.markdown(
                    f"<div style='color:#00d4ff;font-size:0.78rem;font-weight:600;"
                    f"padding:4px 0 2px 0;'>{i}. {item['question']}</div>",
                    unsafe_allow_html=True)
                st.code(item["sql"], language="sql")
                st.markdown(
                    f"<span style='color:#00e676;font-size:0.72rem;'>"
                    f"↳ {item['rows']} rows</span>", unsafe_allow_html=True)
                st.divider()

# ─────────────────────────────────────────────────────────────────────────────
#  HERO
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrap">
  <div class="hero-nl">Natural Language</div>
  <div class="hero-title">
    NL &nbsp;<span class="hero-arrow">→</span>&nbsp; SQL Converter
  </div>
  <div class="hero-sub">
    Type a question in plain English &mdash; ANANTA AI generates the SQL,
    runs it, and returns your results instantly
  </div>
</div>
""", unsafe_allow_html=True)
st.divider()

# ─────────────────────────────────────────────────────────────────────────────
#  EXAMPLE CHIPS
# ─────────────────────────────────────────────────────────────────────────────
EXAMPLES = [
    "Top 5 employees by salary",
    "Total sales by region",
    "Highest budget department",
    "Monthly sales trend",
    "Avg salary by department",
    "Top 3 products by sales",
]
JOIN_EXAMPLES = [
    "Employee name + total sales",
    "Employees with sales > 10000",
    "Employee, dept name & budget",
    "Employees who sold in North",
    "Dept name + total dept sales",
]

st.markdown("<div class='sec-label'>💡 Single Table</div>", unsafe_allow_html=True)
ec = st.columns(len(EXAMPLES))
for col, ex in zip(ec, EXAMPLES):
    with col:
        if st.button(ex, use_container_width=True):
            st.session_state["selected_example"] = ex

st.markdown("<div class='sec-label' style='margin-top:10px;'>🔗 JOIN Queries</div>",
            unsafe_allow_html=True)
jc = st.columns(len(JOIN_EXAMPLES))
for col, ex in zip(jc, JOIN_EXAMPLES):
    with col:
        if st.button(ex, use_container_width=True):
            st.session_state["selected_example"] = ex

# ─────────────────────────────────────────────────────────────────────────────
#  INPUT
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
question = st.text_area(
    "✏️ Ask anything about your data:",
    value=st.session_state["selected_example"],
    height=90,
    placeholder="e.g.  Show each employee's name with their total sales amount",
)
submit = st.button("🧠  Convert to SQL & Run", type="primary", use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
#  PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
if submit:
    q = question.strip()
    st.session_state["last_result"]  = None
    st.session_state["last_blocked"] = None

    if not q:
        st.warning("⚠️ Please enter a question first.")
        st.stop()

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key or len(api_key) <= 1:
        st.error("🔑 GROQ_API_KEY missing — add it to your .env file.")
        st.stop()

    st.divider()

    # ── What does this do? ────────────────────────────────────────────────────
    st.markdown("""
    <div style='background:linear-gradient(90deg,#041828,#07101a);
                border:1px solid #0d2a3a;border-left:3px solid #00d4ff;
                border-radius:10px;padding:14px 18px;margin-bottom:16px;'>
      <div style='color:#00d4ff;font-weight:700;font-size:0.85rem;
                  letter-spacing:1px;margin-bottom:6px;'>
        🧠 HOW ANANTA AI WORKS — AGENT LOOP
      </div>
      <div style='color:#445577;font-size:0.8rem;line-height:1.8;'>
        <b style='color:#7b9fcc;'>Step 1</b> — Reads your database schema (tables, columns, relationships)<br>
        <b style='color:#7b9fcc;'>Step 2</b> — Checks your question for destructive intent before calling AI<br>
        <b style='color:#7b9fcc;'>Step 3</b> — Converts your English question into SQL using Groq LLaMA<br>
        <b style='color:#7b9fcc;'>Step 4</b> — Safety check: scans generated SQL for forbidden keywords<br>
        <b style='color:#7b9fcc;'>Step 5</b> — Executes the SQL. If it fails, the <b style='color:#00d4ff;'>
        agent loop</b> kicks in — the error is fed back to the AI, which rewrites
        the SQL. Repeats up to <b style='color:#00d4ff;'>3 attempts</b>.<br>
        <b style='color:#7b9fcc;'>Step 6</b> — Returns results as a table + chart + plain-English explanation
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### ⚙️ Agent Pipeline")

    # ── Step placeholders ─────────────────────────────────────────────────────
    s1       = st.empty()   # schema
    s2       = st.empty()   # intent check
    s3       = st.empty()   # generate SQL
    s4       = st.empty()   # SQL safety
    loop_box = st.empty()   # agent loop
    s6       = st.empty()   # explanation
    block_box = st.empty()  # block explanation card (shown when blocked)

    def step(el, icon, label, detail="", state="running"):
        cls = {"running":"step-running","done":"step-done","error":"step-error",
               "warn":"step-warn","pending":"step-pending"}[state]
        det = f"<div class='step-detail'>{detail}</div>" if detail else ""
        el.markdown(
            f"<div class='step-card {cls}'>"
            f"<div class='step-icon'>{icon}</div>"
            f"<div class='step-body'><div class='step-label'>{label}</div>{det}</div>"
            f"</div>", unsafe_allow_html=True)

    # Initial pending state for all steps
    step(s1,"⏳","Reading Database Schema…","","running")
    step(s2,"○","Intent Check — Read-Only Guard","Waiting…","pending")
    step(s3,"○","AI Generating SQL","Waiting…","pending")
    step(s4,"○","SQL Safety Check","Waiting…","pending")
    loop_box.markdown(
        "<div class='step-card step-pending'>"
        "<div class='step-icon'>○</div>"
        "<div class='step-body'><div class='step-label'>Agent Loop — Execute &amp; Auto-Fix</div>"
        "<div class='step-detail'>Waiting…</div></div></div>",
        unsafe_allow_html=True)
    step(s6,"○","Generating Explanation","Waiting…","pending")

    # ── Step 1: Schema ────────────────────────────────────────────────────────
    refreshed   = get_schema(DEFAULT_DB)
    table_count = refreshed.count("TABLE ")
    step(s1,"✅","Schema Read",
         f"{table_count} tables · employees · sales · departments","done")

    # ── Step 2: Intent check on raw question ─────────────────────────────────
    step(s2,"⏳","Intent Check — scanning your question…",
         "Checking for destructive operations before calling AI","running")
    intent_safe, intent_reason = check_question_intent(q)
    if not intent_safe:
        step(s2,"🚫","Request Blocked — Destructive Intent Detected",
             intent_reason,"error")
        step(s3,"○","Skipped — AI not called","","pending")
        step(s4,"○","Skipped","","pending")
        loop_box.markdown(
            "<div class='step-card step-pending'>"
            "<div class='step-icon'>○</div>"
            "<div class='step-body'><div class='step-label'>Skipped — query blocked before execution</div>"
            "</div></div>", unsafe_allow_html=True)
        step(s6,"○","Skipped","","pending")

        block_box.markdown(f"""
        <div class="block-card">
          <div class="block-title">🚫 Request Blocked — Destructive Intent Detected</div>
          <div class="block-reason">⛔ {intent_reason}</div>
          <div class="block-explain">
            <b style="color:#ff8888;">Why was this blocked?</b><br><br>
            ANANTA AI detected that your question is asking to
            <b>delete, modify, drop, or write</b> data. This is not allowed.<br><br>
            ANANTA AI operates in strict <b>read-only mode</b> — it can only
            <em>retrieve</em> and <em>display</em> data. It cannot delete rows,
            drop tables, update records, insert data, or make any changes to
            your database — regardless of how the request is phrased.<br><br>
            <b style="color:#ff8888;">Examples of blocked requests:</b><br>
            <code style="color:#ffaaaa;">
            "delete student table" &nbsp;·&nbsp; "remove all sales" &nbsp;·&nbsp;
            "drop employees" &nbsp;·&nbsp; "update salary" &nbsp;·&nbsp;
            "insert new record" &nbsp;·&nbsp; "clear the database"
            </code>
          </div>
          <div class="block-safe-hint">
            ✅ Try a read query instead — e.g.
            <em>"Show all employees"</em> &nbsp;·&nbsp; <em>"List total sales by region"</em>
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    step(s2,"✅","Intent Check Passed","No destructive intent detected","done")

    # ── Step 3: Generate SQL ──────────────────────────────────────────────────
    step(s3,"⏳","Groq AI Generating SQL…","LLaMA-3.3-70b · NL → SQL","running")
    try:
        sql = generate_sql(q, refreshed, api_key)
        step(s3,"✅","SQL Generated (Attempt 1)",
             f"<code style='color:#00d4ff'>{sql[:90]}{'…' if len(sql)>90 else ''}</code>",
             "done")
    except Exception as e:
        step(s3,"❌","SQL Generation Failed",str(e),"error")
        st.stop()

    # ── Step 4: SQL Safety check ──────────────────────────────────────────────
    step(s4,"⏳","SQL Safety Check…","Scanning generated SQL for forbidden keywords","running")
    safe, reason = is_safe(sql)
    if not safe:
        step(s4,"🚫","SQL BLOCKED by Safety Guard",reason,"error")
        loop_box.markdown(
            "<div class='step-card step-pending'>"
            "<div class='step-icon'>○</div>"
            "<div class='step-body'><div class='step-label'>Skipped — unsafe SQL blocked</div>"
            "</div></div>", unsafe_allow_html=True)
        step(s6,"○","Skipped","","pending")
        block_box.markdown(f"""
        <div class="block-card">
          <div class="block-title">🚫 SQL Blocked — Safety Violation in Generated Query</div>
          <div class="block-reason">⛔ {reason}</div>
          <div class="block-explain">
            <b style="color:#ff8888;">Why blocked?</b><br><br>
            The AI generated a query containing a <b>forbidden keyword</b>.
            Even though your question passed the intent check, the generated SQL
            was caught by the second safety layer.<br><br>
            <b style="color:#ff8888;">Forbidden SQL keywords:</b>
            <code style="color:#ffaaaa;">DROP · DELETE · INSERT · UPDATE · ALTER ·
            CREATE · TRUNCATE · REPLACE · ATTACH · VACUUM</code><br><br>
            Only <code style='color:#ffaaaa;'>SELECT</code> statements are permitted.
          </div>
          <div class="block-safe-hint">
            ✅ Try rephrasing as a read query — e.g.
            <em>"Show all employees"</em> or <em>"List total sales by region"</em>
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.session_state["last_blocked"] = {"sql": sql, "reason": reason}
        st.stop()

    step(s4,"✅","SQL Safety Check Passed","SELECT only · no destructive keywords found","done")

    # ── Step 5: AGENT LOOP (up to MAX_ATTEMPTS) ───────────────────────────────

    # Build a container to show the live loop status
    loop_container = loop_box.container()

    # Conversation history so each retry builds on all prior errors
    conv_history = [
        {"role": "system", "content":
            "You are an expert SQLite SQL generator. "
            "Return ONLY valid SQLite SELECT queries. No markdown, no explanation."}
    ]

    df        = None
    final_sql = sql
    succeeded = False

    for attempt in range(1, MAX_ATTEMPTS + 1):
        attempt_slot = loop_container.empty()

        if attempt == 1:
            attempt_slot.markdown(
                f"<div class='step-card step-running'>"
                f"<div class='step-icon'>⚡</div>"
                f"<div class='step-body'>"
                f"<div class='step-label'>Agent Loop · Attempt {attempt}/{MAX_ATTEMPTS} — Executing SQL…</div>"
                f"<div class='step-detail'><code style='color:#00d4ff'>{final_sql[:80]}…</code></div>"
                f"</div></div>",
                unsafe_allow_html=True)
        else:
            attempt_slot.markdown(
                f"<div class='step-card step-running'>"
                f"<div class='step-icon'>🔄</div>"
                f"<div class='step-body'>"
                f"<div class='step-label'>Agent Loop · Retry {attempt}/{MAX_ATTEMPTS} — AI rewriting SQL…</div>"
                f"<div class='step-detail'>Feeding error back to LLaMA-3.3-70b for correction…</div>"
                f"</div></div>",
                unsafe_allow_html=True)

        df, err = execute_query(DEFAULT_DB, final_sql)

        if err is None:
            # ✅ Success
            attempt_slot.markdown(
                f"<div class='step-card step-done'>"
                f"<div class='step-icon'>✅</div>"
                f"<div class='step-body'>"
                f"<div class='step-label'>Agent Loop · Attempt {attempt} — Query Succeeded</div>"
                f"<div class='step-detail'>{len(df)} rows · {len(df.columns)} columns returned</div>"
                f"</div></div>",
                unsafe_allow_html=True)
            succeeded = True
            break
        else:
            # ❌ Failed — show error and retry if attempts remain
            attempt_slot.markdown(
                f"<div class='step-card step-warn'>"
                f"<div class='step-icon'>⚠️</div>"
                f"<div class='step-body'>"
                f"<div class='step-label'>Agent Loop · Attempt {attempt} — SQL Error</div>"
                f"<div class='step-detail'>{err}</div>"
                f"</div></div>",
                unsafe_allow_html=True)

            if attempt < MAX_ATTEMPTS:
                # Feed error back to the AI to get a fixed SQL
                try:
                    fixed = retry_sql(
                        user_question=q,
                        failed_sql=final_sql,
                        error=err,
                        schema=refreshed,
                        api_key=api_key,
                        attempt=attempt,
                        history=conv_history,
                    )
                    # Append this exchange to conversation history
                    conv_history.append({"role": "assistant", "content": final_sql})
                    conv_history.append({"role": "user",
                        "content": f"That failed with: {err}. Try again."})

                    safe_r, reason_r = is_safe(fixed)
                    if not safe_r:
                        loop_container.error(f"🚫 Retry SQL blocked: {reason_r}")
                        break
                    final_sql = fixed
                except Exception as rex:
                    loop_container.error(f"❌ Retry generation error: {rex}")
                    break
            else:
                loop_container.markdown(
                    f"<div class='step-card step-error'>"
                    f"<div class='step-icon'>❌</div>"
                    f"<div class='step-body'>"
                    f"<div class='step-label'>Agent Loop exhausted — all {MAX_ATTEMPTS} attempts failed</div>"
                    f"<div class='step-detail'>Try rephrasing your question.</div>"
                    f"</div></div>",
                    unsafe_allow_html=True)

    if not succeeded:
        st.stop()

    # ── Step 6: Explain ───────────────────────────────────────────────────────
    step(s6,"⏳","Generating Plain-English Explanation…","","running")
    explanation = explain_sql(final_sql, api_key)
    step(s6,"✅","Explanation Ready","","done")

    st.session_state["history"].append({"question":q,"sql":final_sql,"rows":len(df)})
    st.session_state["history"] = st.session_state["history"][-20:]
    st.session_state["last_result"] = {"sql":final_sql,"explanation":explanation,"df":df}

# ─────────────────────────────────────────────────────────────────────────────
#  RESULTS
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state["last_result"]:
    res = st.session_state["last_result"]
    sql, explanation, df = res["sql"], res["explanation"], res["df"]

    st.divider()

    # Top row — SQL | Explanation | Stats
    c1, c2, c3 = st.columns([2.2, 2.2, 1])
    with c1:
        st.markdown("""
            <div class='r-card r-card-blue'>
              <div class='r-card-h h-blue'>📝 Generated SQL</div>
            </div>""", unsafe_allow_html=True)
        st.code(sql, language="sql")

    with c2:
        st.markdown("""
            <div class='r-card r-card-purple'>
              <div class='r-card-h h-purple'>💡 Plain-English Explanation</div>
            </div>""", unsafe_allow_html=True)
        st.info(explanation)

    with c3:
        st.markdown("""
            <div class='r-card r-card-green'>
              <div class='r-card-h h-green'>📊 Query Stats</div>
            </div>""", unsafe_allow_html=True)
        st.metric("🗂 Rows", len(df))
        st.metric("📐 Cols", len(df.columns))
        joins = sql.upper().count("JOIN")
        if joins:
            st.metric("🔗 JOINs", joins)

    # Results table
    st.divider()
    row_badge = f"{len(df)} rows"
    col_badge = f"{len(df.columns)} columns"
    st.markdown(f"""
        <div class='table-title'>
          🗂️ Query Results
          <span class='tbl-badge'>{row_badge}</span>
          <span class='tbl-badge' style='background:#7b2ff722;border-color:#7b2ff744;color:#bf7fff;'>
            {col_badge}</span>
        </div>""", unsafe_allow_html=True)

    if len(df) == 0:
        st.info("✅ Query ran successfully but returned no rows.")
    else:
        st.dataframe(df, use_container_width=True,
                     height=min(540, 60 + len(df) * 38))

        # ── DOWNLOAD PANEL ────────────────────────────────────────────────────
        st.markdown("""
        <div class='dl-panel'>
          <div class='dl-title'>⬇️ Download Results</div>
        </div>
        """, unsafe_allow_html=True)

        # Format selector
        fmt_col1, fmt_col2, fmt_col3, fmt_col4, fmt_spacer = st.columns([1,1,1,1,2])

        # ── CSV ──
        with fmt_col1:
            st.markdown("""
            <div class='dl-format-card'>
              <div class='dl-fmt-icon'>📄</div>
              <div class='dl-fmt-name'>CSV</div>
              <div class='dl-fmt-desc'>Spreadsheet compatible</div>
            </div>""", unsafe_allow_html=True)
            csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇ Download CSV",
                data=csv_data,
                file_name="ananta_ai_results.csv",
                mime="text/csv",
                use_container_width=True,
                key="dl_csv",
            )

        # ── JSON ──
        with fmt_col2:
            st.markdown("""
            <div class='dl-format-card'>
              <div class='dl-fmt-icon'>🔷</div>
              <div class='dl-fmt-name'>JSON</div>
              <div class='dl-fmt-desc'>API / developer friendly</div>
            </div>""", unsafe_allow_html=True)
            json_data = df.to_json(orient="records", indent=2).encode("utf-8")
            st.download_button(
                label="⬇ Download JSON",
                data=json_data,
                file_name="ananta_ai_results.json",
                mime="application/json",
                use_container_width=True,
                key="dl_json",
            )

        # ── Excel ──
        with fmt_col3:
            st.markdown("""
            <div class='dl-format-card'>
              <div class='dl-fmt-icon'>📊</div>
              <div class='dl-fmt-name'>Excel</div>
              <div class='dl-fmt-desc'>Microsoft Excel .xlsx</div>
            </div>""", unsafe_allow_html=True)
            excel_buf = io.BytesIO()
            with __import__("contextlib").suppress(Exception):
                df.to_excel(excel_buf, index=False, engine="openpyxl")
                excel_buf.seek(0)
            st.download_button(
                label="⬇ Download Excel",
                data=excel_buf,
                file_name="ananta_ai_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="dl_excel",
            )

        # ── Markdown ──
        with fmt_col4:
            st.markdown("""
            <div class='dl-format-card'>
              <div class='dl-fmt-icon'>📝</div>
              <div class='dl-fmt-name'>Markdown</div>
              <div class='dl-fmt-desc'>GitHub / docs ready</div>
            </div>""", unsafe_allow_html=True)
            md_data = df.to_markdown(index=False).encode("utf-8")
            st.download_button(
                label="⬇ Download MD",
                data=md_data,
                file_name="ananta_ai_results.md",
                mime="text/markdown",
                use_container_width=True,
                key="dl_md",
            )

    # Chart
    fig = auto_chart(df)
    if fig is not None:
        st.divider()
        st.markdown("""
            <div class='table-title'>
              📈 Auto-Generated Chart
              <span class='tbl-badge'>Plotly</span>
            </div>""", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)

    # Footer
    st.divider()
    st.markdown("""
        <div style='text-align:center;padding:8px 0;'>
          <span style='font-family:Orbitron,monospace;font-size:0.75rem;font-weight:700;
                       background:linear-gradient(90deg,#00d4ff,#7b2ff7);
                       -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                       background-clip:text;letter-spacing:2px;'>✦ ANANTA AI</span>
          <span style='color:#1e3a4a;font-size:0.75rem;'>
            &nbsp;·&nbsp; Groq LLaMA-3.3-70b
            &nbsp;·&nbsp; SQLite
            &nbsp;·&nbsp; Pandas + Plotly
            &nbsp;·&nbsp; Streamlit
          </span>
        </div>
    """, unsafe_allow_html=True)
