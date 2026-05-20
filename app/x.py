# Clean Rewritten `x.py`

import os
import json
import webbrowser
from pathlib import Path
from textwrap import dedent

import pandas as pd
import plotly.express as px

from llm_engine import LLMEngine
from preprocess_data import DataProcessor


# ============================================================
# CONFIG
# ============================================================
DATASET_PATH = r"data/Walmart.csv"
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================
# LOAD + CLEAN DATA
# ============================================================
print("\n" + "=" * 60)
print("STARTING DATA PIPELINE")
print("=" * 60)

processor = DataProcessor(DATASET_PATH)
clean_df, metadata = processor.process()

print("✅ Dataset processed")
print(clean_df.head())


# ============================================================
# CONNECT LLM
# ============================================================
print("\n" + "=" * 60)
print("CONNECTING TO LLM")
print("=" * 60)

engine = LLMEngine(model="llama3.2")


# ============================================================
# GENERATE CHARTS
# ============================================================
print("\nGenerating charts...")

charts = []

# ------------------------------------------------------------
# SALES TREND
# ------------------------------------------------------------
if "date" in clean_df.columns and "weekly_sales" in clean_df.columns:

    sales_by_date = (
        clean_df.groupby("date")["weekly_sales"]
        .sum()
        .reset_index()
    )

    fig = px.line(
        sales_by_date,
        x="date",
        y="weekly_sales",
        title="Weekly Sales Trend"
    )

    chart_path = OUTPUT_DIR / "sales_trend.html"
    fig.write_html(chart_path)

    charts.append({
        "title": "Weekly Sales Trend",
        "file": chart_path.name
    })


# ------------------------------------------------------------
# STORE SALES
# ------------------------------------------------------------
if "store" in clean_df.columns and "weekly_sales" in clean_df.columns:

    sales_by_store = (
        clean_df.groupby("store")["weekly_sales"]
        .sum()
        .reset_index()
    )

    fig = px.bar(
        sales_by_store,
        x="store",
        y="weekly_sales",
        title="Sales by Store"
    )

    chart_path = OUTPUT_DIR / "sales_by_store.html"
    fig.write_html(chart_path)

    charts.append({
        "title": "Sales by Store",
        "file": chart_path.name
    })


# ============================================================
# ASK QUESTIONS TO DATASET
# ============================================================
print("\n" + "=" * 60)
print("DATASET Q&A")
print("=" * 60)

sample_question = "Which store has highest sales?"

answer = engine.answer_question(
    df=clean_df,
    question=sample_question,
    metadata=metadata
)

print("\nQuestion:")
print(sample_question)

print("\nAnswer:")
print(answer)


# ============================================================
# GENERATE REPORT
# ============================================================
print("\n" + "=" * 60)
print("GENERATING REPORT")
print("=" * 60)

report = engine.generate_report(
    df=clean_df,
    metadata=metadata
)

# --------------------------------------------------------
# Convert dict → formatted text
# --------------------------------------------------------
if isinstance(report, dict):

    report_text = json.dumps(
        report,
        indent=2,
        ensure_ascii=False
    )

else:
    report_text = str(report)

# --------------------------------------------------------
# Save report
# --------------------------------------------------------
report_path = OUTPUT_DIR / "dataset_report.txt"

with open(report_path, "w", encoding="utf-8") as f:
    f.write(report_text)

print(f"✅ Report saved: {report_path}")


# ============================================================
# BUILD COLUMN TABLE
# ============================================================
col_info = []

for col in clean_df.columns:

    col_info.append({
        "name": col,
        "dtype": str(clean_df[col].dtype),
        "unique_count": clean_df[col].nunique(),
        "null_count": int(clean_df[col].isnull().sum())
    })


rows = []

for c in col_info:

    # dtype badge class
    if "int" in c["dtype"] or "float" in c["dtype"]:
        dtype_class = "dtype-num"

    elif "datetime" in c["dtype"]:
        dtype_class = "dtype-date"

    else:
        dtype_class = "dtype-cat"

    # null display
    if c["null_count"] > 0:
        null_html = (
            f"<span style='color:red'>{c['null_count']}</span>"
        )
    else:
        null_html = "0"

    row_html = dedent(f"""
        <tr>
            <td><b>{c['name']}</b></td>

            <td>
                <span class="dtype-badge {dtype_class}">
                    {c['dtype']}
                </span>
            </td>

            <td>{c['unique_count']:,}</td>

            <td>{null_html}</td>
        </tr>
    """)

    rows.append(row_html)

rows_html = "\n".join(rows)


# ============================================================
# BUILD DASHBOARD HTML
# ============================================================
print("\nBuilding dashboard...")

charts_html = ""

for chart in charts:

    charts_html += f"""
    <div class='chart-card'>
        <h3>{chart['title']}</h3>

        <iframe
            src='{chart['file']}'
            width='100%'
            height='500'
            frameborder='0'>
        </iframe>
    </div>
    """


html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>AI Dashboard</title>

    <style>
        body {{
            font-family: Arial;
            background: #f5f5f5;
            margin: 0;
            padding: 30px;
        }}

        h1 {{
            color: #111;
        }}

        .card {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        th, td {{
            padding: 12px;
            border-bottom: 1px solid #ddd;
            text-align: left;
        }}

        .dtype-badge {{
            padding: 5px 10px;
            border-radius: 6px;
            color: white;
            font-size: 12px;
        }}

        .dtype-num {{
            background: #2563eb;
        }}

        .dtype-date {{
            background: #9333ea;
        }}

        .dtype-cat {{
            background: #16a34a;
        }}

        iframe {{
            border-radius: 10px;
        }}
    </style>
</head>

<body>

    <h1>AI DATASET DASHBOARD</h1>

    <div class='card'>
        <h2>Dataset Summary</h2>

        <p><b>Rows:</b> {clean_df.shape[0]:,}</p>
        <p><b>Columns:</b> {clean_df.shape[1]}</p>
    </div>


    <div class='card'>
        <h2>Columns Information</h2>

        <table>
            <thead>
                <tr>
                    <th>Column</th>
                    <th>Type</th>
                    <th>Unique</th>
                    <th>Nulls</th>
                </tr>
            </thead>

            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>


    <div class='card'>
        <h2>Generated Charts</h2>

        {charts_html}
    </div>


    <div class='card'>
        <h2>AI Generated Report</h2>

        <pre>
{report}
        </pre>
    </div>

</body>
</html>
"""


# ============================================================
# SAVE DASHBOARD
# ============================================================
dashboard_path = OUTPUT_DIR / "dashboard.html"

with open(dashboard_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ Dashboard saved: {dashboard_path}")


# ============================================================
# OPEN IN BROWSER
# ============================================================
webbrowser.open(str(dashboard_path.resolve()))


print("\n" + "=" * 60)
print("PIPELINE COMPLETED")
print("=" * 60)
