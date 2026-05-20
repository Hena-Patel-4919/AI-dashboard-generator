import re
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ================================================================
# FESTIVAL CALENDAR  (2019 – 2026)
# ================================================================

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


# ================================================================
# SYSTEM PROMPTS  (LLM only used for Q&A and Report now)
# ================================================================

QA_QUERY_SYSTEM_PROMPT = """You are an expert data analyst.
Given a dataset schema, column information, and a business question,
write ONE Pandas expression that answers it correctly.
DataFrame is called `df`. Store result in variable called `result`.

RULES:
1. Return ONLY the Python code — nothing else, no explanation, no comments.
2. Result must be a scalar, string, or small Series/DataFrame (max 20 rows).
3. MAIN METRIC COLUMN and CATEGORY COLUMN are clearly stated below — use them.
4. For "average", "avg", "mean" questions → always use .mean() or .groupby().mean()
5. For "highest", "best", "top" with groupby → use .groupby().mean() then .idxmax()
   NOT .idxmax() on a single row — that picks ONE student, not a department average.
6. For "total", "sum" questions → use .sum() or .groupby().sum()
7. For "count", "how many" questions → use .value_counts() or .groupby().count()
8. For ranking → use .groupby()[col].mean().sort_values(ascending=False)

CORRECT examples:
  Q: "Which department has highest avg score?"
  A: result = df.groupby('department')['total_score'].mean().idxmax()

  Q: "Show avg score by department in descending order"
  A: result = df.groupby('department')['total_score'].mean().sort_values(ascending=False).round(2)

  Q: "How many students per department?"
  A: result = df['department'].value_counts()

  Q: "Which store had highest total sales?"
  A: result = df.groupby('store')['weekly_sales'].sum().idxmax()

WRONG (never do this):
  result = df.loc[df['assignments_avg'].idxmax(), 'department']  ← picks one student row, wrong
"""

QA_INTERPRET_SYSTEM_PROMPT = """You are a data analyst giving a direct answer.
You receive a business question and the exact data result computed by Pandas.
Write 2-3 sentences that state ONLY what the data result shows.

CRITICAL RULES:
- Use the EXACT numbers from DATA RESULT — do not change, round, or reinterpret them.
- If the result is a number like 20, the answer must include that exact number.
- Do NOT invent store names, product names, or locations that are not in the result.
- Do NOT say "Store A" or make up names — use the actual values shown.
- Do NOT add predictions, comparisons, or context not in the result.
- Keep it short: 2-3 sentences maximum.

Example: If DATA RESULT is "20", answer: "Store 20 had the highest total weekly sales."
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

# Chart planner prompt — LLM decides WHAT charts to make, Python builds them
CHART_PLANNER_PROMPT = """You are a data analyst. Decide what 3 charts to show.
You receive an EXACT list of column names from the dataset and a user request.

Return a JSON array of exactly 3 chart specifications.
Each spec must have:
  "chart_type"  : "bar", "line", "box", "scatter", "pie", or "histogram"
  "title"       : short descriptive title (max 6 words)
  "x_col"       : column name for X axis — MUST be from AVAILABLE COLUMNS list
  "y_col"       : column name for Y axis — MUST be from AVAILABLE COLUMNS list
  "color_col"   : column to color by, or null
  "agg"         : "mean" for scores/rates/percentages, "sum" for totals, "count" for frequency, "none" for raw
  "group_by"    : column to group by (usually same as x_col), or null
  "top_n"       : max categories to show (20 for many categories, null for dates)
  "sort"        : "desc", "asc", or null

CRITICAL RULES — follow exactly:
1. Use ONLY columns from the AVAILABLE COLUMNS list below. Never invent column names.
2. For score/grade/percentage columns always use agg="mean" not "sum".
3. Make all 3 charts DIFFERENT — different x_col or different chart_type.
4. For boolean/flag columns (0/1 or Yes/No) use chart_type="box" with agg="none".
5. For count/frequency charts use agg="count" and y_col=any column.
6. Return ONLY the JSON array — no explanation, no markdown backticks.

AVAILABLE COLUMNS: {columns_list}

Example for student data:
[
  {{"chart_type":"bar","title":"Avg Score by Department","x_col":"department","y_col":"total_score","color_col":"department","agg":"mean","group_by":"department","top_n":10,"sort":"desc"}},
  {{"chart_type":"bar","title":"Extracurricular Participation by Dept","x_col":"department","y_col":"extracurricular_activities","color_col":"department","agg":"count","group_by":"department","top_n":10,"sort":"desc"}},
  {{"chart_type":"box","title":"Score Distribution by Grade","x_col":"grade","y_col":"total_score","color_col":"grade","agg":"none","group_by":null,"top_n":null,"sort":null}}
]
"""


# ================================================================
# OLLAMA CLIENT
# ================================================================

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

    def _resolve_model(self):
        """Auto-resolve model name — handles llama3.2 vs llama3.2:latest."""
        available = self.list_models()
        if not available:
            return self.model
        # Exact match
        if self.model in available:
            return self.model
        # Try with :latest suffix
        with_latest = f"{self.model}:latest"
        if with_latest in available:
            return with_latest
        # Try prefix match
        for m in available:
            if m.startswith(self.model):
                return m
        return self.model  # fallback

    def generate(self, system_prompt, user_message,
                 temperature=0.2, max_tokens=2048, debug=False):
        if not self.is_running():
            raise ConnectionError("Ollama not running. Run: ollama serve")
        try:
            import ollama
            resolved_model = self._resolve_model()
            full_prompt = f"SYSTEM:\n{system_prompt}\n\nUSER:\n{user_message}"
            response    = ollama.generate(
                model=resolved_model,
                prompt=full_prompt,
                options={"temperature": temperature, "num_predict": max_tokens}
            )
            result = response["response"].strip()
            if debug:
                print(f"\n[DEBUG] {resolved_model} response ({len(result)} chars):")
                print(result[:600])
            return result
        except ImportError:
            raise ImportError("Run: pip install ollama")
        except Exception as e:
            raise ConnectionError(f"Ollama failed: {e}")


# ================================================================
# CHART BUILDER  — Pure Python, always correct charts
# ================================================================

class ChartBuilder:
    """
    Builds Plotly charts purely in Python from a chart specification.
    No LLM involved in the actual chart code — 100% reliable output.
    """

    # Plotly colour palette
    COLORS = px.colors.qualitative.Set2

    # Column keywords where MEAN makes more sense than SUM
    MEAN_KEYWORDS = [
        "score", "grade", "pct", "percent", "rate", "ratio", "avg",
        "average", "rating", "index", "gpa", "marks", "attendance",
        "temperature", "stress", "sleep", "hours", "satisfaction"
    ]

    @classmethod
    def _smart_agg(cls, col_name, requested_agg):
        """
        Override agg to 'mean' if the column is clearly a score/rate/percent.
        Summing scores across students gives meaningless 91K totals.
        """
        if requested_agg in ("sum", "auto"):
            col_lower = col_name.lower()
            if any(kw in col_lower for kw in cls.MEAN_KEYWORDS):
                return "mean"
        return requested_agg

    @classmethod
    def _prepare_data(cls, df, spec):
        """Aggregate data according to the spec before plotting."""
        x_col    = spec["x_col"]
        y_col    = spec["y_col"]
        agg      = cls._smart_agg(y_col, spec.get("agg", "sum"))
        group_by = spec.get("group_by")
        top_n    = spec.get("top_n")
        sort     = spec.get("sort", "desc")

        if agg == "none" or not group_by:
            plot_df = df[[c for c in [x_col, y_col,
                          spec.get("color_col")] if c and c in df.columns]].copy()
        else:
            if agg == "sum":
                plot_df = df.groupby(group_by)[y_col].sum().reset_index()
            elif agg == "mean":
                plot_df = df.groupby(group_by)[y_col].mean().reset_index()
                # Round mean values to 2 decimal places for cleaner display
                plot_df[y_col] = plot_df[y_col].round(2)
            elif agg == "count":
                plot_df = df.groupby(group_by)[y_col].count().reset_index()
            else:
                plot_df = df.groupby(group_by)[y_col].sum().reset_index()

            if sort == "desc":
                plot_df = plot_df.sort_values(y_col, ascending=False)
            elif sort == "asc":
                plot_df = plot_df.sort_values(y_col, ascending=True)

            if top_n:
                plot_df = plot_df.head(int(top_n))

        # Cast x to string for categorical axes to prevent numeric scaling
        if x_col in plot_df.columns and agg != "none":
            if plot_df[x_col].nunique() < 100:
                plot_df[x_col] = plot_df[x_col].astype(str)

        return plot_df, agg  # return agg used for title suffix

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
                fig.update_layout(title=f"⚠️ Column '{col}' not found in data")
                return {"title": title, "figure_json": json.loads(fig.to_json())}

        plot_df, actual_agg = self._prepare_data(df, spec)
        # Add "(Average)" suffix to title if we switched from sum to mean
        if actual_agg == "mean" and spec.get("agg") in ("sum", "auto", None):
            title = title.replace(" Total ", " Average ") if " Total " in title else title
            if "average" not in title.lower() and "avg" not in title.lower():
                title = title + " (Avg)"

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
            fig.update_layout(title=f"⚠️ Could not render: {title} ({e})")
            return {"title": title, "figure_json": json.loads(fig.to_json())}


# ================================================================
# CHART PLANNER  — LLM decides WHAT, Python builds HOW
# ================================================================

class ChartPlanner:
    """
    Asks the LLM to output a JSON plan of what charts to make.
    Then ChartBuilder builds them in pure Python — no LLM chart code.
    """

    def __init__(self, ollama_client: OllamaClient, debug=False):
        self.ollama  = ollama_client
        self.debug   = debug
        self.builder = ChartBuilder()

    def _build_fallback_specs(self, df, user_prompt=""):
        """
        Generates sensible chart specs based on data types.
        Handles retail, student, HR, financial data differently.
        Always produces 3 DIFFERENT charts.
        """
        specs        = []
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        cat_cols     = [c for c in df.select_dtypes(include=["object","category"]).columns
                        if df[c].nunique() < 60 and df[c].nunique() > 1]
        date_cols    = df.select_dtypes(include=["datetime64"]).columns.tolist()
        bool_cols    = [c for c in df.columns if df[c].nunique() <= 5
                        and c not in cat_cols and c not in date_cols]

        # ── Detect main metric ───────────────────────────────────
        metric_keywords = [
            ("sum",  ["sales","revenue","amount","price","profit","quantity","total_sales"]),
            ("mean", ["score","grade","pct","percent","attendance","rating","marks",
                      "total_score","avg","gpa","satisfaction","stress","sleep","hours",
                      "participation","projects","assignments","quizzes","midterm","final"]),
        ]
        main_metric = None
        main_agg    = "sum"
        for agg_type, keywords in metric_keywords:
            for kw in keywords:
                for col in numeric_cols:
                    if kw in col.lower():
                        main_metric = col
                        main_agg    = agg_type
                        break
                if main_metric:
                    break
            if main_metric:
                break
        if not main_metric and numeric_cols:
            # Pick the numeric column with the most variance (most informative)
            variances   = {col: df[col].var() for col in numeric_cols}
            main_metric = max(variances, key=variances.get)
            # Guess agg from value range
            if df[main_metric].max() <= 100:
                main_agg = "mean"

        # ── Detect main category ─────────────────────────────────
        cat_keywords = [
            "department","dept","category","region","store","branch",
            "grade","gender","level","type","class","group","subject"
        ]
        main_cat = None
        for kw in cat_keywords:
            for col in cat_cols:
                if kw in col.lower():
                    main_cat = col
                    break
            if main_cat:
                break
        if not main_cat and cat_cols:
            # Use the column with fewest unique values (clearest grouping)
            main_cat = min(cat_cols, key=lambda c: df[c].nunique())

        # ── Detect secondary metric (different from main) ────────
        sec_metric = None
        for col in numeric_cols:
            if col != main_metric:
                col_lower = col.lower()
                # Prefer a column related to the prompt
                if user_prompt and any(w in col_lower for w in user_prompt.lower().split()):
                    sec_metric = col
                    break
        if not sec_metric:
            for col in numeric_cols:
                if col != main_metric:
                    sec_metric = col
                    break

        # ── Detect boolean/flag column ───────────────────────────
        flag_col = None
        flag_keywords = ["holiday","flag","extracurricular","internet","activity",
                         "access","weekend","promo","gender","pass","fail"]
        for kw in flag_keywords:
            for col in df.columns:
                if kw in col.lower() and df[col].nunique() <= 10:
                    flag_col = col
                    break
            if flag_col:
                break

        # ── Build 3 DIFFERENT specs ───────────────────────────────
        used_combos = set()

        def make_spec(chart_type, title, x_col, y_col, color_col,
                      agg, group_by, top_n, sort):
            combo = (x_col, y_col, chart_type)
            if combo in used_combos:
                return None
            used_combos.add(combo)
            return {
                "chart_type": chart_type, "title": title,
                "x_col": x_col, "y_col": y_col, "color_col": color_col,
                "agg": agg, "group_by": group_by, "top_n": top_n, "sort": sort
            }

        # Chart 1 — main category vs main metric
        if main_cat and main_metric:
            agg_label = "Avg" if main_agg == "mean" else "Total"
            s = make_spec("bar",
                f"{agg_label} {main_metric.replace('_',' ').title()} by {main_cat.replace('_',' ').title()}",
                main_cat, main_metric, main_cat,
                main_agg, main_cat, 20, "desc")
            if s: specs.append(s)

        # Chart 2 — time trend OR second metric OR count
        if date_cols and main_metric and len(specs) < 3:
            s = make_spec("line",
                f"{main_metric.replace('_',' ').title()} Trend Over Time",
                date_cols[0], main_metric, None,
                main_agg, date_cols[0], None, None)
            if s: specs.append(s)
        elif flag_col and main_metric and len(specs) < 3:
            s = make_spec("box",
                f"{main_metric.replace('_',' ').title()} by {flag_col.replace('_',' ').title()}",
                flag_col, main_metric, flag_col,
                "none", None, None, None)
            if s: specs.append(s)
        elif sec_metric and main_cat and len(specs) < 3:
            sec_agg = "mean" if any(kw in sec_metric.lower()
                                    for kw in ChartBuilder.MEAN_KEYWORDS) else "sum"
            agg_label = "Avg" if sec_agg == "mean" else "Total"
            s = make_spec("bar",
                f"{agg_label} {sec_metric.replace('_',' ').title()} by {main_cat.replace('_',' ').title()}",
                main_cat, sec_metric, main_cat,
                sec_agg, main_cat, 20, "desc")
            if s: specs.append(s)

        # Chart 3 — distribution OR flag comparison OR count
        if flag_col and main_metric and len(specs) < 3:
            s = make_spec("box",
                f"{main_metric.replace('_',' ').title()} by {flag_col.replace('_',' ').title()}",
                flag_col, main_metric, flag_col,
                "none", None, None, None)
            if s: specs.append(s)
        elif main_cat and main_metric and len(specs) < 3:
            s = make_spec("pie",
                f"{main_metric.replace('_',' ').title()} Share by {main_cat.replace('_',' ').title()}",
                main_cat, main_metric, main_cat,
                main_agg, main_cat, 8, "desc")
            if s: specs.append(s)
        elif main_metric and len(specs) < 3:
            s = make_spec("histogram",
                f"Distribution of {main_metric.replace('_',' ').title()}",
                main_metric, main_metric, None,
                "none", None, None, None)
            if s: specs.append(s)

        return specs[:3]

    def _parse_filters(self, user_prompt, df):
        """
        Parse user prompt for filter instructions.
        
        KEY FIX: Detects year RANGE (2010-2012) vs single year (2011).
        - "2010-2012" or "3 years" → self._multi_year = [2010,2011,2012], NO filter applied
        - "year 2011" or "in 2011" → single year filter applied
        - "store 20" → filter to that store only
        """
        filtered_df     = df.copy()
        filter_notes    = []
        prompt_lower    = user_prompt.lower()
        self._multi_year = None   # reset

        date_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()

        # ── Check for year RANGE first (e.g. "2010-2012", "2010 to 2012") ──
        range_match = re.search(
            r'\b(20\d{2})\s*[-–to]+\s*(20\d{2})\b', user_prompt, re.IGNORECASE
        )
        if range_match and date_cols:
            year_start = int(range_match.group(1))
            year_end   = int(range_match.group(2))
            self._multi_year = list(range(year_start, year_end + 1))
            # Do NOT filter df — keep all years, we'll split in plan_and_build
            print(f"  📅 Multi-year mode detected: {self._multi_year}")
        else:
            # Check for "3 charts for 3 years" / "each year" / "all years" intent
            multi_hints = ["each year","all years","every year","per year","for each year",
                           "3 years","all 3","compare years","year comparison"]
            if any(hint in prompt_lower for hint in multi_hints) and date_cols:
                year_col = f"{date_cols[0]}_year"
                if year_col in df.columns:
                    self._multi_year = sorted(df[year_col].dropna().unique().astype(int).tolist())
                    print(f"  📅 Multi-year mode (auto): {self._multi_year}")

        # ── Single store filter e.g. "store 20" "for store 4" ──
        store_match = re.search(r'store\s+(\d+)', prompt_lower)
        if store_match and "store" in df.columns:
            store_num   = int(store_match.group(1))
            filtered_df = filtered_df[filtered_df["store"] == store_num]
            filter_notes.append(f"Store {store_num} only")

        # ── Single year filter — ONLY if no range/multi detected ──
        if self._multi_year is None:
            all_years = re.findall(r'\b(20\d{2})\b', user_prompt)
            if len(all_years) == 1 and date_cols:
                year_num      = int(all_years[0])
                year_col_name = f"{date_cols[0]}_year"
                if year_col_name in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df[year_col_name] == year_num]
                    filter_notes.append(f"Year {year_num} only")

        # ── Granularity preference ──
        if any(kw in prompt_lower for kw in ["year wise","yearly","annual","by year"]):
            self._granularity = "year"
        elif any(kw in prompt_lower for kw in ["quarter","quarterly","by quarter"]):
            self._granularity = "quarter"
        elif any(kw in prompt_lower for kw in ["month","monthly","by month"]):
            self._granularity = "month"
        else:
            self._granularity = "date"

        return filtered_df, filter_notes

    def _apply_granularity(self, spec, df):
        """Swap date column for year/quarter/month if user asked for it."""
        date_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()
        if not date_cols:
            return spec
        gran = getattr(self, "_granularity", "date")
        date_col = date_cols[0]
        gran_col = f"{date_col}_{gran}" if gran != "date" else date_col
        if gran_col in df.columns and spec.get("x_col") == date_col:
            spec = dict(spec)
            spec["x_col"]    = gran_col
            spec["group_by"] = gran_col
            spec["sort"]     = "asc"
        return spec

    def _get_single_spec(self, df, user_prompt, metadata):
        """
        Ask LLM for ONE chart spec (for the base chart type).
        Falls back to smart default. Used in multi-year mode.
        """
        col_list      = ", ".join(df.columns.tolist())
        filled_prompt = CHART_PLANNER_PROMPT.replace("{columns_list}", col_list)
        schema        = metadata.get("llm_schema_description", "")
        user_msg = (
            f"DATASET SCHEMA:\n{schema}\n\n"
            f"AVAILABLE COLUMNS: {col_list}\n\n"
            f"USER REQUEST:\n{user_prompt}\n\n"
            f"Return ONLY a JSON array of 1 chart spec (the most relevant chart type). "
            f"Use only columns listed above."
        )
        try:
            raw   = self.ollama.generate(
                system_prompt=filled_prompt,
                user_message=user_msg,
                temperature=0.1, max_tokens=512, debug=self.debug
            )
            match = re.search(r'\[.*\]', raw, re.DOTALL)
            if match:
                specs = json.loads(match.group())
                valid = [s for s in specs
                         if s.get("x_col") in df.columns
                         and s.get("y_col") in df.columns]
                if valid:
                    return valid[0]
        except Exception:
            pass
        # Fallback: bar of main category vs main metric
        fb = self._build_fallback_specs(df, user_prompt)
        return fb[0] if fb else None

    def plan_and_build(self, user_prompt, df, metadata):
        """
        Step 0: Parse filters — detect single year, year range, store filter.
        Step 1: If multi-year → build ONE chart per year (e.g. 3 charts for 2010/2011/2012).
        Step 2: Otherwise ask LLM for chart plan, build all at once.
        Step 3: Fix line charts to prevent 45-line spaghetti.
        """
        filtered_df, filter_notes = self._parse_filters(user_prompt, df)
        if filter_notes:
            print(f"  🔍 Filters applied: {filter_notes}")
        if len(filtered_df) == 0:
            print("  ⚠️ Filter returned empty — using full data")
            filtered_df = df.copy()

        # ── MULTI-YEAR MODE: one chart per year ───────────────────
        multi_year = getattr(self, "_multi_year", None)
        if multi_year and len(multi_year) > 1:
            print(f"  📅 Building {len(multi_year)} year charts: {multi_year}")

            date_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()
            year_col  = f"{date_cols[0]}_year" if date_cols else None

            # Get the base spec once
            base_spec = self._get_single_spec(filtered_df, user_prompt, metadata)
            if not base_spec:
                base_spec = self._build_fallback_specs(filtered_df, user_prompt)[0]

            figures = []
            for yr in multi_year[:3]:   # max 3 charts
                if year_col and year_col in filtered_df.columns:
                    yr_df = filtered_df[filtered_df[year_col] == yr].copy()
                else:
                    yr_df = filtered_df.copy()

                if len(yr_df) == 0:
                    continue

                spec        = dict(base_spec)
                spec        = self._fix_line_chart(spec, yr_df)
                spec["title"] = f"{spec.get('title','Chart')} ({yr})"
                print(f"  Building: {spec['title']} ({spec.get('chart_type')})")
                fig_data = self.builder.build(yr_df, spec)
                figures.append(fig_data)

            return figures

        # ── STANDARD MODE ─────────────────────────────────────────
        schema        = metadata.get("llm_schema_description", "")
        col_list      = ", ".join(filtered_df.columns.tolist())
        filled_prompt = CHART_PLANNER_PROMPT.replace("{columns_list}", col_list)
        user_msg = (
            f"DATASET SCHEMA:\n{schema}\n\n"
            f"AVAILABLE COLUMNS: {col_list}\n\n"
            f"USER REQUEST:\n{user_prompt}\n\n"
            f"Return ONLY a JSON array of 3 chart specs using only the columns listed above."
        )

        specs = None
        try:
            raw = self.ollama.generate(
                system_prompt=filled_prompt,
                user_message=user_msg,
                temperature=0.1, max_tokens=1024, debug=self.debug
            )
            json_match = re.search(r'\[.*\]', raw, re.DOTALL)
            if json_match:
                specs = json.loads(json_match.group())
                specs = [self._apply_granularity(s, filtered_df)
                         for s in specs
                         if s.get("x_col") in filtered_df.columns
                         and s.get("y_col") in filtered_df.columns]
                if not specs:
                    raise ValueError("No valid specs")
                print(f"  ✅ LLM planned {len(specs)} charts")
            else:
                raise ValueError("No JSON array found")
        except Exception as e:
            print(f"  ⚠️ Planning failed ({e}) — using smart defaults")
            specs = self._build_fallback_specs(filtered_df, user_prompt)
            specs = [self._apply_granularity(s, filtered_df) for s in specs]

        title_suffix = f" ({', '.join(filter_notes)})" if filter_notes else ""

        figures = []
        for spec in specs[:3]:
            spec        = dict(spec)
            spec        = self._fix_line_chart(spec, filtered_df)
            spec["title"] = spec.get("title", "Chart") + title_suffix
            print(f"  Building: {spec['title']} ({spec.get('chart_type')})")
            fig_data = self.builder.build(filtered_df, spec)
            figures.append(fig_data)

        return figures

    def _fix_line_chart(self, spec, df):
        """
        FIX: Prevent spaghetti line charts.
        If color_col on a line chart has too many unique values (> 8),
        remove the color split and aggregate all into one clean trend line.
        """
        if spec.get("chart_type") != "line":
            return spec
        color_col = spec.get("color_col")
        if color_col and color_col in df.columns:
            unique_vals = df[color_col].nunique()
            if unique_vals > 8:
                spec = dict(spec)
                spec["color_col"] = None   # remove color split
                print(f"  ✂️ Removed color split on {color_col} ({unique_vals} values) — too many lines")
        return spec


# ================================================================
# DATA SUMMARIZER
# ================================================================

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


# ================================================================
# LLM ENGINE
# ================================================================

class LLMEngine:

    def __init__(self, model="llama3.2", debug=False):
        self.debug   = debug
        self.ollama  = OllamaClient(model=model)
        self.planner = ChartPlanner(self.ollama, debug=debug)
        self._check_connection()

    def _check_connection(self):
        if not self.ollama.is_running():
            print("\n⚠️  Ollama not running. Run: ollama serve\n")
        else:
            available = self.ollama.list_models()
            print(f"✅ Ollama connected — model: {self.ollama.model}")
            print(f"   Models available: {available}")

    # ── MODE 1: CHART GENERATION ─────────────────────────────────
    def generate_charts(self, user_prompt, df, metadata, max_retries=2):
        """
        LLM plans what charts to show (JSON spec).
        Python builds the actual charts (always correct).
        """
        print(f"\n[Charts] Planning charts for: {user_prompt[:60]}...")
        figures = self.planner.plan_and_build(user_prompt, df, metadata)
        print(f"  ✅ {len(figures)} charts built successfully")
        return figures

    # ── MODE 2: Q&A ──────────────────────────────────────────────
    def _normalize_question(self, question):
        """
        Fix common typos and normalize question text before sending to LLM.
        Handles: arange→arrange, dept→department, avg→average, etc.
        """
        import re as _re
        q = question.strip()
        # Common typo fixes
        fixes = {
            r"\barange\b":      "arrange",
            r"\bdepartmens\b":  "departments",
            r"\bdpet\b":        "department",
            r"\bavg\b":         "average",
            r"\bscore s\b":     "scores",
            r"\bwhich dept\b":  "which department",
            r"\bmax\b":         "maximum",
            r"\bmin\b":         "minimum",
            r"\bdesc\b":        "descending",
            r"\basc\b":         "ascending",
            r"\bhighest avg\b": "highest average",
            r"\bno of\b":       "number of",
        }
        for pattern, replacement in fixes.items():
            q = _re.sub(pattern, replacement, q, flags=_re.IGNORECASE)
        return q

    def answer_question(self, question, df, metadata, max_retries=2):
        question      = self._normalize_question(question)
        schema        = metadata.get("llm_schema_description", "")
        pandas_code   = None
        raw_result    = None
        result_str    = ""
        error_context = ""

        # Detect main metric and category so LLM picks the right columns
        numeric_cols  = df.select_dtypes(include=np.number).columns.tolist()
        cat_cols      = [c for c in df.select_dtypes(include=["object","category"]).columns
                         if df[c].nunique() < 60]
        date_cols     = df.select_dtypes(include=["datetime64"]).columns.tolist()

        # Find main metric (total_score > sales > revenue > first numeric)
        main_metric = None
        for kw in ["total_score","total","sales","revenue","profit","amount","score","marks"]:
            for col in numeric_cols:
                if kw == col.lower() or kw in col.lower():
                    main_metric = col
                    break
            if main_metric: break
        if not main_metric and numeric_cols:
            main_metric = numeric_cols[0]

        # Find main category
        main_cat = None
        for kw in ["department","dept","category","region","store","branch","grade","gender"]:
            for col in cat_cols:
                if kw in col.lower():
                    main_cat = col
                    break
            if main_cat: break
        if not main_cat and cat_cols:
            main_cat = cat_cols[0]

        col_types_str = (
            f"NUMERIC COLUMNS: {', '.join(numeric_cols)}\n"
            f"CATEGORICAL COLUMNS: {', '.join(cat_cols)}\n"
            f"DATE COLUMNS: {', '.join(date_cols)}\n"
            f"MAIN METRIC (use this for score/sales questions): {main_metric}\n"
            f"MAIN CATEGORY (use this for grouping): {main_cat}\n"
        )

        query_msg = (
            f"DATASET SCHEMA:\n{schema}\n\n"
            f"{col_types_str}\n"
            f"QUESTION:\n{question}\n\n"
            f"Write ONE Pandas expression. Store in `result`. Return ONLY Python code."
        )

        # Pre-compute grouped stats so Q&A matches chart values exactly
        precomputed_context = ""
        if main_metric and main_cat:
            try:
                grouped_mean = df.groupby(main_cat)[main_metric].mean().round(2)
                grouped_sum  = df.groupby(main_cat)[main_metric].sum().round(2)
                grouped_count = df[main_cat].value_counts()
                # Decide whether mean or sum is more meaningful
                is_mean_metric = any(kw in main_metric.lower()
                    for kw in ["score","grade","pct","percent","avg","rate",
                               "attendance","rating","marks","stress","sleep","hours"])
                if is_mean_metric:
                    precomputed_context = (
                        f"\nPRE-COMPUTED VALUES (use these exact numbers in your code):\n"
                        f"Average {main_metric} by {main_cat}:\n"
                        + grouped_mean.sort_values(ascending=False).to_string()
                        + f"\nHighest: {grouped_mean.idxmax()} = {grouped_mean.max():.2f}"
                        + f"\nLowest:  {grouped_mean.idxmin()} = {grouped_mean.min():.2f}\n"
                    )
                else:
                    precomputed_context = (
                        f"\nPRE-COMPUTED VALUES (use these exact numbers):\n"
                        f"Total {main_metric} by {main_cat}:\n"
                        + grouped_sum.sort_values(ascending=False).to_string()
                        + f"\nHighest: {grouped_sum.idxmax()} = {grouped_sum.max():,.2f}\n"
                    )
            except Exception:
                precomputed_context = ""

        for attempt in range(1, max_retries + 2):
            print(f"\n[Q&A] Attempt {attempt}...")
            retry_note = f"\nERROR: {error_context}\nFix it." if error_context else ""
            raw = self.ollama.generate(
                system_prompt=QA_QUERY_SYSTEM_PROMPT,
                user_message=query_msg + precomputed_context + retry_note,
                temperature=0.1, max_tokens=512, debug=self.debug
            )
            # Extract code properly — strip markdown fences if present
            if "```" in raw:
                m = re.search(r'```(?:python)?\s*(.*?)```', raw, re.DOTALL)
                pandas_code = m.group(1).strip() if m else raw.strip()
            else:
                pandas_code = raw.strip()
            # Also strip any lines that are plain English (not code)
            code_lines = [l for l in pandas_code.splitlines()
                          if l.strip() and not l.strip().startswith("#")
                          or "result" in l or "df" in l]
            if code_lines:
                pandas_code = "\n".join(code_lines)
            dangerous   = ["import os","open(","exec(","eval(","subprocess"]
            if any(d in pandas_code for d in dangerous):
                error_context = "Unsafe code"
                continue
            try:
                scope = {"df": df.copy(), "pd": pd, "np": np,
                         "px": px, "FESTIVAL_CALENDAR": FESTIVAL_CALENDAR}
                exec(pandas_code, {}, scope)
                raw_result = scope.get("result")
                if raw_result is None:
                    error_context = "`result` not set"
                    continue
                result_str = (raw_result.head(20).to_string()
                              if isinstance(raw_result, (pd.DataFrame, pd.Series))
                              else str(raw_result))
                print(f"  ✅ Result: {result_str[:80]}")
                break
            except Exception as e:
                error_context = str(e)
                print(f"  ❌ Error: {e}")

        if raw_result is None:
            return {"question": question, "pandas_query": pandas_code or "Failed",
                    "raw_result": "Could not compute",
                    "answer": "Sorry, could not answer this question with the available data.",
                    "mini_chart": None}

        print("\n[Q&A] Generating plain English answer...")
        plain = self.ollama.generate(
            system_prompt=QA_INTERPRET_SYSTEM_PROMPT,
            user_message=f"QUESTION:\n{question}\n\nDATA RESULT:\n{result_str}\n\nWrite a 4-5 sentence business answer.",
            temperature=0.4, max_tokens=400, debug=self.debug
        )

        # Mini chart
        mini_chart = None
        try:
            if isinstance(raw_result, (pd.DataFrame, pd.Series)):
                cdf = (raw_result.reset_index() if isinstance(raw_result, pd.Series)
                       else raw_result.head(15))
                if isinstance(raw_result, pd.Series):
                    cdf.columns = ["category", "value"]
                if len(cdf) > 1:
                    cols = cdf.columns.tolist()
                    fig  = px.bar(cdf, x=cols[0],
                                  y=cols[1] if len(cols) > 1 else cols[0],
                                  title=question[:60],
                                  color_discrete_sequence=["#0C447C"])
                    fig.update_layout(paper_bgcolor="white", plot_bgcolor="#f8f9fc")
                    mini_chart = json.loads(fig.to_json())
        except Exception:
            pass

        return {"question": question, "pandas_query": pandas_code,
                "raw_result": result_str, "answer": plain.strip(),
                "mini_chart": mini_chart}

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


# ================================================================
# TEST
# ================================================================

if __name__ == "__main__":
    import sys, os

    print("\n" + "="*60)
    print("  LLM ENGINE — TEST")
    print("="*60)

    client = OllamaClient(model="llama3.2")
    if not client.is_running():
        print("❌ Ollama not running. Run: ollama serve")
        sys.exit(1)

    print(f"✅ Ollama running. Models: {client.list_models()}")

    # Load Walmart data
    for path in ["data/walmart.csv", "data/Walmart.csv", "Walmart.csv"]:
        if os.path.exists(path):
            df = pd.read_csv(path)
            df.columns = [c.strip().lower().replace(" ","_") for c in df.columns]
            if "date" in df.columns and df["date"].dtype == object:
                df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
                df["date_year"]    = df["date"].dt.year
                df["date_month"]   = df["date"].dt.month
                df["date_quarter"] = df["date"].dt.quarter
            print(f"✅ Loaded {path}: {df.shape}")
            break
    else:
        print("Walmart CSV not found — using fake data")
        df = pd.DataFrame({
            "date":         pd.date_range("2022-01-01", periods=24, freq="ME"),
            "weekly_sales": [12000,15000,13000,18000,20000,25000,
                             14000,16000,22000,30000,28000,35000,
                             13000,16000,14000,19000,21000,26000,
                             15000,17000,23000,31000,29000,36000],
            "store":        [1,2,3,4]*6,
            "holiday_flag": [0,0,1,0]*6,
        })

    # Build metadata
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols     = df.select_dtypes(include=["object","category"]).columns.tolist()
    date_cols    = df.select_dtypes(include=["datetime64"]).columns.tolist()
    col_lines    = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        nuniq = df[col].nunique()
        line  = f"  - {col} ({dtype}, {nuniq} unique)"
        if col in numeric_cols:
            line += f" | min={df[col].min():.2f}, max={df[col].max():.2f}, mean={df[col].mean():.2f}"
        if col in cat_cols:
            line += f" | top: {df[col].value_counts().head(3).index.tolist()}"
        if col in date_cols:
            line += f" | range: {df[col].min().date()} to {df[col].max().date()}"
        col_lines.append(line)

    metadata = {
        "llm_schema_description": (
            f"Dataset: {len(df):,} rows x {df.shape[1]} columns.\n"
            f"Columns:\n" + "\n".join(col_lines) + "\n"
            f"\nSample: {df.head(1).to_dict(orient='records')[0]}"
        )
    }

    engine = LLMEngine(model="llama3.2", debug=True)

    print("\n--- Test 1: Charts ---")
    try:
        figs = engine.generate_charts(
            "Show total weekly sales by store, sales trend over time, and holiday vs non-holiday comparison",
            df, metadata
        )
        print(f"✅ {len(figs)} charts:")
        for f in figs: print(f"   {f['title']}")
    except Exception as e:
        print(f"❌ {e}")

    print("\n--- Test 2: Q&A ---")
    try:
        qa = engine.answer_question("Which store had highest total sales?", df, metadata)
        print(f"✅ {qa['answer'][:200]}")
    except Exception as e:
        print(f"❌ {e}")

    print("\n--- Test 3: Report ---")
    try:
        rep = engine.generate_report(df, metadata)
        print(f"✅ Report: {len(rep['report_text'])} chars")
        print(rep["report_text"][:400])
    except Exception as e:
        print(f"❌ {e}")