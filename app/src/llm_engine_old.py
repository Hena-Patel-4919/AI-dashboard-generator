# # import re
# # import json
# # import requests
# # import pandas as pd
# # import numpy as np
# # from datetime import datetime


# # # ================================================================
# # # FESTIVAL CALENDAR  (2019 – 2026)
# # # Used to help the LLM write festival-impact chart code
# # # ================================================================

# # FESTIVAL_CALENDAR = {
# #     "Diwali":     ["2019-10-27", "2020-11-14", "2021-11-04",
# #                    "2022-10-24", "2023-11-12", "2024-11-01", "2025-10-20"],
# #     "Holi":       ["2019-03-21", "2020-03-10", "2021-03-29",
# #                    "2022-03-18", "2023-03-08", "2024-03-25", "2025-03-14"],
# #     "Eid":        ["2019-06-05", "2020-05-25", "2021-05-14",
# #                    "2022-05-03", "2023-04-22", "2024-04-10", "2025-03-30"],
# #     "Christmas":  ["2019-12-25", "2020-12-25", "2021-12-25",
# #                    "2022-12-25", "2023-12-25", "2024-12-25", "2025-12-25"],
# #     "New Year":   ["2019-01-01", "2020-01-01", "2021-01-01",
# #                    "2022-01-01", "2023-01-01", "2024-01-01", "2025-01-01"],
# #     "Navratri":   ["2019-10-07", "2020-10-17", "2021-10-07",
# #                    "2022-09-26", "2023-10-15", "2024-10-03", "2025-09-22"],
# #     "Durga Puja": ["2019-10-07", "2020-10-22", "2021-10-11",
# #                    "2022-10-02", "2023-10-20", "2024-10-09", "2025-09-28"],
# # }


# # # ================================================================
# # # SYSTEM PROMPTS
# # # ================================================================

# # # --- For chart code generation ---
# # CHART_SYSTEM_PROMPT = """You are an expert data analyst and Python developer.
# # You receive a dataset description and a user request.
# # Your job is to write Python code using Pandas and Plotly Express to create 
# # interactive charts that answer the user's request.

# # STRICT RULES — follow every single one:
# # 1. The DataFrame is already loaded in memory as the variable `df`.
# # 2. Import only: import plotly.express as px  and  import pandas as pd
# # 3. Create 3 to 5 charts. Store each as fig1, fig2, fig3 (etc).
# # 4. Every chart MUST have: a clear title, axis labels, and a color parameter
# #    where it makes sense (color by category, region, product etc).
# # 5. Add hover_data to every chart so hovering shows all relevant columns.
# # 6. For time-series charts use the actual date column — do NOT use year-only
# #    unless the user specifically asks for year-level granularity.
# # 7. The festival calendar is provided as a Python dict called FESTIVAL_CALENDAR.
# #    Use it when the user asks about festival or holiday impact.
# # 8. Do NOT use df.head() or any row limiting — always use the full dataset.
# # 9. Do NOT include plt.show() or fig.show() — just define the fig variables.
# # 10. Do NOT add any explanation, comments, or markdown — ONLY raw Python code.
# # 11. If the user asks about something not possible with this data, 
# #     write a single line: # CANNOT_FULFILL: <reason>

# # AVAILABLE VARIABLES IN SCOPE:
# # - df          : the full cleaned Pandas DataFrame
# # - pd          : pandas
# # - px          : plotly.express
# # - FESTIVAL_CALENDAR : dict of festival name → list of date strings
# # """


# # # --- For Q&A (business questions) step 1: get Pandas query ---
# # QA_QUERY_SYSTEM_PROMPT = """You are an expert data analyst.
# # You receive a dataset description and a business question.
# # Write a single Python expression using Pandas that answers the question.
# # The DataFrame is called `df`.

# # STRICT RULES:
# # 1. Return ONLY one Python expression — nothing else, no explanation.
# # 2. The result must be a scalar (number or string) or a small Pandas 
# #    Series/DataFrame (max 20 rows).
# # 3. Do not use df.head() or limit rows unless the question asks for top N.
# # 4. Store the result in a variable called `result`.
# # 5. Example output format:
# #    result = df.groupby('region')['sales'].sum().idxmax()
# # """


# # # --- For Q&A step 2: interpret the query result as plain English ---
# # QA_INTERPRET_SYSTEM_PROMPT = """You are a senior business analyst.
# # You receive:
# #   - A business question asked by the user
# #   - The raw data result that answers it (a number, string, or table)

# # Write a clear, concise 5-6 sentence business answer in plain English.
# # Use actual numbers from the result. Be specific.
# # Do NOT say "based on the data" or "according to the analysis" — just state the finding directly.
# # """


# # # --- For report / summary generation ---
# # REPORT_SYSTEM_PROMPT = """You are a senior business analyst writing an executive report.
# # You receive summaries of charts from an interactive dashboard.

# # Write a structured business report with these exact sections:
# # 1. EXECUTIVE SUMMARY     (3–4 sentences, big picture)
# # 2. KEY FINDINGS          (5 bullet points, each with a specific number)
# # 3. TOP PERFORMERS        (best store / product / region — with numbers)
# # 4. AREAS OF CONCERN      (worst performers or declining trends — with numbers)
# # 5. FESTIVAL IMPACT       (only if festival data is present, else skip)
# # 6. RECOMMENDATIONS       (3 actionable bullet points for management)

# # RULES:
# # - Use actual numbers from the chart summaries provided.
# # - Keep each section tight — no fluff, no generic statements.
# # - Write for a non-technical business audience (no code, no jargon).
# # - Total length: 300–450 words.
# # """


# # # ================================================================
# # # OLLAMA CLIENT
# # # ================================================================

# # class OllamaClient:
# #     """
# #     Thin wrapper around the Ollama local API.
# #     """

# #     def __init__(self, model: str = "llama3.2", base_url: str = "http://localhost:11434"):
# #         self.model = model
# #         self.base_url = base_url.rstrip("/")

# #     # ----------------------------------------------------------------
# #     # Check Ollama is running
# #     # ----------------------------------------------------------------
# #     def is_running(self) -> bool:
# #         try:
# #             r = requests.get(f"{self.base_url}/api/tags", timeout=3)
# #             return r.status_code == 200
# #         except Exception:
# #             return False

# #     # ----------------------------------------------------------------
# #     # Generate response from Ollama
# #     # ----------------------------------------------------------------
# #     def generate(
# #         self,
# #         system_prompt: str,
# #         user_message: str,
# #         temperature: float = 0.2,
# #         max_tokens: int = 2048
# #     ) -> str:

# #         """
# #         Sends prompts to Ollama using generate API.
# #         """

# #         if not self.is_running():
# #             raise ConnectionError(
# #                 "Ollama is not running. Start it with: ollama serve"
# #             )

# #         try:

# #             import ollama

# #             full_prompt = f"""
# # SYSTEM:
# # {system_prompt}

# # USER:
# # {user_message}
# # """

# #             response = ollama.generate(
# #                 model=self.model,
# #                 prompt=full_prompt,
# #                 options={
# #                     "temperature": temperature,
# #                     "num_predict": max_tokens
# #                 }
# #             )

# #             print("MODEL =", self.model)
# #             print("OLLAMA RESPONSE RECEIVED")

# #             return response["response"].strip()

# #         except Exception as e:

# #             raise ConnectionError(
# #                 f"Ollama request failed: {e}"
# #             )
    
# # def generate(
# #         self,
# #         system_prompt: str,
# #         user_message: str,
# #         temperature: float = 0.2,
# #         max_tokens: int = 2048
# #     ) -> str:

# #         """
# #         Sends prompts to Ollama using generate API.
# #         """

# #         if not self.is_running():
# #             raise ConnectionError(
# #                 "Ollama is not running. Start it with: ollama serve"
# #             )

# #         try:

# #             import ollama

# #             full_prompt = f"""
# # SYSTEM:
# # {system_prompt}

# # USER:
# # {user_message}
# # """

# #             response = ollama.generate(
# #                 model=self.model,
# #                 prompt=full_prompt,
# #                 options={
# #                     "temperature": temperature,
# #                     "num_predict": max_tokens
# #                 }
# #             )

# #             print("MODEL =", self.model)
# #             print("OLLAMA RESPONSE RECEIVED")

# #             return response["response"].strip()

# #         except Exception as e:

# #             raise ConnectionError(
# #                 f"Ollama request failed: {e}"
# #             )
# # # ================================================================
# # # CODE EXTRACTOR
# # # ================================================================

# # def extract_code(llm_response: str) -> str:
# #     """
# #     Cleans the LLM response and returns only raw Python code.

# #     Handles these common LLM output patterns:
# #       ```python ... ```   ← most common
# #       ``` ... ```         ← without language tag
# #       Plain code          ← already clean
# #     """
# #     # Pattern 1: ```python ... ```
# #     match = re.search(r'```python\s*(.*?)```', llm_response, re.DOTALL)
# #     if match:
# #         return match.group(1).strip()

# #     # Pattern 2: ``` ... ```
# #     match = re.search(r'```\s*(.*?)```', llm_response, re.DOTALL)
# #     if match:
# #         return match.group(1).strip()

# #     # Pattern 3: already raw code — return as-is
# #     return llm_response.strip()


# # def is_valid_chart_code(code: str) -> tuple[bool, str]:
# #     """
# #     Basic sanity check on LLM-generated chart code.
# #     Returns (is_valid, reason_if_invalid).
# #     """
# #     if not code or len(code) < 20:
# #         return False, "Response is too short to be valid code"

# #     if code.startswith("# CANNOT_FULFILL"):
# #         reason = code.replace("# CANNOT_FULFILL:", "").strip()
# #         return False, f"LLM says cannot fulfill: {reason}"

# #     if "px." not in code and "plotly" not in code:
# #         return False, "No Plotly code found in response"

# #     if "fig" not in code:
# #         return False, "No figure variable (fig1/fig2 etc.) found"

# #     # Check for dangerous operations (security)
# #     dangerous = ["import os", "import sys", "open(", "exec(", "eval(",
# #                  "__import__", "subprocess", "shutil", "rmdir", "remove("]
# #     for danger in dangerous:
# #         if danger in code:
# #             return False, f"Unsafe operation detected: {danger}"

# #     return True, "OK"


# # # ================================================================
# # # CODE EXECUTOR
# # # ================================================================

# # def execute_chart_code(code: str, df: pd.DataFrame) -> list:
# #     """
# #     Safely executes LLM-generated Plotly code.
# #     Returns a list of Plotly figure JSON dicts.

# #     The code runs in a restricted local scope that only has:
# #       - df             : the clean DataFrame
# #       - pd             : pandas
# #       - px             : plotly.express
# #       - np             : numpy
# #       - FESTIVAL_CALENDAR : the festival dates dict

# #     Returns list of dicts:
# #       [{"title": "...", "figure_json": {...}}, ...]
# #     """
# #     import plotly.express as px

# #     local_scope = {
# #         "df":                df.copy(),
# #         "pd":                pd,
# #         "px":                px,
# #         "np":                np,
# #         "FESTIVAL_CALENDAR": FESTIVAL_CALENDAR,
# #     }

# #     try:
# #         exec(code, {}, local_scope)
# #     except Exception as e:
# #         raise RuntimeError(f"Code execution error: {e}\n\nCode was:\n{code}")

# #     # Collect all fig1, fig2, fig3 ... variables
# #     figures = []
# #     for key in sorted(local_scope.keys()):
# #         if re.match(r'^fig\d*$', key):
# #             fig = local_scope[key]
# #             try:
# #                 figures.append({
# #                     "title":       fig.layout.title.text or key,
# #                     "figure_json": json.loads(fig.to_json())
# #                 })
# #             except Exception as e:
# #                 print(f"Warning: could not serialize {key}: {e}")

# #     return figures


# # # ================================================================
# # # CHART DATA SUMMARIZER  (feeds into report generator)
# # # ================================================================

# # def summarize_chart_data(df: pd.DataFrame, metadata: dict) -> str:
# #     """
# #     Computes text summaries of the key data in the DataFrame.
# #     This is passed to the LLM for report generation —
# #     we never send raw rows, only computed summaries.
# #     """
# #     lines = []
# #     numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
# #     cat_cols     = df.select_dtypes(include=['object', 'category']).columns.tolist()
# #     date_cols    = df.select_dtypes(include=['datetime64']).columns.tolist()

# #     lines.append(f"Dataset: {len(df):,} rows, {df.shape[1]} columns")

# #     # Overall numeric totals
# #     for col in numeric_cols[:5]:    # top 5 numeric columns
# #         lines.append(
# #             f"{col}: total={df[col].sum():,.2f}, "
# #             f"avg={df[col].mean():,.2f}, "
# #             f"max={df[col].max():,.2f}, "
# #             f"min={df[col].min():,.2f}"
# #         )

# #     # Category breakdowns
# #     for col in cat_cols[:3]:        # top 3 category columns
# #         top = df[col].value_counts().head(5)
# #         lines.append(f"\nTop values in '{col}':")
# #         for val, cnt in top.items():
# #             lines.append(f"  {val}: {cnt:,} rows")

# #     # Date range
# #     for col in date_cols[:1]:
# #         lines.append(
# #             f"\nDate range: {df[col].min().date()} to {df[col].max().date()}"
# #         )

# #     # Cross-tab: if we have a date + numeric column, show year-wise totals
# #     if date_cols and numeric_cols:
# #         date_col = date_cols[0]
# #         num_col  = numeric_cols[0]
# #         year_col = f"{date_col}_year"
# #         if year_col in df.columns:
# #             yearly = df.groupby(year_col)[num_col].sum()
# #             lines.append(f"\nYear-wise {num_col} totals:")
# #             for yr, total in yearly.items():
# #                 lines.append(f"  {int(yr)}: {total:,.2f}")

# #     return "\n".join(lines)


# # # ================================================================
# # # MAIN LLM ENGINE CLASS
# # # ================================================================

# # class LLMEngine:
# #     """
# #     The brain of the dashboard system.

# #     Three modes:
# #       1. generate_charts(prompt, df, metadata)   → list of Plotly figures
# #       2. answer_question(question, df, metadata) → plain English answer string
# #       3. generate_report(df, metadata)           → full business report string

# #     All three use the same local llama3.2 model via Ollama.
# #     No API keys, no cost, runs fully offline after model download.
# #     """

# #     def __init__(self, model: str = "llama3.2"):

# #         print("INIT MODEL =", model)

# #         self.ollama = OllamaClient(model=model)

# #         self._check_connection()
# #     def _check_connection(self):
# #         if not self.ollama.is_running():
# #             print(
# #                 "\n⚠️  WARNING: Ollama is not running.\n"
# #                 "   Start it with: ollama serve\n"
# #                 "   Then pull a model: ollama pull llama3.2\n"
# #             )
# #         else:
# #             print(f"✅ Ollama connected — model: {self.ollama.model}")

# #     # ----------------------------------------------------------------
# #     # Build the user message sent to LLM (metadata + prompt)
# #     # ----------------------------------------------------------------
# #     def _build_chart_user_message(self, user_prompt: str, metadata: dict) -> str:
# #         schema = metadata.get("llm_schema_description", "No schema available")
# #         festival_str = json.dumps(FESTIVAL_CALENDAR, indent=2)

# #         return f"""DATASET SCHEMA:
# # {schema}

# # FESTIVAL CALENDAR (use this for festival-impact analysis):
# # {festival_str}

# # USER REQUEST:
# # {user_prompt}

# # Write Python code for 3–5 interactive Plotly charts that best answer this request.
# # Remember: only raw Python code, no explanation, no markdown backticks.
# # """

# #     # ----------------------------------------------------------------
# #     # MODE 1 — CHART GENERATION
# #     # ----------------------------------------------------------------
# #     def generate_charts(self, user_prompt: str, df: pd.DataFrame,
# #                         metadata: dict, max_retries: int = 2) -> list:
# #         """
# #         Sends metadata + prompt to LLM → gets Plotly code →
# #         executes code on real df → returns list of figure JSONs.

# #         Retries automatically if:
# #           - LLM returns text instead of code
# #           - Generated code has a syntax error
# #           - Generated code crashes during execution

# #         Returns:
# #           List of dicts: [{"title": str, "figure_json": dict}, ...]
# #         """
# #         user_message  = self._build_chart_user_message(user_prompt, metadata)
# #         last_error    = None
# #         error_context = ""

# #         for attempt in range(1, max_retries + 2):  # attempts: 1, 2, 3

# #             print(f"\n[Chart Generation] Attempt {attempt}...")

# #             # If retrying after an error, add the error to the prompt
# #             retry_suffix = ""
# #             if error_context:
# #                 retry_suffix = f"""

# # PREVIOUS ATTEMPT FAILED WITH THIS ERROR:
# # {error_context}

# # Fix the error and return corrected Python code only.
# # """

# #             # Call the LLM
# #             raw_response = self.ollama.generate(
# #                 system_prompt=CHART_SYSTEM_PROMPT,
# #                 user_message=user_message + retry_suffix,
# #                 temperature=0.1,    # very low — we want consistent code
# #                 max_tokens=2048
# #             )

# #             # Extract code
# #             code = extract_code(raw_response)

# #             # Validate
# #             is_valid, reason = is_valid_chart_code(code)
# #             if not is_valid:
# #                 error_context = reason
# #                 last_error    = reason
# #                 print(f"  Validation failed: {reason}")
# #                 continue

# #             # Execute
# #             try:
# #                 figures = execute_chart_code(code, df)
# #                 if not figures:
# #                     error_context = "Code ran but produced no figures. Make sure figures are named fig1, fig2 etc."
# #                     continue
# #                 print(f"  ✅ Generated {len(figures)} charts successfully")
# #                 return figures

# #             except RuntimeError as e:
# #                 error_context = str(e)
# #                 last_error    = str(e)
# #                 print(f"  Execution error: {e}")

# #         # All attempts exhausted
# #         raise RuntimeError(
# #             f"Chart generation failed after {max_retries + 1} attempts.\n"
# #             f"Last error: {last_error}"
# #         )

# #     # ----------------------------------------------------------------
# #     # MODE 2 — BUSINESS Q&A  (2-step chain)
# #     # ----------------------------------------------------------------
# #     def answer_question(self, question: str, df: pd.DataFrame,
# #                         metadata: dict, max_retries: int = 2) -> dict:
# #         """
# #         Step 1: LLM writes a Pandas expression to answer the question.
# #         Step 2: We run it on df to get the raw result.
# #         Step 3: LLM interprets the raw result as a plain English answer.

# #         Returns:
# #           {
# #             "question":      str,
# #             "pandas_query":  str,    ← the code that ran
# #             "raw_result":    str,    ← the data result
# #             "answer":        str,    ← plain English answer
# #             "mini_chart":    dict|None  ← optional small chart JSON
# #           }
# #         """
# #         schema = metadata.get("llm_schema_description", "")

# #         # ---- STEP 1: Get Pandas query from LLM ----
# #         query_message = f"""DATASET SCHEMA:
# # {schema}

# # BUSINESS QUESTION:
# # {question}

# # Write ONE Python expression. Store the result in a variable called `result`.
# # Return ONLY the Python code — nothing else.
# # """
# #         pandas_code   = None
# #         raw_result    = None
# #         error_context = ""

# #         for attempt in range(1, max_retries + 2):
# #             print(f"\n[Q&A Step 1] Attempt {attempt} — getting Pandas query...")

# #             retry_suffix = f"\nPREVIOUS ERROR: {error_context}\nFix and return only code." if error_context else ""

# #             raw_response = self.ollama.generate(
# #                 system_prompt=QA_QUERY_SYSTEM_PROMPT,
# #                 user_message=query_message + retry_suffix,
# #                 temperature=0.1,
# #                 max_tokens=512
# #             )

# #             pandas_code = extract_code(raw_response)

# #             # Security check
# #             _, reason = is_valid_chart_code(pandas_code)   # reuse security check
# #             dangerous  = ["import os", "open(", "exec(", "eval(", "subprocess"]
# #             if any(d in pandas_code for d in dangerous):
# #                 error_context = f"Unsafe code: {pandas_code[:100]}"
# #                 continue

# #             # Execute the Pandas query
# #             try:
# #                 import plotly.express as px
# #                 local_scope = {
# #                     "df": df.copy(), "pd": pd, "np": np,
# #                     "px": px, "FESTIVAL_CALENDAR": FESTIVAL_CALENDAR
# #                 }
# #                 exec(pandas_code, {}, local_scope)
# #                 raw_result = local_scope.get("result", None)

# #                 if raw_result is None:
# #                     error_context = "Variable `result` not found after running code."
# #                     continue

# #                 # Convert result to a readable string
# #                 if isinstance(raw_result, pd.DataFrame):
# #                     result_str = raw_result.head(20).to_string()
# #                 elif isinstance(raw_result, pd.Series):
# #                     result_str = raw_result.head(20).to_string()
# #                 else:
# #                     result_str = str(raw_result)

# #                 print(f"  ✅ Query ran. Result preview: {result_str[:100]}")
# #                 break

# #             except Exception as e:
# #                 error_context = str(e)
# #                 print(f"  Query execution error: {e}")
# #                 raw_result = None
        
# #         if raw_result is None:
# #             return {
# #                 "question":     question,
# #                 "pandas_query": pandas_code or "Failed to generate",
# #                 "raw_result":   "Could not compute",
# #                 "answer":       "Sorry, I could not compute an answer for this question with the available data.",
# #                 "mini_chart":   None
# #             }

# #         # ---- STEP 2: Interpret result as plain English ----
# #         print("\n[Q&A Step 2] Interpreting result...")

# #         interpret_message = f"""BUSINESS QUESTION:
# # {question}

# # DATA RESULT:
# # {result_str}

# # Write a 2–3 sentence plain English business answer. Use the actual numbers.
# # """
# #         plain_answer = self.ollama.generate(
# #             system_prompt=QA_INTERPRET_SYSTEM_PROMPT,
# #             user_message=interpret_message,
# #             temperature=0.4,    # slightly higher — natural language
# #             max_tokens=300
# #         )

# #         # ---- STEP 3: Try to generate a mini chart for the result ----
# #         mini_chart = None
# #         try:
# #             if isinstance(raw_result, (pd.DataFrame, pd.Series)):
# #                 import plotly.express as px
# #                 if isinstance(raw_result, pd.Series):
# #                     chart_df = raw_result.reset_index()
# #                     chart_df.columns = ["category", "value"]
# #                 else:
# #                     chart_df = raw_result.head(15)

# #                 if len(chart_df) > 1:
# #                     cols = chart_df.columns.tolist()
# #                     fig  = px.bar(
# #                         chart_df,
# #                         x=cols[0],
# #                         y=cols[1] if len(cols) > 1 else cols[0],
# #                         title=f"Answer: {question[:60]}",
# #                     )
# #                     mini_chart = json.loads(fig.to_json())
# #         except Exception as e:
# #             print(f"  Mini chart skipped: {e}")

# #         return {
# #             "question":     question,
# #             "pandas_query": pandas_code,
# #             "raw_result":   result_str,
# #             "answer":       plain_answer.strip(),
# #             "mini_chart":   mini_chart
# #         }

# #     # ----------------------------------------------------------------
# #     # MODE 3 — REPORT GENERATION
# #     # ----------------------------------------------------------------
# #     def generate_report(self, df: pd.DataFrame, metadata: dict) -> dict:
# #         """
# #         Generates a full executive business report from the dashboard data.

# #         Step 1: Compute chart summaries (no raw rows sent to LLM).
# #         Step 2: LLM writes the report.

# #         Returns:
# #           {
# #             "report_text":    str,   ← full formatted report
# #             "generated_at":   str,   ← timestamp
# #             "data_summary":   str    ← the summary that was sent to LLM
# #           }
# #         """
# #         print("\n[Report Generation] Computing data summaries...")
# #         data_summary = summarize_chart_data(df, metadata)

# #         report_message = f"""DASHBOARD DATA SUMMARY:
# # {data_summary}

# # DATASET SCHEMA (for context):
# # {metadata.get('llm_schema_description', '')[:1000]}

# # Write the executive business report now.
# # """
# #         print("[Report Generation] Calling LLM...")
# #         report_text = self.ollama.generate(
# #             system_prompt=REPORT_SYSTEM_PROMPT,
# #             user_message=report_message,
# #             temperature=0.5,    # more creative for report writing
# #             max_tokens=1500
# #         )

# #         return {
# #             "report_text":  report_text.strip(),
# #             "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
# #             "data_summary": data_summary
# #         }


# # # ================================================================
# # # QUICK TEST — run this file directly to verify everything works
# # # ================================================================

# # if __name__ == "__main__":

# #     print("\n" + "="*60)
# #     print("  LLM ENGINE — CONNECTION TEST")
# #     print("="*60)

# #     # Step 1: Check Ollama
# #     client = OllamaClient(model="llama3.2")
# #     if not client.is_running():
# #         print("\n Ollama is NOT running.")
# #         print("   Fix: open a terminal and run:  ollama serve")
# #         print("   Then pull model:               ollama pull llama3.2")
# #         exit(1)

# #     print("\n Ollama is running")

# #     # Step 2: Test simple generation
# #     print("\n--- Testing basic LLM call ---")
# #     response = client.generate(
# #         system_prompt="You are a helpful assistant.",
# #         user_message="Say hello in exactly 5 words.",
# #         temperature=0.5,
# #         max_tokens=50
# #     )
# #     print(f"LLM response: {response}")

# #     # Step 3: Test with a small fake DataFrame
# #     print("\n--- Testing chart generation with fake retail data ---")

# #     import plotly.express as px

# #     fake_df = pd.DataFrame({
# #         "date":     pd.date_range("2022-01-01", periods=24, freq="ME"),
# #         "sales":    [12000, 15000, 13000, 18000, 20000, 25000,
# #                      14000, 16000, 22000, 30000, 28000, 35000,
# #                      13000, 16000, 14000, 19000, 21000, 26000,
# #                      15000, 17000, 23000, 31000, 29000, 36000],
# #         "region":   ["North","South","East","West"] * 6,
# #         "product":  ["Electronics","Clothing","Food","Electronics"] * 6,
# #     })
# #     fake_df["date_year"]    = fake_df["date"].dt.year
# #     fake_df["date_month"]   = fake_df["date"].dt.month
# #     fake_df["date_quarter"] = fake_df["date"].dt.quarter

# #     fake_metadata = {
# #         "llm_schema_description": (
# #             "Dataset: 24 rows × 4 columns.\n"
# #             "Columns:\n"
# #             "  - date (datetime64, 24 unique) | range: 2022-01-31 to 2023-12-31\n"
# #             "  - sales (float64, 20 unique) | min=12000, max=36000, mean=21083\n"
# #             "  - region (category, 4 unique) | top values: ['North','South','East','West']\n"
# #             "  - product (category, 3 unique) | top values: ['Electronics','Clothing','Food']"
# #         )
# #     }

# #     engine = LLMEngine(model="llama3.2")

# #     # Test chart generation
# #     try:
# #         figures = engine.generate_charts(
# #             user_prompt="Show monthly sales trend and sales by region and product",
# #             df=fake_df,
# #             metadata=fake_metadata
# #         )
# #         print(f"\n Chart generation: {len(figures)} charts produced")
# #         for fig in figures:
# #             print(f"   - {fig['title']}")
# #     except Exception as e:
# #         print(f"\n Chart generation failed: {e}")

# #     # Test Q&A
# #     try:
# #         qa_result = engine.answer_question(
# #             question="Which region had the highest total sales?",
# #             df=fake_df,
# #             metadata=fake_metadata
# #         )
# #         print(f"\n Q&A answer:\n   {qa_result['answer']}")
# #     except Exception as e:

# #         print(f"\n Q&A failed: {e}")

# #     # Test report
# #     try:
# #         report = engine.generate_report(fake_df, fake_metadata)
# #         print(f"\n Report generated ({len(report['report_text'])} chars)")
# #         print("\n--- REPORT PREVIEW ---")
# #         print(report["report_text"][:500] + "...")
# #     except Exception as e:
# #         print(f"\n Report generation failed: {e}")




# import re
# import json
# import requests
# import pandas as pd
# import numpy as np
# from datetime import datetime
# import plotly.express as px
# import plotly.graph_objects as go
# from plotly.subplots import make_subplots


# # ================================================================
# # FESTIVAL CALENDAR  (2019 – 2026)
# # ================================================================

# FESTIVAL_CALENDAR = {
#     "Diwali":     ["2019-10-27", "2020-11-14", "2021-11-04",
#                    "2022-10-24", "2023-11-12", "2024-11-01", "2025-10-20"],
#     "Holi":       ["2019-03-21", "2020-03-10", "2021-03-29",
#                    "2022-03-18", "2023-03-08", "2024-03-25", "2025-03-14"],
#     "Eid":        ["2019-06-05", "2020-05-25", "2021-05-14",
#                    "2022-05-03", "2023-04-22", "2024-04-10", "2025-03-30"],
#     "Christmas":  ["2019-12-25", "2020-12-25", "2021-12-25",
#                    "2022-12-25", "2023-12-25", "2024-12-25", "2025-12-25"],
#     "New Year":   ["2019-01-01", "2020-01-01", "2021-01-01",
#                    "2022-01-01", "2023-01-01", "2024-01-01", "2025-01-01"],
#     "Navratri":   ["2019-10-07", "2020-10-17", "2021-10-07",
#                    "2022-09-26", "2023-10-15", "2024-10-03", "2025-09-22"],
#     "Durga Puja": ["2019-10-07", "2020-10-22", "2021-10-11",
#                    "2022-10-02", "2023-10-20", "2024-10-09", "2025-09-28"],
# }


# # ================================================================
# # SYSTEM PROMPTS  (LLM only used for Q&A and Report now)
# # ================================================================

# QA_QUERY_SYSTEM_PROMPT = """You are an expert data analyst.
# Given a dataset schema and a business question, write ONE Pandas expression.
# DataFrame is called `df`. Store result in variable called `result`.
# RULES:
# 1. Return ONLY the Python code — nothing else, no explanation.
# 2. Result must be a scalar, string, or small Series/DataFrame (max 20 rows).
# 3. Example: result = df.groupby('region')['sales'].sum().idxmax()
# """

# QA_INTERPRET_SYSTEM_PROMPT = """You are a senior business analyst.
# You receive a business question and the raw data result.
# Write a clear 4-5 sentence answer in plain English using actual numbers.
# Do not say 'based on the data' — state findings directly.
# """

# REPORT_SYSTEM_PROMPT = """You are a senior business analyst writing an executive report.
# You receive a dashboard data summary.
# Write a structured report with:
# 1. EXECUTIVE SUMMARY     (3-4 sentences)
# 2. KEY FINDINGS          (5 bullet points with specific numbers)
# 3. TOP PERFORMERS        (best performers with numbers)
# 4. AREAS OF CONCERN      (worst performers with numbers)
# 5. FESTIVAL IMPACT       (skip if no festival data)
# 6. RECOMMENDATIONS       (3 actionable bullet points)
# Use actual numbers. No fluff. 300-450 words total.
# """

# # Chart planner prompt — LLM only decides WHAT to show, not HOW to code it
# CHART_PLANNER_PROMPT = """You are a data analyst deciding what charts to show.
# You receive a dataset schema and a user request.
# Respond with a JSON array of chart specifications. Each item has:
#   - "chart_type": one of "bar", "line", "box", "scatter", "pie", "histogram"
#   - "title": a clear descriptive title
#   - "x_col": exact column name for x axis (must exist in schema)
#   - "y_col": exact column name for y axis (must exist in schema)
#   - "color_col": column to color by (optional, use null if not needed)
#   - "agg": aggregation method — "sum", "mean", "count", or "none"
#   - "group_by": column to group/aggregate by (same as x_col usually)
#   - "top_n": integer, limit to top N categories (use 20 for stores, 10 for others, null for time series)
#   - "sort": "desc" or "asc" or null

# RULES:
# - Return ONLY valid JSON array — no explanation, no markdown.
# - Use ONLY column names that exist in the schema.
# - For time series: x_col = date column, agg = "sum", group_by = date column, top_n = null
# - For category bars: group_by = category column, agg = "sum" or "mean"
# - Suggest 3 charts maximum.

# Example output:
# [
#   {"chart_type": "bar", "title": "Total Sales by Store", "x_col": "store", "y_col": "weekly_sales", "color_col": "store", "agg": "sum", "group_by": "store", "top_n": 20, "sort": "desc"},
#   {"chart_type": "line", "title": "Weekly Sales Trend", "x_col": "date", "y_col": "weekly_sales", "color_col": null, "agg": "sum", "group_by": "date", "top_n": null, "sort": null},
#   {"chart_type": "box", "title": "Holiday vs Non-Holiday Sales", "x_col": "holiday_flag", "y_col": "weekly_sales", "color_col": "holiday_flag", "agg": "none", "group_by": null, "top_n": null, "sort": null}
# ]
# """


# # ================================================================
# # OLLAMA CLIENT
# # ================================================================

# class OllamaClient:

#     def __init__(self, model="llama3.2", base_url="http://localhost:11434"):
#         self.model    = model
#         self.base_url = base_url.rstrip("/")

#     def is_running(self):
#         try:
#             r = requests.get(f"{self.base_url}/api/tags", timeout=3)
#             return r.status_code == 200
#         except Exception:
#             return False

#     def list_models(self):
#         try:
#             r = requests.get(f"{self.base_url}/api/tags", timeout=3)
#             if r.status_code == 200:
#                 return [m["name"] for m in r.json().get("models", [])]
#         except Exception:
#             pass
#         return []

#     def generate(self, system_prompt, user_message,
#                  temperature=0.2, max_tokens=2048, debug=False):
#         if not self.is_running():
#             raise ConnectionError("Ollama not running. Run: ollama serve")
#         try:
#             import ollama
#             full_prompt = f"SYSTEM:\n{system_prompt}\n\nUSER:\n{user_message}"
#             response    = ollama.generate(
#                 model=self.model,
#                 prompt=full_prompt,
#                 options={"temperature": temperature, "num_predict": max_tokens}
#             )
#             result = response["response"].strip()
#             if debug:
#                 print(f"\n[DEBUG] {self.model} response ({len(result)} chars):")
#                 print(result[:600])
#             return result
#         except ImportError:
#             raise ImportError("Run: pip install ollama")
#         except Exception as e:
#             raise ConnectionError(f"Ollama failed: {e}")


# # ================================================================
# # CHART BUILDER  — Pure Python, always correct charts
# # ================================================================

# class ChartBuilder:
#     """
#     Builds Plotly charts purely in Python from a chart specification.
#     No LLM involved in the actual chart code — 100% reliable output.
#     """

#     # Plotly colour palette
#     COLORS = px.colors.qualitative.Set2

#     @staticmethod
#     def _prepare_data(df, spec):
#         """Aggregate data according to the spec before plotting."""
#         x_col    = spec["x_col"]
#         y_col    = spec["y_col"]
#         agg      = spec.get("agg", "sum")
#         group_by = spec.get("group_by")
#         top_n    = spec.get("top_n")
#         sort     = spec.get("sort", "desc")

#         if agg == "none" or not group_by:
#             plot_df = df[[c for c in [x_col, y_col,
#                           spec.get("color_col")] if c and c in df.columns]].copy()
#         else:
#             if agg == "sum":
#                 plot_df = df.groupby(group_by)[y_col].sum().reset_index()
#             elif agg == "mean":
#                 plot_df = df.groupby(group_by)[y_col].mean().reset_index()
#             elif agg == "count":
#                 plot_df = df.groupby(group_by)[y_col].count().reset_index()
#             else:
#                 plot_df = df.groupby(group_by)[y_col].sum().reset_index()

#             if sort == "desc":
#                 plot_df = plot_df.sort_values(y_col, ascending=False)
#             elif sort == "asc":
#                 plot_df = plot_df.sort_values(y_col, ascending=True)

#             if top_n:
#                 plot_df = plot_df.head(int(top_n))

#         # Cast x to string for categorical axes to prevent numeric scaling
#         if x_col in plot_df.columns and agg != "none":
#             unique_count = plot_df[x_col].nunique()
#             if unique_count < 100:
#                 plot_df[x_col] = plot_df[x_col].astype(str)

#         return plot_df

#     @staticmethod
#     def _format_value(val):
#         """Format large numbers cleanly for hover labels."""
#         if isinstance(val, (int, float)):
#             if abs(val) >= 1_000_000_000:
#                 return f"${val/1_000_000_000:.2f}B"
#             elif abs(val) >= 1_000_000:
#                 return f"${val/1_000_000:.2f}M"
#             elif abs(val) >= 1_000:
#                 return f"${val/1_000:.1f}K"
#         return str(val)

#     @staticmethod
#     def _apply_layout(fig, title):
#         """Apply a clean, professional layout to every chart."""
#         fig.update_layout(
#             title=dict(text=title, font=dict(size=16, color="#1a1a2e"), x=0.02),
#             paper_bgcolor="white",
#             plot_bgcolor="#f8f9fc",
#             font=dict(family="'Segoe UI', Arial, sans-serif", size=12,
#                       color="#444"),
#             hoverlabel=dict(bgcolor="#1a1a2e", font_color="white",
#                             font_size=12, bordercolor="#1a1a2e"),
#             hovermode="closest",
#             legend=dict(bgcolor="rgba(255,255,255,0.9)",
#                         bordercolor="#e0e0e0", borderwidth=1),
#             margin=dict(l=60, r=30, t=60, b=60),
#             xaxis=dict(gridcolor="#eef0f4", showgrid=True,
#                        zeroline=False, linecolor="#ddd"),
#             yaxis=dict(gridcolor="#eef0f4", showgrid=True,
#                        zeroline=False, linecolor="#ddd"),
#         )
#         return fig

#     def build(self, df, spec):
#         """Build one Plotly figure from a spec dict. Always returns a valid figure."""
#         chart_type = spec.get("chart_type", "bar")
#         title      = spec.get("title", "Chart")
#         x_col      = spec["x_col"]
#         y_col      = spec["y_col"]
#         color_col  = spec.get("color_col")

#         # Validate columns exist
#         for col in [x_col, y_col]:
#             if col not in df.columns:
#                 # Return an empty placeholder figure instead of crashing
#                 fig = go.Figure()
#                 fig.update_layout(title=f"⚠️ Column '{col}' not found in data")
#                 return {"title": title, "figure_json": json.loads(fig.to_json())}

#         plot_df = self._prepare_data(df, spec)

#         try:
#             if chart_type == "bar":
#                 color_arg = color_col if color_col and color_col in plot_df.columns else x_col
#                 fig = px.bar(
#                     plot_df, x=x_col, y=y_col,
#                     color=color_arg if color_arg in plot_df.columns else None,
#                     title=title,
#                     color_discrete_sequence=self.COLORS,
#                     hover_data={c: True for c in plot_df.columns},
#                     text_auto=".2s"
#                 )
#                 fig.update_traces(textposition="outside",
#                                   marker_line_width=0)

#             elif chart_type == "line":
#                 color_arg = color_col if color_col and color_col in plot_df.columns else None
#                 fig = px.line(
#                     plot_df, x=x_col, y=y_col,
#                     color=color_arg,
#                     title=title,
#                     color_discrete_sequence=self.COLORS,
#                     hover_data={c: True for c in plot_df.columns},
#                     markers=True
#                 )
#                 fig.update_traces(line=dict(width=2.5))

#             elif chart_type == "box":
#                 color_arg = color_col if color_col and color_col in plot_df.columns else x_col
#                 # Cast x to string for box plots
#                 plot_df[x_col] = plot_df[x_col].astype(str)
#                 fig = px.box(
#                     plot_df, x=x_col, y=y_col,
#                     color=color_arg if color_arg in plot_df.columns else None,
#                     title=title,
#                     color_discrete_sequence=self.COLORS,
#                     points="outliers"
#                 )

#             elif chart_type == "scatter":
#                 color_arg = color_col if color_col and color_col in plot_df.columns else None
#                 fig = px.scatter(
#                     plot_df, x=x_col, y=y_col,
#                     color=color_arg,
#                     title=title,
#                     color_discrete_sequence=self.COLORS,
#                     hover_data={c: True for c in plot_df.columns},
#                     opacity=0.7
#                 )

#             elif chart_type == "pie":
#                 fig = px.pie(
#                     plot_df, names=x_col, values=y_col,
#                     title=title,
#                     color_discrete_sequence=self.COLORS,
#                     hole=0.35  # donut style
#                 )
#                 fig.update_traces(textposition="inside",
#                                   textinfo="percent+label")

#             elif chart_type == "histogram":
#                 fig = px.histogram(
#                     plot_df, x=x_col,
#                     color=color_col if color_col and color_col in plot_df.columns else None,
#                     title=title,
#                     color_discrete_sequence=self.COLORS,
#                     nbins=30
#                 )

#             else:
#                 fig = px.bar(plot_df, x=x_col, y=y_col, title=title)

#             self._apply_layout(fig, title)
#             return {"title": title, "figure_json": json.loads(fig.to_json())}

#         except Exception as e:
#             fig = go.Figure()
#             fig.update_layout(title=f"⚠️ Could not render: {title} ({e})")
#             return {"title": title, "figure_json": json.loads(fig.to_json())}


# # ================================================================
# # CHART PLANNER  — LLM decides WHAT, Python builds HOW
# # ================================================================

# class ChartPlanner:
#     """
#     Asks the LLM to output a JSON plan of what charts to make.
#     Then ChartBuilder builds them in pure Python — no LLM chart code.
#     """

#     def __init__(self, ollama_client: OllamaClient, debug=False):
#         self.ollama  = ollama_client
#         self.debug   = debug
#         self.builder = ChartBuilder()

#     def _build_fallback_specs(self, df):
#         """
#         If LLM fails, generate sensible default chart specs
#         based on column types. Always produces valid charts.
#         """
#         specs        = []
#         numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
#         date_cols    = df.select_dtypes(include=["datetime64"]).columns.tolist()

#         # Detect main metric column
#         main_metric = None
#         for kw in ["sales","revenue","amount","price","profit","score","marks"]:
#             for col in numeric_cols:
#                 if kw in col.lower():
#                     main_metric = col
#                     break
#             if main_metric:
#                 break
#         if not main_metric and numeric_cols:
#             main_metric = numeric_cols[0]

#         # Detect main category column
#         main_cat = None
#         for kw in ["store","region","product","category","dept","city","state","branch"]:
#             for col in df.columns:
#                 if kw in col.lower() and df[col].nunique() < 100:
#                     main_cat = col
#                     break
#             if main_cat:
#                 break
#         if not main_cat:
#             for col in df.columns:
#                 if df[col].nunique() < 50 and col != main_metric:
#                     main_cat = col
#                     break

#         # Detect flag/boolean column
#         flag_col = None
#         for col in df.columns:
#             if any(kw in col.lower() for kw in ["holiday","flag","weekend","promo"]):
#                 if df[col].nunique() <= 5:
#                     flag_col = col
#                     break

#         if main_cat and main_metric:
#             specs.append({
#                 "chart_type": "bar",
#                 "title":      f"Total {main_metric.replace('_',' ').title()} by {main_cat.replace('_',' ').title()}",
#                 "x_col":      main_cat,
#                 "y_col":      main_metric,
#                 "color_col":  main_cat,
#                 "agg":        "sum",
#                 "group_by":   main_cat,
#                 "top_n":      20,
#                 "sort":       "desc"
#             })

#         if date_cols and main_metric:
#             specs.append({
#                 "chart_type": "line",
#                 "title":      f"{main_metric.replace('_',' ').title()} Trend Over Time",
#                 "x_col":      date_cols[0],
#                 "y_col":      main_metric,
#                 "color_col":  None,
#                 "agg":        "sum",
#                 "group_by":   date_cols[0],
#                 "top_n":      None,
#                 "sort":       None
#             })

#         if flag_col and main_metric:
#             specs.append({
#                 "chart_type": "box",
#                 "title":      f"{main_metric.replace('_',' ').title()} — {flag_col.replace('_',' ').title()} Comparison",
#                 "x_col":      flag_col,
#                 "y_col":      main_metric,
#                 "color_col":  flag_col,
#                 "agg":        "none",
#                 "group_by":   None,
#                 "top_n":      None,
#                 "sort":       None
#             })
#         elif main_cat and main_metric and len(specs) < 3:
#             specs.append({
#                 "chart_type": "pie",
#                 "title":      f"{main_metric.replace('_',' ').title()} Share by {main_cat.replace('_',' ').title()} (Top 10)",
#                 "x_col":      main_cat,
#                 "y_col":      main_metric,
#                 "color_col":  main_cat,
#                 "agg":        "sum",
#                 "group_by":   main_cat,
#                 "top_n":      10,
#                 "sort":       "desc"
#             })

#         return specs[:3]

#     def plan_and_build(self, user_prompt, df, metadata):
#         """
#         Step 1: Ask LLM for a JSON chart plan.
#         Step 2: Parse the plan.
#         Step 3: Build charts in pure Python using ChartBuilder.
#         Step 4: On any failure, fall back to sensible defaults.
#         """
#         schema = metadata.get("llm_schema_description", "")

#         user_msg = (
#             f"DATASET SCHEMA:\n{schema}\n\n"
#             f"USER REQUEST:\n{user_prompt}\n\n"
#             f"Return ONLY a JSON array of chart specs. No markdown, no explanation."
#         )

#         specs = None
#         try:
#             raw = self.ollama.generate(
#                 system_prompt=CHART_PLANNER_PROMPT,
#                 user_message=user_msg,
#                 temperature=0.1,
#                 max_tokens=1024,
#                 debug=self.debug
#             )
#             # Extract JSON array from response
#             json_match = re.search(r'\[.*\]', raw, re.DOTALL)
#             if json_match:
#                 specs = json.loads(json_match.group())
#                 # Validate each spec has required fields
#                 specs = [s for s in specs
#                          if s.get("x_col") in df.columns
#                          and s.get("y_col") in df.columns]
#                 if not specs:
#                     raise ValueError("No valid specs after column validation")
#                 print(f"  ✅ LLM planned {len(specs)} charts")
#             else:
#                 raise ValueError("No JSON array found in LLM response")

#         except Exception as e:
#             print(f"  ⚠️ LLM planning failed ({e}) — using smart defaults")
#             specs = self._build_fallback_specs(df)

#         # Build all charts in pure Python
#         figures = []
#         for spec in specs[:3]:
#             print(f"  Building: {spec.get('title', 'Chart')} ({spec.get('chart_type')})")
#             fig_data = self.builder.build(df, spec)
#             figures.append(fig_data)

#         return figures


# # ================================================================
# # DATA SUMMARIZER
# # ================================================================

# def summarize_chart_data(df, metadata):
#     lines        = []
#     numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
#     cat_cols     = df.select_dtypes(include=["object","category"]).columns.tolist()
#     date_cols    = df.select_dtypes(include=["datetime64"]).columns.tolist()

#     lines.append(f"Dataset: {len(df):,} rows, {df.shape[1]} columns")

#     for col in numeric_cols[:5]:
#         lines.append(
#             f"{col}: total={df[col].sum():,.2f}, "
#             f"avg={df[col].mean():,.2f}, "
#             f"max={df[col].max():,.2f}, min={df[col].min():,.2f}"
#         )
#     for col in cat_cols[:3]:
#         top = df[col].value_counts().head(5)
#         lines.append(f"\nTop values in '{col}':")
#         for val, cnt in top.items():
#             lines.append(f"  {val}: {cnt:,} rows")
#     for col in date_cols[:1]:
#         lines.append(f"\nDate range: {df[col].min().date()} to {df[col].max().date()}")
#     if date_cols and numeric_cols:
#         year_col = f"{date_cols[0]}_year"
#         if year_col in df.columns:
#             yearly = df.groupby(year_col)[numeric_cols[0]].sum()
#             lines.append(f"\nYear-wise {numeric_cols[0]} totals:")
#             for yr, total in yearly.items():
#                 lines.append(f"  {int(yr)}: {total:,.2f}")
#     return "\n".join(lines)


# # ================================================================
# # LLM ENGINE
# # ================================================================

# class LLMEngine:

#     def __init__(self, model="llama3.2", debug=False):
#         self.debug   = debug
#         self.ollama  = OllamaClient(model=model)
#         self.planner = ChartPlanner(self.ollama, debug=debug)
#         self._check_connection()

#     def _check_connection(self):
#         if not self.ollama.is_running():
#             print("\n⚠️  Ollama not running. Run: ollama serve\n")
#         else:
#             available = self.ollama.list_models()
#             print(f"✅ Ollama connected — model: {self.ollama.model}")
#             print(f"   Models available: {available}")

#     # ── MODE 1: CHART GENERATION ─────────────────────────────────
#     def generate_charts(self, user_prompt, df, metadata, max_retries=2):
#         """
#         LLM plans what charts to show (JSON spec).
#         Python builds the actual charts (always correct).
#         """
#         print(f"\n[Charts] Planning charts for: {user_prompt[:60]}...")
#         figures = self.planner.plan_and_build(user_prompt, df, metadata)
#         print(f"  ✅ {len(figures)} charts built successfully")
#         return figures

#     # ── MODE 2: Q&A ──────────────────────────────────────────────
#     def answer_question(self, question, df, metadata, max_retries=2):

#             import re
#             import json
#             import pandas as pd
#             import numpy as np
#             import plotly.express as px

#             schema = metadata.get("llm_schema_description", "")

#             pandas_code = None
#             raw_result = None
#             result_str = ""
#             error_context = ""

#             # =====================================================
#             # QUESTION PROMPT
#             # =====================================================
#             query_msg = f"""
#     DATASET SCHEMA:
#     {schema}

#     QUESTION:
#     {question}

#     You are an expert Pandas analyst.

#     RULES:
#     1. Use dataframe name: df
#     2. Return ONLY executable Python code
#     3. Store final output in variable named: result
#     4. No markdown
#     5. No explanations
#     6. No ```python blocks

#     GOOD EXAMPLE:
#     result = df.groupby('store')['weekly_sales'].sum().idxmax()
#     """

#             # =====================================================
#             # RETRY LOOP
#             # =====================================================
#             for attempt in range(1, max_retries + 2):

#                 print(f"\n[Q&A] Attempt {attempt}...")

#                 retry_note = (
#                     f"\nPREVIOUS ERROR:\n{error_context}\nFix the code."
#                     if error_context else ""
#                 )

#                 try:

#                     raw = self.ollama.generate(
#                         system_prompt=QA_QUERY_SYSTEM_PROMPT,
#                         user_message=query_msg + retry_note,
#                         temperature=0.1,
#                         max_tokens=512,
#                         debug=self.debug
#                     )

#                 except Exception as e:

#                     error_context = str(e)
#                     continue

#                 # =================================================
#                 # CLEAN LLM OUTPUT
#                 # =================================================
#                 pandas_code = raw.strip()

#                 pandas_code = pandas_code.replace("```python", "")
#                 pandas_code = pandas_code.replace("```", "")
#                 pandas_code = pandas_code.strip()

#                 print("\nGenerated Code:")
#                 print(pandas_code)

#                 # =================================================
#                 # BASIC SECURITY
#                 # =================================================
#                 dangerous = [
#                     "import os",
#                     "open(",
#                     "exec(",
#                     "eval(",
#                     "subprocess",
#                     "__"
#                 ]

#                 if any(d in pandas_code for d in dangerous):

#                     error_context = "Unsafe code detected"
#                     continue

#                 # =================================================
#                 # EXECUTE CODE
#                 # =================================================
#                 try:

#                     scope = {
#                         "df": df.copy(),
#                         "pd": pd,
#                         "np": np,
#                         "px": px,
#                         "FESTIVAL_CALENDAR": FESTIVAL_CALENDAR
#                     }

#                     exec(pandas_code, {}, scope)

#                     raw_result = scope.get("result")

#                     if raw_result is None:

#                         error_context = "Variable `result` not found"
#                         continue

#                     # =============================================
#                     # FORMAT RESULT
#                     # =============================================
#                     if isinstance(raw_result, (pd.DataFrame, pd.Series)):

#                         result_str = raw_result.head(20).to_string()

#                     else:

#                         result_str = str(raw_result)

#                     print("\n✅ Query Result:")
#                     print(result_str[:500])

#                     break

#                 except Exception as e:

#                     error_context = str(e)

#                     print(f"\n❌ Execution Error: {e}")

#             # =====================================================
#             # FAILED AFTER RETRIES
#             # =====================================================
#             if raw_result is None:

#                 return {
#                     "question": question,
#                     "pandas_query": pandas_code or "Failed",
#                     "raw_result": "Could not compute",
#                     "answer": "Sorry, could not answer this question with the available data.",
#                     "mini_chart": None
#                 }

#             # =====================================================
#             # BUSINESS INTERPRETATION
#             # =====================================================
#             print("\n[Q&A] Generating business explanation...")

#             explanation_prompt = f"""
#     QUESTION:
#     {question}

#     RESULT:
#     {result_str}

#     Explain this result like a business analyst.
#     Use simple business language.
#     Keep answer concise but insightful.
#     """

#             try:

#                 plain = self.ollama.generate(
#                     system_prompt=QA_INTERPRET_SYSTEM_PROMPT,
#                     user_message=explanation_prompt,
#                     temperature=0.3,
#                     max_tokens=400,
#                     debug=self.debug
#                 )

#             except Exception as e:

#                 plain = f"Could not generate explanation: {e}"

#             # =====================================================
#             # MINI CHART GENERATION
#             # =====================================================
#             mini_chart = None

#             try:

#                 if isinstance(raw_result, pd.Series):

#                     cdf = raw_result.reset_index()

#                     cdf.columns = ["category", "value"]

#                 elif isinstance(raw_result, pd.DataFrame):

#                     cdf = raw_result.head(15)

#                 else:

#                     cdf = None

#                 if cdf is not None and len(cdf.columns) >= 2:

#                     fig = px.bar(
#                         cdf,
#                         x=cdf.columns[0],
#                         y=cdf.columns[1],
#                         title=question[:60]
#                     )

#                     fig.update_layout(
#                         paper_bgcolor="white",
#                         plot_bgcolor="#f8f9fc"
#                     )

#                     mini_chart = json.loads(fig.to_json())

#             except Exception as e:

#                 print("Mini chart failed:", e)

#             # =====================================================
#             # FINAL RESPONSE
#             # =====================================================
#             return {
#                 "question": question,
#                 "pandas_query": pandas_code,
#                 "raw_result": result_str,
#                 "answer": plain.strip(),
#                 "mini_chart": mini_chart
#             }


#     # def answer_question(self, question, df, metadata, max_retries=2):
#     #     schema        = metadata.get("llm_schema_description", "")
#     #     pandas_code   = None
#     #     raw_result    = None
#     #     result_str    = ""
#     #     error_context = ""

#     #     query_msg = (
#     #         f"DATASET SCHEMA:\n{schema}\n\n"
#     #         f"QUESTION:\n{question}\n\n"
#     #         f"Write ONE Pandas expression. Store in `result`. Return ONLY code."
#     #     )

#     #     for attempt in range(1, max_retries + 2):
#     #         print(f"\n[Q&A] Attempt {attempt}...")
#     #         retry_note = f"\nERROR: {error_context}\nFix it." if error_context else ""
#     #         raw = self.ollama.generate(
#     #             system_prompt=QA_QUERY_SYSTEM_PROMPT,
#     #             user_message=query_msg + retry_note,
#     #             temperature=0.1, max_tokens=512, debug=self.debug
#     #         )
#     #         pandas_code = re.sub(r'```.*?```', '', raw, flags=re.DOTALL).strip()
#     #         dangerous   = ["import os","open(","exec(","eval(","subprocess"]
#     #         if any(d in pandas_code for d in dangerous):
#     #             error_context = "Unsafe code"
#     #             continue
#     #         try:
#     #             scope = {"df": df.copy(), "pd": pd, "np": np,
#     #                      "px": px, "FESTIVAL_CALENDAR": FESTIVAL_CALENDAR}
#     #             exec(pandas_code, {}, scope)
#     #             raw_result = scope.get("result")
#     #             if raw_result is None:
#     #                 error_context = "`result` not set"
#     #                 continue
#     #             result_str = (raw_result.head(20).to_string()
#     #                           if isinstance(raw_result, (pd.DataFrame, pd.Series))
#     #                           else str(raw_result))
#     #             print(f"  ✅ Result: {result_str[:80]}")
#     #             break
#     #         except Exception as e:
#     #             error_context = str(e)
#     #             print(f"  ❌ Error: {e}")

#     #     if raw_result is None:
#     #         return {"question": question, "pandas_query": pandas_code or "Failed",
#     #                 "raw_result": "Could not compute",
#     #                 "answer": "Sorry, could not answer this question with the available data.",
#     #                 "mini_chart": None}

#     #     print("\n[Q&A] Generating plain English answer...")
#     #     plain = self.ollama.generate(
#     #         system_prompt=QA_INTERPRET_SYSTEM_PROMPT,
#     #         user_message=f"QUESTION:\n{question}\n\nDATA RESULT:\n{result_str}\n\nWrite a 4-5 sentence business answer.",
#     #         temperature=0.4, max_tokens=400, debug=self.debug
#     #     )

#     #     # Mini chart
#     #     mini_chart = None
#     #     try:
#     #         if isinstance(raw_result, (pd.DataFrame, pd.Series)):
#     #             cdf = (raw_result.reset_index() if isinstance(raw_result, pd.Series)
#     #                    else raw_result.head(15))
#     #             if isinstance(raw_result, pd.Series):
#     #                 cdf.columns = ["category", "value"]
#     #             if len(cdf) > 1:
#     #                 cols = cdf.columns.tolist()
#     #                 fig  = px.bar(cdf, x=cols[0],
#     #                               y=cols[1] if len(cols) > 1 else cols[0],
#     #                               title=question[:60],
#     #                               color_discrete_sequence=["#0C447C"])
#     #                 fig.update_layout(paper_bgcolor="white", plot_bgcolor="#f8f9fc")
#     #                 mini_chart = json.loads(fig.to_json())
#     #     except Exception:
#     #         pass

#     #     return {"question": question, "pandas_query": pandas_code,
#     #             "raw_result": result_str, "answer": plain.strip(),
#     #             "mini_chart": mini_chart}

#     # ── MODE 3: REPORT ───────────────────────────────────────────
#     def generate_report(self, df, metadata):
#         print("\n[Report] Summarising data...")
#         summary = summarize_chart_data(df, metadata)
#         print("[Report] Calling LLM...")
#         text = self.ollama.generate(
#             system_prompt=REPORT_SYSTEM_PROMPT,
#             user_message=(
#                 f"DASHBOARD DATA SUMMARY:\n{summary}\n\n"
#                 f"SCHEMA:\n{metadata.get('llm_schema_description','')[:1000]}\n\n"
#                 f"Write the executive report now."
#             ),
#             temperature=0.5, max_tokens=1500, debug=self.debug
#         )
#         return {"report_text": text.strip(),
#                 "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#                 "data_summary": summary}


# # ================================================================
# # TEST
# # ================================================================

# if __name__ == "__main__":
#     import sys, os

#     print("\n" + "="*60)
#     print("  LLM ENGINE — TEST")
#     print("="*60)

#     client = OllamaClient(model="llama3.2")
#     if not client.is_running():
#         print("❌ Ollama not running. Run: ollama serve")
#         sys.exit(1)

#     print(f"✅ Ollama running. Models: {client.list_models()}")

#     # Load Walmart data
#     for path in ["data/walmart.csv", "data/Walmart.csv", "Walmart.csv"]:
#         if os.path.exists(path):
#             df = pd.read_csv(path)
#             df.columns = [c.strip().lower().replace(" ","_") for c in df.columns]
#             if "date" in df.columns and df["date"].dtype == object:
#                 df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
#                 df["date_year"]    = df["date"].dt.year
#                 df["date_month"]   = df["date"].dt.month
#                 df["date_quarter"] = df["date"].dt.quarter
#             print(f"✅ Loaded {path}: {df.shape}")
#             break
#     else:
#         print("Walmart CSV not found — using fake data")
#         df = pd.DataFrame({
#             "date":         pd.date_range("2022-01-01", periods=24, freq="ME"),
#             "weekly_sales": [12000,15000,13000,18000,20000,25000,
#                              14000,16000,22000,30000,28000,35000,
#                              13000,16000,14000,19000,21000,26000,
#                              15000,17000,23000,31000,29000,36000],
#             "store":        [1,2,3,4]*6,
#             "holiday_flag": [0,0,1,0]*6,
#         })

#     # Build metadata
#     numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
#     cat_cols     = df.select_dtypes(include=["object","category"]).columns.tolist()
#     date_cols    = df.select_dtypes(include=["datetime64"]).columns.tolist()
#     col_lines    = []
#     for col in df.columns:
#         dtype = str(df[col].dtype)
#         nuniq = df[col].nunique()
#         line  = f"  - {col} ({dtype}, {nuniq} unique)"
#         if col in numeric_cols:
#             line += f" | min={df[col].min():.2f}, max={df[col].max():.2f}, mean={df[col].mean():.2f}"
#         if col in cat_cols:
#             line += f" | top: {df[col].value_counts().head(3).index.tolist()}"
#         if col in date_cols:
#             line += f" | range: {df[col].min().date()} to {df[col].max().date()}"
#         col_lines.append(line)

#     metadata = {
#         "llm_schema_description": (
#             f"Dataset: {len(df):,} rows x {df.shape[1]} columns.\n"
#             f"Columns:\n" + "\n".join(col_lines) + "\n"
#             f"\nSample: {df.head(1).to_dict(orient='records')[0]}"
#         )
#     }

#     engine = LLMEngine(model="llama3.2", debug=True)

#     print("\n--- Test 1: Charts ---")
#     try:
#         figs = engine.generate_charts(
#             "Show total weekly sales by store, sales trend over time, and holiday vs non-holiday comparison",
#             df, metadata
#         )
#         print(f"✅ {len(figs)} charts:")
#         for f in figs: print(f"   {f['title']}")
#     except Exception as e:
#         print(f"❌ {e}")

#     print("\n--- Test 2: Q&A ---")
#     try:
#         qa = engine.answer_question("Which store had highest total sales?", df, metadata)
#         print(f"✅ {qa['answer'][:200]}")
#     except Exception as e:
#         print(f"❌ {e}")

#     print("\n--- Test 3: Report ---")
#     try:
#         rep = engine.generate_report(df, metadata)
#         print(f"✅ Report: {len(rep['report_text'])} chars")
#         print(rep["report_text"][:400])
#     except Exception as e:
#         print(f"❌ {e}")

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
Given a dataset schema and a business question, write ONE Pandas expression.
DataFrame is called `df`. Store result in variable called `result`.
RULES:
1. Return ONLY the Python code — nothing else, no explanation.
2. Result must be a scalar, string, or small Series/DataFrame (max 20 rows).
3. Example: result = df.groupby('region')['sales'].sum().idxmax()
"""

QA_INTERPRET_SYSTEM_PROMPT = """You are a senior business analyst.
You receive a business question and the raw data result.
Write a clear 4-5 sentence answer in plain English using actual numbers.
Do not say 'based on the data' — state findings directly.
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
CHART_PLANNER_PROMPT = """You are a data analyst deciding what charts to show.
You receive a dataset schema and a user request.
Respond with a JSON array of chart specifications. Each item has:
  - "chart_type": one of "bar", "line", "box", "scatter", "pie", "histogram"
  - "title": a clear descriptive title
  - "x_col": exact column name for x axis (must exist in schema)
  - "y_col": exact column name for y axis (must exist in schema)
  - "color_col": column to color by (optional, use null if not needed)
  - "agg": aggregation method — "sum", "mean", "count", or "none"
  - "group_by": column to group/aggregate by (same as x_col usually)
  - "top_n": integer, limit to top N categories (use 20 for stores, 10 for others, null for time series)
  - "sort": "desc" or "asc" or null

RULES:
- Return ONLY valid JSON array — no explanation, no markdown.
- Use ONLY column names that exist in the schema.
- For time series: x_col = date column, agg = "sum", group_by = date column, top_n = null
- For category bars: group_by = category column, agg = "sum" or "mean"
- Suggest 3 charts maximum.

Example output:
[
  {"chart_type": "bar", "title": "Total Sales by Store", "x_col": "store", "y_col": "weekly_sales", "color_col": "store", "agg": "sum", "group_by": "store", "top_n": 20, "sort": "desc"},
  {"chart_type": "line", "title": "Weekly Sales Trend", "x_col": "date", "y_col": "weekly_sales", "color_col": null, "agg": "sum", "group_by": "date", "top_n": null, "sort": null},
  {"chart_type": "box", "title": "Holiday vs Non-Holiday Sales", "x_col": "holiday_flag", "y_col": "weekly_sales", "color_col": "holiday_flag", "agg": "none", "group_by": null, "top_n": null, "sort": null}
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

    @staticmethod
    def _prepare_data(df, spec):
        """Aggregate data according to the spec before plotting."""
        x_col    = spec["x_col"]
        y_col    = spec["y_col"]
        agg      = spec.get("agg", "sum")
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
                fig.update_layout(title=f"⚠️ Column '{col}' not found in data")
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

    def _build_fallback_specs(self, df):
        """
        If LLM fails, generate sensible default chart specs
        based on column types. Always produces valid charts.
        """
        specs        = []
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        date_cols    = df.select_dtypes(include=["datetime64"]).columns.tolist()

        # Detect main metric column
        main_metric = None
        for kw in ["sales","revenue","amount","price","profit","score","marks"]:
            for col in numeric_cols:
                if kw in col.lower():
                    main_metric = col
                    break
            if main_metric:
                break
        if not main_metric and numeric_cols:
            main_metric = numeric_cols[0]

        # Detect main category column
        main_cat = None
        for kw in ["store","region","product","category","dept","city","state","branch"]:
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

        # Detect flag/boolean column
        flag_col = None
        for col in df.columns:
            if any(kw in col.lower() for kw in ["holiday","flag","weekend","promo"]):
                if df[col].nunique() <= 5:
                    flag_col = col
                    break

        if main_cat and main_metric:
            specs.append({
                "chart_type": "bar",
                "title":      f"Total {main_metric.replace('_',' ').title()} by {main_cat.replace('_',' ').title()}",
                "x_col":      main_cat,
                "y_col":      main_metric,
                "color_col":  main_cat,
                "agg":        "sum",
                "group_by":   main_cat,
                "top_n":      20,
                "sort":       "desc"
            })

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

        if flag_col and main_metric:
            specs.append({
                "chart_type": "box",
                "title":      f"{main_metric.replace('_',' ').title()} — {flag_col.replace('_',' ').title()} Comparison",
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
                "title":      f"{main_metric.replace('_',' ').title()} Share by {main_cat.replace('_',' ').title()} (Top 10)",
                "x_col":      main_cat,
                "y_col":      main_metric,
                "color_col":  main_cat,
                "agg":        "sum",
                "group_by":   main_cat,
                "top_n":      10,
                "sort":       "desc"
            })

        return specs[:3]

    def _parse_filters(self, user_prompt, df):
        """
        Parse user prompt for filter instructions like:
        'store 20', 'year 2011', 'year wise', 'monthly', 'quarterly'
        Returns a filtered DataFrame and a description of what was filtered.
        """
        filtered_df  = df.copy()
        filter_notes = []
        prompt_lower = user_prompt.lower()

        # Filter by specific store number  e.g. "store 20" "for store 4"
        store_match = re.search(r'store\s+(\d+)', prompt_lower)
        if store_match and "store" in df.columns:
            store_num = int(store_match.group(1))
            filtered_df = filtered_df[filtered_df["store"] == store_num]
            filter_notes.append(f"Store {store_num} only")

        # Filter by specific year  e.g. "year 2011" "in 2010"
        year_match = re.search(r'\b(20\d{2})\b', user_prompt)
        date_cols  = df.select_dtypes(include=["datetime64"]).columns.tolist()
        if year_match and date_cols:
            year_num = int(year_match.group(1))
            year_col_name = f"{date_cols[0]}_year"
            if year_col_name in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[year_col_name] == year_num]
                filter_notes.append(f"Year {year_num} only")

        # Detect granularity preference
        if any(kw in prompt_lower for kw in ["year wise","yearly","annual","by year"]):
            self._granularity = "year"
        elif any(kw in prompt_lower for kw in ["quarter","quarterly","by quarter"]):
            self._granularity = "quarter"
        elif any(kw in prompt_lower for kw in ["month","monthly","by month"]):
            self._granularity = "month"
        else:
            self._granularity = "date"  # default: full date

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

    def plan_and_build(self, user_prompt, df, metadata):
        """
        Step 0: Parse filters from prompt (store X, year Y etc.)
        Step 1: Ask LLM for a JSON chart plan.
        Step 2: Validate and apply granularity.
        Step 3: Build charts in pure Python using ChartBuilder.
        Step 4: On any failure, fall back to sensible defaults.
        """
        # Step 0: filter df based on prompt
        filtered_df, filter_notes = self._parse_filters(user_prompt, df)
        if filter_notes:
            print(f"  🔍 Filters applied: {filter_notes}")
        if len(filtered_df) == 0:
            print("  ⚠️ Filter produced empty DataFrame — using full data")
            filtered_df = df.copy()

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
            json_match = re.search(r'\[.*\]', raw, re.DOTALL)
            if json_match:
                specs = json.loads(json_match.group())
                specs = [self._apply_granularity(s, filtered_df)
                         for s in specs
                         if s.get("x_col") in filtered_df.columns
                         and s.get("y_col") in filtered_df.columns]
                if not specs:
                    raise ValueError("No valid specs after validation")
                print(f"  ✅ LLM planned {len(specs)} charts")
            else:
                raise ValueError("No JSON array found")

        except Exception as e:
            print(f"  ⚠️ LLM planning failed ({e}) — using smart defaults")
            specs = self._build_fallback_specs(filtered_df)
            specs = [self._apply_granularity(s, filtered_df) for s in specs]

        # Add filter context to chart titles
        title_suffix = f" ({', '.join(filter_notes)})" if filter_notes else ""

        figures = []
        for spec in specs[:3]:
            spec = dict(spec)
            spec["title"] = spec.get("title", "Chart") + title_suffix
            print(f"  Building: {spec['title']} ({spec.get('chart_type')})")
            fig_data = self.builder.build(filtered_df, spec)
            figures.append(fig_data)

        return figures


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
    def answer_question(self, question, df, metadata, max_retries=2):
        schema        = metadata.get("llm_schema_description", "")
        pandas_code   = None
        raw_result    = None
        result_str    = ""
        error_context = ""

        query_msg = (
            f"DATASET SCHEMA:\n{schema}\n\n"
            f"QUESTION:\n{question}\n\n"
            f"Write ONE Pandas expression. Store in `result`. Return ONLY code."
        )

        for attempt in range(1, max_retries + 2):
            print(f"\n[Q&A] Attempt {attempt}...")
            retry_note = f"\nERROR: {error_context}\nFix it." if error_context else ""
            raw = self.ollama.generate(
                system_prompt=QA_QUERY_SYSTEM_PROMPT,
                user_message=query_msg + retry_note,
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