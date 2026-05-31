import re
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots




# | Step | Topic                     |
# | ---- | ------------------------- |
# | 1    | Imports                   |
# | 2    | LLMEngine class           |
# | 3    | Model initialization      |
# | 4    | Prompt creation           |
# | 5    | Sending prompt to Llama   |
# | 6    | Extracting generated code |
# | 7    | Validating code           |
# | 8    | Executing code            |
# | 9    | Creating Plotly figures   |
# | 10   | Retry mechanism           |
# | 11   | Returning JSON            |



# FESTIVAL CALENDAR  (2019 – 2026)


FESTIVAL_CALENDAR = {
    "Diwali":     ["2019-10-27", "2020-11-14", "2021-11-04",
                   "2022-10-24", "2023-11-12", "2024-11-01", "2025-10-20"],
    "Holi":       ["2019-03-21", "2020-03-10", "2021-03-29",
                   "2022-03-18", "2023-03-08", "2024-03-25", "2025-03-14"],
    "Eid":        ["2019-06-05", "2020-05-25", "2021-05-14",
                   "2022-05-03", "2023-04-22", "2024-04-10", "2025-03-30"],
    "Christmas":  ["2019-12-25", "2020-12-25", "2021-12-25",
                   "2022-12-25", "2023-12-25", "2024-12-25", "2025-12-25"],
    "New Year":   ["2019-01-01", "2020-01-01", "2021-01-01",
                   "2022-01-01", "2023-01-01", "2024-01-01", "2025-01-01"],
    "Navratri":   ["2019-10-07", "2020-10-17", "2021-10-07",
                   "2022-09-26", "2023-10-15", "2024-10-03", "2025-09-22"],
    "Durga Puja": ["2019-10-07", "2020-10-22", "2021-10-11",
                   "2022-10-02", "2023-10-20", "2024-10-09", "2025-09-28"],
}



# SYSTEM PROMPTS  (LLM only used for Q&A and Report now)


QA_QUERY_SYSTEM_PROMPT = """You are an expert Python/Pandas data analyst.
The DataFrame is called `df`. You must store your final answer in a variable called `result`.

STRICT RULES:
1. Return ONLY raw executable Python code. No markdown. No ``` blocks. No explanation.
2. The variable must be named exactly: result
3. Use ONLY column names from the schema provided. Copy them exactly.
4. result must be a scalar, string, pd.Series, or pd.DataFrame (max 20 rows).
5. Never use .ix[] — use .loc[] or .iloc[].
6. Never use import statements.
7. For listing all column names: result = pd.Series(df.columns.tolist())
8. For counting columns: result = len(df.columns)
9. For showing sample data: result = df.head(5)

CORRECT EXAMPLES:
Question: list all column names
result = pd.Series(df.columns.tolist())

Question: how many columns are there?
result = len(df.columns)

Question: which store has the highest sales?
result = df.groupby('store')['weekly_sales'].sum().idxmax()

Question: show top 5 stores by total sales
result = df.groupby('store')['weekly_sales'].sum().sort_values(ascending=False).head(5)

Question: what is average temperature?
result = df['temperature'].mean()

Question: show first few rows
result = df.head(5)
"""

QA_INTERPRET_SYSTEM_PROMPT = """You are a senior business analyst.
You receive a QUESTION and the exact RAW RESULT from a pandas query.

STRICT RULES:
1. Use ONLY the values present in RESULT. Never invent numbers.
2. If result is a list of column names, list them clearly as: Column 1, Column 2, etc.
3. If result is a single number, state it directly in one sentence.
4. If result is a table/series, summarize the top findings with actual values.
5. Maximum 3 sentences. No preamble. No 'based on the data'.
6. Never describe what columns represent  only answer the question asked.

EXAMPLES:
Question: list all column names
Result: ['store', 'date', 'weekly_sales', 'holiday_flag', 'temperature', 'fuel_price', 'cpi', 'unemployment']
Answer: The dataset has 8 columns: store, date, weekly_sales, holiday_flag, temperature, fuel_price, cpi, and unemployment.

Question: which store has highest sales?
Result: 20
Answer: Store 20 has the highest total weekly sales across the entire dataset.
"""

REPORT_SYSTEM_PROMPT = """You are a senior business analyst writing an executive report.
You receive a dashboard data summary.
Write a structured report with:
1. EXECUTIVE SUMMARY     (3-4 sentences)
2. KEY FINDINGS          (5 bullet points with specific numbers)
3. TOP PERFORMERS        (best performers with numbers)
4. AREAS OF CONCERN      (worst performers with numbers)
5. FESTIVAL IMPACT       (skip if no festival data)
6. RECOMMENDATIONS       (3 actionable bullet points)
Use actual numbers. No fluff. 300-450 words total.
"""

# Chart planner prompt — LLM only decides WHAT to show, not HOW to code it
CHART_PLANNER_PROMPT = """You are a data analyst deciding what charts to show based on the user's request.
You receive a dataset schema and a user request.
Respond with a JSON array of chart specifications.

Each item must have these exact fields:
  - "chart_type": one of "bar", "line", "box", "scatter", "pie", "histogram"
  - "title": a clear descriptive title that matches what the user asked
  - "x_col": exact column name for x axis (must exist in schema)
  - "y_col": exact column name for y axis (must exist in schema)
  - "color_col": column to color by (use null if not needed)
  - "agg": aggregation function, one of "sum", "mean", "count", or "none"
  - "group_by": column to group by before plotting (same as x_col for categories)
  - "top_n": integer to limit rows shown (null for time series)
  - "sort": "asc" for lowest/worst/bottom, "desc" for highest/best/top, null for time series

CRITICAL RULES:
1. Return ONLY a valid JSON array. No markdown, no explanation, no ```json blocks.
2. Use ONLY column names that exist in the schema — exact spelling.
3. ALWAYS read the user request carefully:
   - "lowest", "bottom", "worst", "minimum" → sort = "asc"
   - "highest", "top", "best", "maximum" → sort = "desc"
   - "trend", "over time", "monthly", "yearly" → chart_type = "line", x_col = date column
   - "compare", "vs", "versus" → chart_type = "box" or grouped bar
   - "distribution", "spread" → chart_type = "histogram" or "box"
   - "share", "proportion", "percentage" → chart_type = "pie"
4. Generate charts that DIRECTLY answer the user's question.
5. Maximum 3 charts. Each chart must be different and useful.
6. For "lowest N" or "bottom N": set sort = "asc", top_n = N
7. For "top N" or "highest N": set sort = "desc", top_n = N
8. You have to understand the uses prompt vey carefully and generate charts accordingly. If user is asking for "lowest 10 stores sales wise", you should generate a bar chart showing the bottom 10 stores by total sales, a pie chart showing the sales share of those bottom 10 stores, and a line chart showing the sales trend for those lowest performing stores over time.
9. You look at the schema and prompt both and decide weathre to display avg, min or max in teh numerical graphs. 
10. STRICTLY follow the user prompt. You always have to follow the user prompt, generate charts accordingly and never generate charts that are not relevant to the user prompt.


EXAMPLES:

User: "lowest 10 stores sales wise"
[
  {"chart_type": "bar", "title": "Bottom 10 Stores by Total Sales", "x_col": "store", "y_col": "weekly_sales", "color_col": "store", "agg": "sum", "group_by": "store", "top_n": 10, "sort": "asc"},
  {"chart_type": "pie", "title": "Sales Share of Bottom 10 Stores", "x_col": "store", "y_col": "weekly_sales", "color_col": null, "agg": "sum", "group_by": "store", "top_n": 10, "sort": "asc"},
  {"chart_type": "line", "title": "Sales Trend for Lowest Performing Stores", "x_col": "date", "y_col": "weekly_sales", "color_col": null, "agg": "sum", "group_by": "date", "top_n": null, "sort": null}
]

User: "show holiday impact on sales"
[
  {"chart_type": "box", "title": "Sales Distribution: Holiday vs Non-Holiday", "x_col": "holiday_flag", "y_col": "weekly_sales", "color_col": "holiday_flag", "agg": "none", "group_by": null, "top_n": null, "sort": null},
  {"chart_type": "bar", "title": "Average Sales on Holiday vs Non-Holiday", "x_col": "holiday_flag", "y_col": "weekly_sales", "color_col": "holiday_flag", "agg": "mean", "group_by": "holiday_flag", "top_n": null, "sort": "desc"},
  {"chart_type": "line", "title": "Weekly Sales Trend Highlighting Holidays", "x_col": "date", "y_col": "weekly_sales", "color_col": null, "agg": "sum", "group_by": "date", "top_n": null, "sort": null}
]

User: "top 5 stores by average temperature"
[
  {"chart_type": "bar", "title": "Top 5 Stores by Average Temperature", "x_col": "store", "y_col": "temperature", "color_col": "store", "agg": "mean", "group_by": "store", "top_n": 5, "sort": "desc"},
  {"chart_type": "scatter", "title": "Temperature vs Weekly Sales", "x_col": "temperature", "y_col": "weekly_sales", "color_col": null, "agg": "none", "group_by": null, "top_n": null, "sort": null},
  {"chart_type": "histogram", "title": "Temperature Distribution Across Stores", "x_col": "temperature", "y_col": "temperature", "color_col": null, "agg": "none", "group_by": null, "top_n": null, "sort": null}
]
"""


# OLLAMA CLIENT


class OllamaClient:

    def __init__(self, model="llama3.2", base_url="http://localhost:11434"):
        self.model    = model
        self.base_url = base_url.rstrip("/")

    def is_running(self):
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    def list_models(self):
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if r.status_code == 200:
                return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            pass
        return []

    def generate(self, system_prompt, user_message,
                 temperature=0.2, max_tokens=2048, debug=False):
        if not self.is_running():
            raise ConnectionError("Ollama not running. Run: ollama serve")
        try:
            import ollama
            full_prompt = f"SYSTEM:\n{system_prompt}\n\nUSER:\n{user_message}"
            response    = ollama.generate(
                model=self.model,
                prompt=full_prompt,
                options={"temperature": temperature, "num_predict": max_tokens}
            )
            result = response["response"].strip()
            if debug:
                print(f"\n[DEBUG] {self.model} response ({len(result)} chars):")
                print(result[:600])
            return result
        except ImportError:
            raise ImportError("Run: pip install ollama")
        except Exception as e:
            raise ConnectionError(f"Ollama failed: {e}")



# CHART BUILDER  — Pure Python, always correct charts


class ChartBuilder:

    # Plotly colour palette
    COLORS = px.colors.qualitative.Set2

    @staticmethod
    def _prepare_data(df, spec):
        """Aggregate data according to the spec before plotting."""
        x_col    = spec["x_col"]
        y_col    = spec["y_col"]
        agg      = spec.get("agg", "sum")
        group_by = spec.get("group_by")
        top_n    = spec.get("top_n")
        sort     = spec.get("sort", "desc")  # "asc" = lowest first, "desc" = highest first

        print(f"  [_prepare_data] sort={sort}, top_n={top_n}, agg={agg}, group_by={group_by}")

        if agg == "none" or not group_by:
            plot_df = df[[c for c in [x_col, y_col,
                          spec.get("color_col")] if c and c in df.columns]].copy()
        else:
            if agg == "sum":
                plot_df = df.groupby(group_by)[y_col].sum().reset_index()
            elif agg == "mean":
                plot_df = df.groupby(group_by)[y_col].mean().reset_index()
            elif agg == "count":
                plot_df = df.groupby(group_by)[y_col].count().reset_index()
            else:
                plot_df = df.groupby(group_by)[y_col].sum().reset_index()

            # ── Sort BEFORE slicing top_n so lowest/highest is correct ──
            if sort == "asc":
                # Lowest first — for "bottom N", "lowest N", "worst N"
                plot_df = plot_df.sort_values(y_col, ascending=True)
                print(f"  [_prepare_data] Sorted ASC (lowest first). Top row: {plot_df.iloc[0][y_col]:.0f}")
            else:
                # Highest first — default
                plot_df = plot_df.sort_values(y_col, ascending=False)
                print(f"  [_prepare_data] Sorted DESC (highest first). Top row: {plot_df.iloc[0][y_col]:.0f}")

            # ── Slice AFTER sorting ──
            if top_n:
                plot_df = plot_df.head(int(top_n))
                print(f"  [_prepare_data] Sliced to top_n={top_n}. Rows kept: {len(plot_df)}")

        # Cast x to string for categorical axes to prevent numeric scaling
        if x_col in plot_df.columns and agg != "none":
            unique_count = plot_df[x_col].nunique()
            if unique_count < 100:
                plot_df[x_col] = plot_df[x_col].astype(str)

        return plot_df

    @staticmethod
    def _format_value(val):
        """Format large numbers cleanly for hover labels."""
        if isinstance(val, (int, float)):
            if abs(val) >= 1_000_000_000:
                return f"${val/1_000_000_000:.2f}B"
            elif abs(val) >= 1_000_000:
                return f"${val/1_000_000:.2f}M"
            elif abs(val) >= 1_000:
                return f"${val/1_000:.1f}K"
        return str(val)

    @staticmethod
    def _apply_layout(fig, title):
        """Apply a clean, professional layout to every chart."""
        fig.update_layout(
            title=dict(text=title, font=dict(size=16, color="#1a1a2e"), x=0.02),
            paper_bgcolor="white",
            plot_bgcolor="#f8f9fc",
            font=dict(family="'Segoe UI', Arial, sans-serif", size=12,
                      color="#444"),
            hoverlabel=dict(bgcolor="#1a1a2e", font_color="white",
                            font_size=12, bordercolor="#1a1a2e"),
            hovermode="closest",
            legend=dict(bgcolor="rgba(255,255,255,0.9)",
                        bordercolor="#e0e0e0", borderwidth=1),
            margin=dict(l=60, r=30, t=60, b=60),
            xaxis=dict(gridcolor="#eef0f4", showgrid=True,
                       zeroline=False, linecolor="#ddd"),
            yaxis=dict(gridcolor="#eef0f4", showgrid=True,
                       zeroline=False, linecolor="#ddd"),
        )
        return fig

    def build(self, df, spec):
        """Build one Plotly figure from a spec dict. Always returns a valid figure."""
        chart_type = spec.get("chart_type", "bar")
        title      = spec.get("title", "Chart")
        x_col      = spec["x_col"]
        y_col      = spec["y_col"]
        color_col  = spec.get("color_col")

        # Validate columns exist
        for col in [x_col, y_col]:
            if col not in df.columns:
                # Return an empty placeholder figure instead of crashing
                fig = go.Figure()
                fig.update_layout(title=f" Column '{col}' not found in data")
                return {"title": title, "figure_json": json.loads(fig.to_json())}

        plot_df = self._prepare_data(df, spec)

        try:
            if chart_type == "bar":
                color_arg = color_col if color_col and color_col in plot_df.columns else x_col
                fig = px.bar(
                    plot_df, x=x_col, y=y_col,
                    color=color_arg if color_arg in plot_df.columns else None,
                    title=title,
                    color_discrete_sequence=self.COLORS,
                    hover_data={c: True for c in plot_df.columns},
                    text_auto=".2s"
                )
                fig.update_traces(textposition="outside",
                                  marker_line_width=0)

            elif chart_type == "line":
                color_arg = color_col if color_col and color_col in plot_df.columns else None
                fig = px.line(
                    plot_df, x=x_col, y=y_col,
                    color=color_arg,
                    title=title,
                    color_discrete_sequence=self.COLORS,
                    hover_data={c: True for c in plot_df.columns},
                    markers=True
                )
                fig.update_traces(line=dict(width=2.5))

            elif chart_type == "box":
                color_arg = color_col if color_col and color_col in plot_df.columns else x_col
                # Cast x to string for box plots
                plot_df[x_col] = plot_df[x_col].astype(str)
                fig = px.box(
                    plot_df, x=x_col, y=y_col,
                    color=color_arg if color_arg in plot_df.columns else None,
                    title=title,
                    color_discrete_sequence=self.COLORS,
                    points="outliers"
                )

            elif chart_type == "scatter":
                color_arg = color_col if color_col and color_col in plot_df.columns else None
                fig = px.scatter(
                    plot_df, x=x_col, y=y_col,
                    color=color_arg,
                    title=title,
                    color_discrete_sequence=self.COLORS,
                    hover_data={c: True for c in plot_df.columns},
                    opacity=0.7
                )

            elif chart_type == "pie":
                fig = px.pie(
                    plot_df, names=x_col, values=y_col,
                    title=title,
                    color_discrete_sequence=self.COLORS,
                    hole=0.35  # donut style
                )
                fig.update_traces(textposition="inside",
                                  textinfo="percent+label")

            elif chart_type == "histogram":
                fig = px.histogram(
                    plot_df, x=x_col,
                    color=color_col if color_col and color_col in plot_df.columns else None,
                    title=title,
                    color_discrete_sequence=self.COLORS,
                    nbins=30
                )

            else:
                fig = px.bar(plot_df, x=x_col, y=y_col, title=title)

            self._apply_layout(fig, title)
            return {"title": title, "figure_json": json.loads(fig.to_json())}

        except Exception as e:
            fig = go.Figure()
            fig.update_layout(title=f"  Could not render: {title} ({e})")
            return {"title": title, "figure_json": json.loads(fig.to_json())}



# CHART PLANNER  — LLM decides WHAT, Python builds HOW


class ChartPlanner:
    

    def __init__(self, ollama_client: OllamaClient, debug=False):
        self.ollama  = ollama_client
        self.debug   = debug
        self.builder = ChartBuilder()

    def _build_fallback_specs(self, df, user_prompt=""):
        """
        If LLM fails, generate sensible default chart specs.
        Reads user_prompt to detect sort direction and top_n.
        """
        import re as _re
        specs       = []
        prompt_low  = user_prompt.lower()

        # ── Detect sort direction ──
        if any(w in prompt_low for w in ["lowest", "bottom", "worst", "minimum", "least", "smallest"]):
            default_sort = "asc"
            rank_label   = "Bottom"
        else:
            default_sort = "desc"
            rank_label   = "Top"

        # ── Detect N from prompt e.g. "lowest 10", "top 5" ──
        n_match      = _re.search(r'\b(\d+)\b', prompt_low)
        default_top_n = int(n_match.group(1)) if n_match else 10

        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        date_cols    = df.select_dtypes(include=["datetime64"]).columns.tolist()

        # ── Detect main metric ──
        main_metric = None
        for kw in ["sales", "revenue", "amount", "price", "profit", "score"]:
            for col in numeric_cols:
                if kw in col.lower():
                    main_metric = col
                    break
            if main_metric:
                break
        if not main_metric and numeric_cols:
            main_metric = numeric_cols[0]

        # ── Detect main category ──
        main_cat = None
        for kw in ["store", "region", "product", "category", "dept", "city", "branch"]:
            for col in df.columns:
                if kw in col.lower() and df[col].nunique() < 100:
                    main_cat = col
                    break
            if main_cat:
                break
        if not main_cat:
            for col in df.columns:
                if df[col].nunique() < 50 and col != main_metric:
                    main_cat = col
                    break

        # ── Detect flag column ──
        flag_col = None
        for col in df.columns:
            if any(kw in col.lower() for kw in ["holiday", "flag", "weekend", "promo"]):
                if df[col].nunique() <= 5:
                    flag_col = col
                    break

        # Chart 1 — Bar: lowest/highest N by main metric
        if main_cat and main_metric:
            specs.append({
                "chart_type": "bar",
                "title":      f"{rank_label} {default_top_n} {main_cat.replace('_',' ').title()} by {main_metric.replace('_',' ').title()}",
                "x_col":      main_cat,
                "y_col":      main_metric,
                "color_col":  main_cat,
                "agg":        "sum",
                "group_by":   main_cat,
                "top_n":      default_top_n,
                "sort":       default_sort       # ← uses detected direction
            })

        # Chart 2 — Line trend
        if date_cols and main_metric:
            specs.append({
                "chart_type": "line",
                "title":      f"{main_metric.replace('_',' ').title()} Trend Over Time",
                "x_col":      date_cols[0],
                "y_col":      main_metric,
                "color_col":  None,
                "agg":        "sum",
                "group_by":   date_cols[0],
                "top_n":      None,
                "sort":       None
            })

        # Chart 3 — Box or Pie
        if flag_col and main_metric:
            specs.append({
                "chart_type": "box",
                "title":      f"{main_metric.replace('_',' ').title()} by {flag_col.replace('_',' ').title()}",
                "x_col":      flag_col,
                "y_col":      main_metric,
                "color_col":  flag_col,
                "agg":        "none",
                "group_by":   None,
                "top_n":      None,
                "sort":       None
            })
        elif main_cat and main_metric and len(specs) < 3:
            specs.append({
                "chart_type": "pie",
                "title":      f"{rank_label} {default_top_n} {main_cat.replace('_',' ').title()} Sales Share",
                "x_col":      main_cat,
                "y_col":      main_metric,
                "color_col":  main_cat,
                "agg":        "sum",
                "group_by":   main_cat,
                "top_n":      default_top_n,
                "sort":       default_sort       # ← uses detected direction
            })

        print(f"  [Fallback] sort={default_sort}, top_n={default_top_n}, charts={len(specs)}")
        return specs[:3]

    def plan_and_build(self, user_prompt, df, metadata):
        
        # Step 1: Ask LLM for a JSON chart plan.
        # Step 2: Parse the plan.
        # Step 3: Build charts in pure Python using ChartBuilder.
        # Step 4: On any failure, fall back to sensible defaults.
        
        schema = metadata.get("llm_schema_description", "")

        user_msg = (
            f"DATASET SCHEMA:\n{schema}\n\n"
            f"USER REQUEST:\n{user_prompt}\n\n"
            f"Return ONLY a JSON array of chart specs. No markdown, no explanation."
        )

        specs = None
        try:
            raw = self.ollama.generate(
                system_prompt=CHART_PLANNER_PROMPT,
                user_message=user_msg,
                temperature=0.1,
                max_tokens=1024,
                debug=self.debug
            )
            print(f"\n[ChartPlanner RAW LLM OUTPUT]:\n{raw[:800]}\n")  # DEBUG
            # Extract JSON array from response
            json_match = re.search(r'\[.*\]', raw, re.DOTALL)
            if json_match:
                specs = json.loads(json_match.group())
                # Validate each spec has required fields
                specs = [s for s in specs
                         if s.get("x_col") in df.columns
                         and s.get("y_col") in df.columns]
                if not specs:
                    raise ValueError("No valid specs after column validation")
                print(f"  LLM planned {len(specs)} charts")
            else:
                raise ValueError("No JSON array found in LLM response")

        except Exception as e:
            print(f"   LLM planning failed ({e}) — using smart defaults")
            specs = self._build_fallback_specs(df, user_prompt=user_prompt)

        # Build all charts in pure Python
        figures = []
        for spec in specs[:3]:
            print(f"  Building: {spec.get('title', 'Chart')} ({spec.get('chart_type')})")
            fig_data = self.builder.build(df, spec)
            figures.append(fig_data)

        return figures



# DATA SUMMARIZER


def summarize_chart_data(df, metadata):
    lines        = []
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols     = df.select_dtypes(include=["object","category"]).columns.tolist()
    date_cols    = df.select_dtypes(include=["datetime64"]).columns.tolist()

    lines.append(f"Dataset: {len(df):,} rows, {df.shape[1]} columns")

    for col in numeric_cols[:5]:
        lines.append(
            f"{col}: total={df[col].sum():,.2f}, "
            f"avg={df[col].mean():,.2f}, "
            f"max={df[col].max():,.2f}, min={df[col].min():,.2f}"
        )
    for col in cat_cols[:3]:
        top = df[col].value_counts().head(5)
        lines.append(f"\nTop values in '{col}':")
        for val, cnt in top.items():
            lines.append(f"  {val}: {cnt:,} rows")
    for col in date_cols[:1]:
        lines.append(f"\nDate range: {df[col].min().date()} to {df[col].max().date()}")
    if date_cols and numeric_cols:
        year_col = f"{date_cols[0]}_year"
        if year_col in df.columns:
            yearly = df.groupby(year_col)[numeric_cols[0]].sum()
            lines.append(f"\nYear-wise {numeric_cols[0]} totals:")
            for yr, total in yearly.items():
                lines.append(f"  {int(yr)}: {total:,.2f}")
    return "\n".join(lines)



# LLM ENGINE


class LLMEngine:

    def __init__(self, model="llama3.2", debug=False):
        self.debug   = debug
        self.ollama  = OllamaClient(model=model)
        self.planner = ChartPlanner(self.ollama, debug=debug)
        self._check_connection()

    def _check_connection(self):
        if not self.ollama.is_running():
            print("\n  Ollama not running. Run: ollama serve\n")
        else:
            available = self.ollama.list_models()
            print(f" Ollama connected — model: {self.ollama.model}")
            print(f"   Models available: {available}")

    # ── MODE 1: CHART GENERATION ─────────────────────────────────
    def generate_charts(self, user_prompt, df, metadata, max_retries=2):
        """
        LLM plans what charts to show (JSON spec).
        Python builds the actual charts (always correct).
        """
        print(f"\n[Charts] Planning charts for: {user_prompt[:60]}...")
        figures = self.planner.plan_and_build(user_prompt, df, metadata)
        print(f"   {len(figures)} charts built successfully")
        return figures

    # ── MODE 2: Q&A ──────────────────────────────────────────────
    def answer_question(self, question, df, metadata, max_retries=2):

            import re
            import json
            import pandas as pd
            import numpy as np
            import plotly.express as px

            # ── Shortcut: column listing questions (LLM always fails these) ──
            q_low = question.lower().strip()
            if any(phrase in q_low for phrase in [
            "column name", "list column", "show column",
            "all column", "column list", "name of column",
            "how many column", "number of column", "columns are"
            ]):
                col_list = [c for c in df.columns
                        if not any(c.endswith(s) for s in ("_year", "_month", "_quarter"))]
                answer_text = (
                f"The dataset has {len(col_list)} columns: "
                + ", ".join(col_list) + "."
            )
                return {
                "question":     question,
                "pandas_query": f"result = pd.Series({col_list})",
                "raw_result":   str(col_list),
                "answer":       answer_text,
                "mini_chart":   None
            }

            schema = metadata.get("llm_schema_description", "")

            pandas_code = None
            raw_result = None
            result_str = ""
            error_context = ""

            # =====================================================
            # QUESTION PROMPT
            # =====================================================
            query_msg = f"""
    DATASET SCHEMA:
    {schema}

    QUESTION:
    {question}

    You are an expert Pandas analyst.

    RULES:
    1. Use dataframe name: df
    2. Return ONLY executable Python code
    3. Store final output in variable named: result
    4. No markdown
    5. No explanations
    6. No ```python blocks

    GOOD EXAMPLE:
    result = df.groupby('store')['weekly_sales'].sum().idxmax()
    """

           
            # RETRY LOOP
           
            for attempt in range(1, max_retries + 2):

                print(f"\n[Q&A] Attempt {attempt}...")

                retry_note = (
                    f"\nPREVIOUS ERROR:\n{error_context}\nFix the code."
                    if error_context else ""
                )

                try:

                    raw = self.ollama.generate(
                        system_prompt=QA_QUERY_SYSTEM_PROMPT,
                        user_message=query_msg + retry_note,
                        temperature=0.1,
                        max_tokens=512,
                        debug=self.debug
                    )

                except Exception as e:

                    error_context = str(e)
                    continue

                
                # CLEAN LLM OUTPUT
                pandas_code = raw.strip()

                pandas_code = pandas_code.replace("```python", "")
                pandas_code = pandas_code.replace("```", "")
                pandas_code = pandas_code.strip()

                # ── SAFETY: reject code that doesn't set `result` ──
                if "result" not in pandas_code:
                    error_context = "Code does not contain variable named `result`. Must store answer in `result`."
                    print(f"\n Rejected (no result var): {pandas_code[:200]}")
                    continue

                print(f"\n[Q&A Attempt {attempt}] Generated Code:\n{pandas_code}\n")

                # =================================================
                # BASIC SECURITY
                # =================================================
                dangerous = [
                    "import os",
                    "open(",
                    "exec(",
                    "eval(",
                    "subprocess",
                    "__"
                ]

                if any(d in pandas_code for d in dangerous):

                    error_context = "Unsafe code detected"
                    continue

                # =================================================
                # EXECUTE CODE
                # =================================================
                try:

                    # Pass the full df including preprocessed helper columns
                    scope = {
                        "df": df.copy(),
                        "pd": pd,
                        "np": np,
                        "px": px,
                        "re": re,
                        "json": json,
                        "datetime": datetime,
                        "FESTIVAL_CALENDAR": FESTIVAL_CALENDAR
                    }

                    exec(pandas_code, {}, scope)

                    raw_result = scope.get("result")

                    if raw_result is None:

                        error_context = "Variable `result` not found"
                        continue

                    # =============================================
                    # FORMAT RESULT
                    # =============================================
                    if isinstance(raw_result, (pd.DataFrame, pd.Series)):

                        result_str = raw_result.head(20).to_string()

                    else:

                        result_str = str(raw_result)

                    print("\n Query Result:")
                    print(result_str[:500])

                    break

                except Exception as e:

                    error_context = str(e)

                    print(f"\n Execution Error: {e}")

            # =====================================================
            # FAILED AFTER RETRIES
            # =====================================================
            if raw_result is None:

                return {
                    "question": question,
                    "pandas_query": pandas_code or "Failed",
                    "raw_result": "Could not compute",
                    "answer": "Sorry, could not answer this question with the available data.",
                    "mini_chart": None
                }

            # =====================================================
            # BUSINESS INTERPRETATION
            # =====================================================
            print("\n[Q&A] Generating business explanation...")

            explanation_prompt = f"""
    QUESTION:
    {question}

    RESULT:
    {result_str}

    Explain this result like a business analyst.
    Use simple business language.
    Keep answer concise but insightful.
    """

            try:

                plain = self.ollama.generate(
                    system_prompt=QA_INTERPRET_SYSTEM_PROMPT,
                    user_message=explanation_prompt,
                    temperature=0.3,
                    max_tokens=400,
                    debug=self.debug
                )

            except Exception as e:

                plain = f"Could not generate explanation: {e}"

            
            # MINI CHART GENERATION
            
            mini_chart = None

            try:

                if isinstance(raw_result, pd.Series):

                    cdf = raw_result.reset_index()

                    cdf.columns = ["category", "value"]

                elif isinstance(raw_result, pd.DataFrame):

                    cdf = raw_result.head(15)

                else:

                    cdf = None

                if cdf is not None and len(cdf.columns) >= 2:

                    fig = px.bar(
                        cdf,
                        x=cdf.columns[0],
                        y=cdf.columns[1],
                        title=question[:60]
                    )

                    fig.update_layout(
                        paper_bgcolor="white",
                        plot_bgcolor="#f8f9fc"
                    )

                    mini_chart = json.loads(fig.to_json())

            except Exception as e:

                print("Mini chart failed:", e)

                       # FINAL RESPONSE
           
            return {
                "question": question,
                "pandas_query": pandas_code,
                "raw_result": result_str,
                "answer": plain.strip(),
                "mini_chart": mini_chart
            }




    # ── MODE 3: REPORT ───────────────────────────────────────────
    def generate_report(self, df, metadata):
        print("\n[Report] Summarising data...")
        summary = summarize_chart_data(df, metadata)
        print("[Report] Calling LLM...")
        text = self.ollama.generate(
            system_prompt=REPORT_SYSTEM_PROMPT,
            user_message=(
                f"DASHBOARD DATA SUMMARY:\n{summary}\n\n"
                f"SCHEMA:\n{metadata.get('llm_schema_description','')[:1000]}\n\n"
                f"Write the executive report now."
            ),
            temperature=0.5, max_tokens=1500, debug=self.debug
        )
        return {"report_text": text.strip(),
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data_summary": summary}



