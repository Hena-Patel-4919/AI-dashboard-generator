import io
import sys
import os
import json
import pandas as pd

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.append(os.path.dirname(__file__))

from preprocess_data import DataProcessor
from llm_engine import LLMEngine


# ================================================================
# APP SETUP
# ================================================================

app = FastAPI(
    title="AI Dashboard Generator",
    description="Upload any dataset → generate interactive dashboards using local LLM",
    version="1.0.0"
)

# ── CORS — allows React (port 3000) to talk to FastAPI (port 8000)
# Without this, the browser blocks all requests from React to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",  # React dev server
                   "http://localhost:5173",  # Vite dev server
                   "*"],                     # allow all during development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# SESSION STORE

SESSION = {
    "df":       None,
    "metadata": None,
    "filename": None,
}



# LLM ENGINE initialised once when server starts

# This loads the connection to Ollama once.
# All 4 endpoints share this single engine instance.

print("\n Starting AI Dashboard Generator...")
engine = LLMEngine(model="llama3.2", debug=False)
#creating object of llm class    run cleaner production-style output        
# do not show extra log and errors



# REQUEST MODELS comes form FE


class ChartRequest(BaseModel):
    prompt: str         
class QuestionRequest(BaseModel):
    question: str       


# HELPER   check if data is loaded

def require_data():
   
    if SESSION["df"] is None:
        raise HTTPException(
            status_code=400,
            detail="No dataset uploaded yet. Call POST /upload first."
        )
    return SESSION["df"], SESSION["metadata"]


# ENDPOINT 1 — GET /
# Health check — confirms server is running

@app.get("/")
def root():
    return {
        "status":  "running",
        "message": "AI Dashboard Generator API is live",
        "endpoints": {
            "upload":          "POST /upload",
            "generate_charts": "POST /generate-charts",
            "ask":             "POST /ask",
            "report":          "POST /report",
            "status":          "GET  /status"
        }
    }



# ENDPOINT 2 — GET /status
# Returns what data is currently loaded in memory


@app.get("/status")
def get_status():
    if SESSION["df"] is None:
        return {
            "data_loaded": False,
            "message":     "No dataset loaded. Upload a file first."
        }

    df = SESSION["df"]
    return {
        "data_loaded": True,
        "filename":    SESSION["filename"],
        "rows":        int(df.shape[0]),
        "columns":     int(df.shape[1]),
        "column_names": df.columns.tolist(),
        "message":     f"Dataset '{SESSION['filename']}' is loaded and ready."
    }


# ENDPOINT 3 — POST /upload

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    
    # ── Read file bytes ───────────────────────────────────────
    file_bytes    = await file.read()
    original_name = file.filename

    print(f"\n[Upload] Received file: {original_name} ({len(file_bytes):,} bytes)")

    # ── Validate file type ────────────────────────────────────
    allowed_extensions = [".csv", ".xlsx", ".xls", ".json", ".parquet", ".tsv"]
    file_ext = os.path.splitext(original_name)[1].lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. "
                   f"Allowed: {allowed_extensions}"
        )

    import tempfile
    temp_path = None
    try:
        suffix = os.path.splitext(original_name)[1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file_bytes)
            temp_path = tmp.name
        print(f"[Upload] Temp file: {temp_path}")
        processor        = DataProcessor(file_path=temp_path)
        clean_df, metadata = processor.process()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Data processing failed: {str(e)}"
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
            print("[Upload] Temp file deleted")

    # ── Save to session ───────────────────────────────────────
    SESSION["df"]       = clean_df
    SESSION["metadata"] = metadata
    SESSION["filename"] = original_name

    print(f"[Upload]    Stored in session: {clean_df.shape[0]} rows × {clean_df.shape[1]} cols")

    # ── Build response ────────────────────────────────────────
    # Send back enough info for React to show a preview
    col_info = []
    for col in clean_df.columns:
        col_info.append({
            "name":         col,
            "dtype":        str(clean_df[col].dtype),
            "unique_count": int(clean_df[col].nunique()),
            "null_count":   int(clean_df[col].isnull().sum()),
        })

    # Safe sample — convert timestamps to strings for JSON
    sample_df   = clean_df.head(5).copy()
    for col in sample_df.select_dtypes(include=["datetime64"]).columns:
        sample_df[col] = sample_df[col].astype(str)
    sample_rows = sample_df.to_dict(orient="records")

    return {
        "success":            True,
        "filename":           original_name,
        "rows":               int(clean_df.shape[0]),
        "columns":            int(clean_df.shape[1]),
        "column_info":        col_info,
        "sample_rows":        sample_rows,
        "schema_description": metadata.get("llm_schema_description", ""),
        "cleaning_summary": {
            "duplicates_removed":  metadata.get("duplicate_rows_removed", 0),
            "columns_dropped":     metadata.get("dropped_columns", []),
            "columns_filled":      [c for c, _ in metadata.get("filled_columns", [])],
            "outliers_handled":    list(metadata.get("outliers_handled", {}).keys()),
            "memory_saved_mb":     metadata.get("memory_saved_mb", 0),
        }
    }



# ENDPOINT 4 — POST /generate-charts
# ================================================================
# What frontend sends:  { "prompt": "Show sales by store over time" }
# What this does:
#   1. Reads df + metadata from SESSION
#   2. Passes prompt to LLMEngine.generate_charts()
#   3. LLM writes Plotly code → code executes on real df
#   4. Returns list of Plotly figure JSONs
# What frontend receives: list of chart objects React can render

@app.post("/generate-charts")
def generate_charts(request: ChartRequest):
    
    df, metadata = require_data()

    if not request.prompt or len(request.prompt.strip()) < 3:
        raise HTTPException(
            status_code=400,
            detail="Prompt is too short. Describe what charts you want to see."
        )

    print(f"\n[Charts] Prompt: {request.prompt[:80]}")

    try:
        figures = engine.generate_charts(
            user_prompt=request.prompt,
            df=df,
            metadata=metadata,
            max_retries=2
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chart generation failed: {str(e)}"
        )

    print(f"[Charts]   Returning {len(figures)} charts to frontend")

    return {
        "success":     True,
        "chart_count": len(figures),
        "prompt":      request.prompt,
        "charts":      figures       # List of Plotly figure JSONs
    }


# ================================================================
# ENDPOINT 5 — POST /ask
# ================================================================
# What frontend sends:  { "question": "Which store had highest sales?" }
# What this does:
#   1. Reads df + metadata from SESSION
#   2. LLM writes Pandas query → runs on real df → gets raw result
#   3. LLM interprets result as plain English
#   4. Also generates a mini bar chart if result is tabular
# What frontend receives: answer text + pandas query + mini chart JSON

@app.post("/ask")
def ask_question(request: QuestionRequest):
    

    df, metadata = require_data()

    if not request.question or len(request.question.strip()) < 5:
        raise HTTPException(
            status_code=400,
            detail="Question is too short. Ask a specific business question."
        )

    print(f"\n[Q&A] Question: {request.question}")

    try:
        result = engine.answer_question(
            question=request.question,
            df=df,
            metadata=metadata,
            max_retries=2
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Q&A failed: {str(e)}"
        )

    print(f"[Q&A]  Answer generated")

    return {
        "success":     True,
        "question":    result["question"],
        "answer":      result["answer"],
        "raw_result":  result["raw_result"],
        "pandas_query": result["pandas_query"],
        "mini_chart":  result["mini_chart"]    
    }


# ================================================================
# ENDPOINT 6 — POST /report
# ================================================================
# What frontend sends:  nothing (no body needed)
# What this does:
#   1. Reads df + metadata from SESSION
#   2. Computes data summaries (totals, averages, top categories)
#   3. LLM writes executive report from those summaries
# What frontend receives: full report text + timestamp

@app.post("/report")
def generate_report():
    """
    Generate a full executive business report from the loaded dataset.
    One click — no input needed from user.
    """

    df, metadata = require_data()

    print(f"\n[Report] Generating executive report...")

    try:
        result = engine.generate_report(
            df=df,
            metadata=metadata
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}"
        )

    print(f"[Report] ✅ Report generated ({len(result['report_text'])} chars)")

    return {
        "success":      True,
        "report_text":  result["report_text"],
        "generated_at": result["generated_at"],
        "data_summary": result["data_summary"]
    }


# ================================================================
# ENDPOINT 7 — GET /clear
# Clears the session — user can upload a new file
# ================================================================

@app.get("/clear")
def clear_session():
    SESSION["df"]       = None
    SESSION["metadata"] = None
    SESSION["filename"] = None
    return {
        "success": True,
        "message": "Session cleared. You can now upload a new file."
    }


# ================================================================
# RUN THE SERVER
# ================================================================

if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*60)
    print("  AI DASHBOARD GENERATOR — FASTAPI SERVER")
    print("="*60)
    print("  Server:      http://localhost:8000")
    print("  API Docs:    http://localhost:8000/docs")
    print("  Health:      http://localhost:8000/")
    print("="*60 + "\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False
    )