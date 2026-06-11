"""
chart_generator.py — Automatically selects the best Plotly chart
based on the shape and content of the query result DataFrame.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def _is_date_column(series: pd.Series) -> bool:
    """Heuristic: column values look like ISO dates (contain '-' and are parseable)."""
    if series.dtype == object:
        sample = series.dropna().head(5).astype(str)
        if all("-" in v for v in sample):
            try:
                pd.to_datetime(sample, infer_datetime_format=True)
                return True
            except Exception:
                pass
    return False


def auto_chart(df: pd.DataFrame) -> go.Figure | None:
    """
    Inspect the DataFrame and return the most appropriate Plotly figure.

    Rules:
      - 0 or 1 rows          → None (not enough data to chart)
      - 2 cols, col2 numeric + col1 date-like → Line chart
      - 2 cols, col2 numeric + col1 categorical (<10 unique) → Pie chart
      - 2 cols, col2 numeric → Bar chart
      - >2 cols, last col numeric → Bar chart using first col as x
      - fallback             → None
    """
    if df is None or len(df) <= 1:
        return None

    cols = df.columns.tolist()

    # ── Try to work with the first two columns ────────────────────────────────
    if len(cols) >= 2:
        x_col = cols[0]
        # Find the first numeric column after the first column
        numeric_cols = [c for c in cols[1:] if pd.api.types.is_numeric_dtype(df[c])]

        if not numeric_cols:
            return None

        y_col = numeric_cols[0]

        # Line chart: x looks like a date
        if _is_date_column(df[x_col]):
            df_sorted = df.sort_values(x_col)
            fig = px.line(
                df_sorted, x=x_col, y=y_col,
                title=f"{y_col} over {x_col}",
                markers=True,
                template="plotly_dark",
            )
            fig.update_layout(margin=dict(t=50, b=30))
            return fig

        # Pie chart: categorical x with few unique values
        if (
            df[x_col].dtype == object
            and df[x_col].nunique() < 10
            and len(cols) == 2
        ):
            fig = px.pie(
                df, names=x_col, values=y_col,
                title=f"{y_col} by {x_col}",
                template="plotly_dark",
                hole=0.3,
            )
            fig.update_layout(margin=dict(t=50, b=30))
            return fig

        # Default → Bar chart
        fig = px.bar(
            df, x=x_col, y=y_col,
            title=f"{y_col} by {x_col}",
            template="plotly_dark",
            color=y_col,
            color_continuous_scale="Viridis",
        )
        fig.update_layout(margin=dict(t=50, b=30), coloraxis_showscale=False)
        return fig

    return None
