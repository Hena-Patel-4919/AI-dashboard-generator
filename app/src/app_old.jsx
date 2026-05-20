
// // // ================================================================
// // // AI DASHBOARD GENERATOR Complete React Frontend
// // // File: frontend/src/App.jsx

// // // HOW TO SET UP:
// // //   cd C:\Users\Krish Patel\...\LLM
// // //   npx create-react-app frontend
// // //   cd frontend
// // //   npm install react-plotly.js plotly.js axios
// // //   Replace src/App.jsx with this file
// // //   Replace src/index.css with the CSS at the bottom
// // //   npm start

// // // MAKE SURE FastAPI is running:
// // //   python app/api_main.py   (in a separate terminal)
// // // ================================================================

// // import { useState, useRef, useEffect, useCallback } from "react";
// // import axios from "axios";
// // import Plot from "react-plotly.js";

// // const API = "http://localhost:8000";

// // // ── Axios instance ─────────────────────────────────────────────
// // const api = axios.create({ baseURL: API, timeout: 300000 });


// // // ================================================================
// // // ICONS  (inline SVG — no icon library needed)
// // // ================================================================
// // const Icon = {
// //   Upload:   () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/></svg>,
// //   Chart:    () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>,
// //   Send:     () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>,
// //   Report:   () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>,
// //   Download: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>,
// //   Expand:   () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>,
// //   Close:    () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>,
// //   Spark:    () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>,
// //   Bot:      () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4M8 15h.01M16 15h.01"/></svg>,
// //   Clear:    () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/><path d="M10 11v6M14 11v6"/></svg>,
// // };


// // // ================================================================
// // // SPINNER
// // // ================================================================
// // const Spinner = ({ size = 20, color = "#6366f1" }) => (
// //   <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
// //        style={{ animation: "spin 0.8s linear infinite" }}>
// //     <circle cx="12" cy="12" r="10" stroke={color} strokeWidth="3" strokeOpacity="0.2"/>
// //     <path d="M12 2a10 10 0 0110 10" stroke={color} strokeWidth="3" strokeLinecap="round"/>
// //   </svg>
// // );


// // // ================================================================
// // // UPLOAD PANEL
// // // ================================================================
// // const UploadPanel = ({ onUploadSuccess, uploadedFile }) => {
// //   const [dragging, setDragging] = useState(false);
// //   const [loading,  setLoading]  = useState(false);
// //   const [error,    setError]    = useState("");
// //   const inputRef = useRef();

// //   const handleFile = useCallback(async (file) => {
// //     if (!file) return;
// //     const allowed = [".csv", ".xlsx", ".xls", ".json", ".parquet", ".tsv"];
// //     const ext = "." + file.name.split(".").pop().toLowerCase();
// //     if (!allowed.includes(ext)) {
// //       setError(`Unsupported format. Allowed: ${allowed.join(", ")}`);
// //       return;
// //     }
// //     setLoading(true);
// //     setError("");
// //     try {
// //       const fd = new FormData();
// //       fd.append("file", file);
// //       const { data } = await api.post("/upload", fd, {
// //         headers: { "Content-Type": "multipart/form-data" },
// //       });
// //       onUploadSuccess(data);
// //     } catch (e) {
// //       setError(e.response?.data?.detail || "Upload failed. Is FastAPI running?");
// //     } finally {
// //       setLoading(false);
// //     }
// //   }, [onUploadSuccess]);

// //   const onDrop = (e) => {
// //     e.preventDefault();
// //     setDragging(false);
// //     handleFile(e.dataTransfer.files[0]);
// //   };

// //   return (
// //     <div className="panel upload-panel">
// //       <div className="panel-title">
// //         <span className="icon-wrap"><Icon.Upload /></span>
// //         Upload Dataset
// //       </div>

// //       {!uploadedFile ? (
// //         <div
// //           className={`drop-zone ${dragging ? "dragging" : ""} ${loading ? "loading" : ""}`}
// //           onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
// //           onDragLeave={() => setDragging(false)}
// //           onDrop={onDrop}
// //           onClick={() => inputRef.current?.click()}
// //         >
// //           <input ref={inputRef} type="file"
// //                  accept=".csv,.xlsx,.xls,.json,.parquet,.tsv"
// //                  style={{ display: "none" }}
// //                  onChange={(e) => handleFile(e.target.files[0])} />
// //           {loading ? (
// //             <div className="drop-content">
// //               <Spinner size={32} />
// //               <p>Processing & cleaning data...</p>
// //             </div>
// //           ) : (
// //             <div className="drop-content">
// //               <div className="drop-icon">📂</div>
// //               <p className="drop-main">Drag & drop your file here</p>
// //               <p className="drop-sub">CSV · Excel · JSON · Parquet · TSV</p>
// //               <button className="btn btn-outline">Browse files</button>
// //             </div>
// //           )}
// //         </div>
// //       ) : (
// //         <div className="upload-success">
// //           <div className="success-header">
// //             <span className="success-icon">✅</span>
// //             <div>
// //               <div className="success-name">{uploadedFile.filename}</div>
// //               <div className="success-meta">
// //                 {uploadedFile.rows?.toLocaleString()} rows · {uploadedFile.columns} columns
// //               </div>
// //             </div>
// //           </div>
// //           <div className="cleaning-tags">
// //             {uploadedFile.cleaning_summary?.duplicates_removed > 0 &&
// //               <span className="ctag green">✓ {uploadedFile.cleaning_summary.duplicates_removed} duplicates removed</span>}
// //             {uploadedFile.cleaning_summary?.memory_saved_mb > 0 &&
// //               <span className="ctag blue">✓ {uploadedFile.cleaning_summary.memory_saved_mb?.toFixed(1)}MB saved</span>}
// //             <span className="ctag green">✓ Data cleaned</span>
// //           </div>
// //           <div className="col-list">
// //             {uploadedFile.column_info?.slice(0, 8).map(c => (
// //               <span key={c.name} className={`col-badge ${
// //                 c.dtype.includes("int") || c.dtype.includes("float") ? "num" :
// //                 c.dtype.includes("datetime") ? "date" : "cat"}`}>
// //                 {c.name}
// //               </span>
// //             ))}
// //             {uploadedFile.column_info?.length > 8 &&
// //               <span className="col-badge more">+{uploadedFile.column_info.length - 8} more</span>}
// //           </div>
// //           <button className="btn btn-ghost btn-sm"
// //                   onClick={() => { onUploadSuccess(null); inputRef.current?.click(); }}>
// //             Upload different file
// //           </button>
// //         </div>
// //       )}

// //       {error && <div className="error-msg">{error}</div>}
// //     </div>
// //   );
// // };


// // // ================================================================
// // // PROMPT BAR
// // // ================================================================
// // const PromptBar = ({ onGenerate, disabled, loading }) => {
// //   const [prompt, setPrompt] = useState("");

// //   const examples = [
// //     "Show sales by store and holiday impact",
// //     "Sales trend over time by quarter",
// //     "Top performing stores with seasonal patterns",
// //   ];

// //   const submit = () => {
// //     if (!prompt.trim() || loading) return;
// //     onGenerate(prompt.trim());
// //   };

// //   return (
// //     <div className="prompt-section">
// //       <div className="prompt-bar">
// //         <span className="prompt-icon"><Icon.Spark /></span>
// //         <input
// //           className="prompt-input"
// //           placeholder="Describe what you want to see... (e.g. Show weekly sales by store and holiday impact)"
// //           value={prompt}
// //           onChange={(e) => setPrompt(e.target.value)}
// //           onKeyDown={(e) => e.key === "Enter" && submit()}
// //           disabled={disabled || loading}
// //         />
// //         <button
// //           className={`btn btn-primary ${loading ? "loading" : ""}`}
// //           onClick={submit}
// //           disabled={disabled || loading || !prompt.trim()}
// //         >
// //           {loading ? <><Spinner size={16} color="white" /> Generating...</> : "Generate Dashboard"}
// //         </button>
// //       </div>
// //       {!disabled && (
// //         <div className="example-prompts">
// //           <span className="example-label">Try:</span>
// //           {examples.map(ex => (
// //             <button key={ex} className="example-chip"
// //                     onClick={() => setPrompt(ex)}>
// //               {ex}
// //             </button>
// //           ))}
// //         </div>
// //       )}
// //     </div>
// //   );
// // };


// // // ================================================================
// // // CHART MODAL  (fullscreen view)
// // // ================================================================
// // const ChartModal = ({ chart, onClose }) => {
// //   useEffect(() => {
// //     const handler = (e) => e.key === "Escape" && onClose();
// //     window.addEventListener("keydown", handler);
// //     return () => window.removeEventListener("keydown", handler);
// //   }, [onClose]);

// //   return (
// //     <div className="modal-overlay" onClick={onClose}>
// //       <div className="modal-box" onClick={(e) => e.stopPropagation()}>
// //         <div className="modal-header">
// //           <span className="modal-title">{chart.title}</span>
// //           <button className="icon-btn" onClick={onClose}><Icon.Close /></button>
// //         </div>
// //         <div className="modal-body">
// //           <Plot
// //             data={chart.figure_json.data}
// //             layout={{
// //               ...chart.figure_json.layout,
// //               autosize: true,
// //               paper_bgcolor: "white",
// //               plot_bgcolor: "#f8faff",
// //               font: { family: "'DM Sans', sans-serif", size: 13 },
// //               hoverlabel: { bgcolor: "#111827", font: { color: "white", size: 12 } },
// //               margin: { l: 70, r: 40, t: 60, b: 70 },
// //             }}
// //             config={{
// //               responsive: true,
// //               displayModeBar: true,
// //               displaylogo: false,
// //               modeBarButtonsToRemove: ["lasso2d", "select2d"],
// //               toImageButtonOptions: { format: "png", filename: chart.title, scale: 2 },
// //             }}
// //             style={{ width: "100%", height: "100%" }}
// //             useResizeHandler
// //           />
// //         </div>
// //       </div>
// //     </div>
// //   );
// // };


// // // ================================================================
// // // DASHBOARD GRID
// // // ================================================================
// // const DashboardGrid = ({ charts, onDownload }) => {
// //   const [fullscreen, setFullscreen] = useState(null);

// //   if (!charts.length) return null;

// //   const plotLayout = (chart) => ({
// //     ...chart.figure_json.layout,
// //     autosize: true,
// //     paper_bgcolor: "white",
// //     plot_bgcolor: "#f8faff",
// //     font: { family: "'DM Sans', sans-serif", size: 11, color: "#374151" },
// //     hoverlabel: { bgcolor: "#111827", font: { color: "white", size: 11 }, bordercolor: "#111827" },
// //     hovermode: "closest",
// //     margin: { l: 55, r: 20, t: 45, b: 55 },
// //     showlegend: true,
// //     legend: { bgcolor: "rgba(255,255,255,0.9)", bordercolor: "#e5e7eb",
// //               borderwidth: 1, font: { size: 10 } },
// //     xaxis: { ...chart.figure_json.layout?.xaxis,
// //              gridcolor: "#f0f1f6", linecolor: "#e5e7eb", zeroline: false },
// //     yaxis: { ...chart.figure_json.layout?.yaxis,
// //              gridcolor: "#f0f1f6", linecolor: "#e5e7eb", zeroline: false,
// //              tickformat: ".2s" },
// //   });

// //   return (
// //     <>
// //       <div className="dashboard-header">
// //         <h2 className="section-title">
// //           <span className="icon-wrap"><Icon.Chart /></span>
// //           Dashboard — {charts.length} charts
// //         </h2>
// //         <button className="btn btn-outline btn-sm" onClick={onDownload}>
// //           <Icon.Download /> Download Dashboard
// //         </button>
// //       </div>

// //       <div className={`charts-grid cols-${Math.min(charts.length, 2)}`}>
// //         {charts.map((chart, i) => (
// //           <div key={i} className="chart-card">
// //             <div className="chart-card-header">
// //               <span className="chart-card-title">{chart.title}</span>
// //               <button className="icon-btn" title="Fullscreen"
// //                       onClick={() => setFullscreen(chart)}>
// //                 <Icon.Expand />
// //               </button>
// //             </div>
// //             <div className="chart-wrap">
// //               <Plot
// //                 data={chart.figure_json.data}
// //                 layout={plotLayout(chart)}
// //                 config={{
// //                   responsive: true,
// //                   displayModeBar: true,
// //                   displaylogo: false,
// //                   modeBarButtonsToRemove: ["lasso2d", "select2d", "autoScale2d"],
// //                   toImageButtonOptions: {
// //                     format: "png", filename: chart.title,
// //                     height: 600, width: 1200, scale: 2
// //                   },
// //                 }}
// //                 style={{ width: "100%", height: "100%" }}
// //                 useResizeHandler
// //               />
// //             </div>
// //           </div>
// //         ))}
// //       </div>

// //       {fullscreen && (
// //         <ChartModal chart={fullscreen} onClose={() => setFullscreen(null)} />
// //       )}
// //     </>
// //   );
// // };


// // // ================================================================
// // // CHAT PANEL
// // // ================================================================
// // const ChatPanel = ({ disabled }) => {
// //   const [messages,  setMessages]  = useState([]);
// //   const [question,  setQuestion]  = useState("");
// //   const [loading,   setLoading]   = useState(false);
// //   const bottomRef = useRef();

// //   useEffect(() => {
// //     bottomRef.current?.scrollIntoView({ behavior: "smooth" });
// //   }, [messages]);

// //   const ask = async () => {
// //     if (!question.trim() || loading || disabled) return;
// //     const q = question.trim();
// //     setQuestion("");
// //     setMessages(m => [...m, { role: "user", text: q }]);
// //     setLoading(true);
// //     try {
// //       const { data } = await api.post("/ask", { question: q });
// //       setMessages(m => [...m, {
// //         role: "bot",
// //         text: data.answer,
// //         query: data.pandas_query,
// //         result: data.raw_result,
// //         chart: data.mini_chart,
// //       }]);
// //     } catch (e) {
// //       setMessages(m => [...m, {
// //         role: "bot",
// //         text: e.response?.data?.detail || "Something went wrong. Try again.",
// //         error: true,
// //       }]);
// //     } finally {
// //       setLoading(false);
// //     }
// //   };

// //   const suggestions = [
// //     "Which store had the highest sales?",
// //     "What was the average weekly sales?",
// //     "How many holiday weeks are there?",
// //     "What is the total revenue across all stores?",
// //   ];

// //   return (
// //     <div className="panel chat-panel">
// //       <div className="panel-title">
// //         <span className="icon-wrap"><Icon.Bot /></span>
// //         Ask Business Questions
// //         {messages.length > 0 && (
// //           <button className="icon-btn ml-auto"
// //                   title="Clear chat"
// //                   onClick={() => setMessages([])}>
// //             <Icon.Clear />
// //           </button>
// //         )}
// //       </div>

// //       <div className="chat-body">
// //         {messages.length === 0 ? (
// //           <div className="chat-empty">
// //             <div className="chat-empty-icon">💬</div>
// //             <p>Ask anything about your data</p>
// //             {!disabled && (
// //               <div className="suggestions">
// //                 {suggestions.map(s => (
// //                   <button key={s} className="suggestion-chip"
// //                           onClick={() => setQuestion(s)}>
// //                     {s}
// //                   </button>
// //                 ))}
// //               </div>
// //             )}
// //             {disabled && <p className="chat-disabled">Upload a dataset first</p>}
// //           </div>
// //         ) : (
// //           messages.map((m, i) => (
// //             <div key={i} className={`message ${m.role}`}>
// //               <div className={`bubble ${m.role} ${m.error ? "error" : ""}`}>
// //                 <p>{m.text}</p>
// //                 {m.query && (
// //                   <details className="query-details">
// //                     <summary>View Pandas query</summary>
// //                     <code>{m.query}</code>
// //                   </details>
// //                 )}
// //                 {m.chart && (
// //                   <div className="mini-chart">
// //                     <Plot
// //                       data={m.chart.data}
// //                       layout={{
// //                         ...m.chart.layout,
// //                         autosize: true,
// //                         paper_bgcolor: "transparent",
// //                         plot_bgcolor: "transparent",
// //                         margin: { l: 40, r: 10, t: 30, b: 40 },
// //                         font: { size: 10 },
// //                         showlegend: false,
// //                       }}
// //                       config={{ displayModeBar: false, responsive: true }}
// //                       style={{ width: "100%", height: "180px" }}
// //                       useResizeHandler
// //                     />
// //                   </div>
// //                 )}
// //               </div>
// //             </div>
// //           ))
// //         )}
// //         {loading && (
// //           <div className="message bot">
// //             <div className="bubble bot typing">
// //               <Spinner size={14} color="#6366f1" />
// //               <span>Analysing your data...</span>
// //             </div>
// //           </div>
// //         )}
// //         <div ref={bottomRef} />
// //       </div>

// //       <div className="chat-input-row">
// //         <input
// //           className="chat-input"
// //           placeholder="Ask a business question..."
// //           value={question}
// //           onChange={(e) => setQuestion(e.target.value)}
// //           onKeyDown={(e) => e.key === "Enter" && ask()}
// //           disabled={disabled || loading}
// //         />
// //         <button className="btn btn-primary btn-icon"
// //                 onClick={ask}
// //                 disabled={disabled || loading || !question.trim()}>
// //           {loading ? <Spinner size={16} color="white" /> : <Icon.Send />}
// //         </button>
// //       </div>
// //     </div>
// //   );
// // };


// // // ================================================================
// // // REPORT PANEL
// // // ================================================================
// // const ReportPanel = ({ disabled }) => {
// //   const [report,  setReport]  = useState(null);
// //   const [loading, setLoading] = useState(false);
// //   const [error,   setError]   = useState("");

// //   const generate = async () => {
// //     setLoading(true);
// //     setError("");
// //     try {
// //       const { data } = await api.post("/report");
// //       setReport(data);
// //     } catch (e) {
// //       setError(e.response?.data?.detail || "Report generation failed.");
// //     } finally {
// //       setLoading(false);
// //     }
// //   };

// //   const download = () => {
// //     if (!report) return;
// //     const blob = new Blob([report.report_text], { type: "text/plain" });
// //     const url  = URL.createObjectURL(blob);
// //     const a    = document.createElement("a");
// //     a.href = url; a.download = "executive_report.txt"; a.click();
// //     URL.revokeObjectURL(url);
// //   };

// //   // Format report text into sections
// //   const renderReport = (text) => {
// //     return text.split("\n").map((line, i) => {
// //       line = line.trim();
// //       if (!line) return <div key={i} className="report-spacer" />;
// //       if (line.startsWith("**") && line.endsWith("**"))
// //         return <div key={i} className="report-h">{line.replace(/\*\*/g, "")}</div>;
// //       if (line.match(/^\d\./))
// //         return <div key={i} className="report-h">{line}</div>;
// //       if (line.startsWith("•") || line.startsWith("-") || line.startsWith("*"))
// //         return <div key={i} className="report-bullet">{line}</div>;
// //       return <div key={i} className="report-p">{line}</div>;
// //     });
// //   };

// //   return (
// //     <div className="panel report-panel">
// //       <div className="panel-title">
// //         <span className="icon-wrap"><Icon.Report /></span>
// //         Executive Report
// //         {report && (
// //           <button className="btn btn-outline btn-sm ml-auto" onClick={download}>
// //             <Icon.Download /> Download
// //           </button>
// //         )}
// //       </div>

// //       {!report ? (
// //         <div className="report-empty">
// //           <div className="report-empty-icon">📄</div>
// //           <p>Generate a full executive report with<br/>key findings and recommendations</p>
// //           <button
// //             className={`btn btn-primary ${loading ? "loading" : ""}`}
// //             onClick={generate}
// //             disabled={disabled || loading}
// //           >
// //             {loading
// //               ? <><Spinner size={16} color="white" /> Generating report...</>
// //               : "Generate Report"}
// //           </button>
// //           {error && <div className="error-msg">{error}</div>}
// //         </div>
// //       ) : (
// //         <div className="report-body">
// //           <div className="report-meta">
// //             Generated at {report.generated_at} · by LLaMA 3.2
// //           </div>
// //           <div className="report-content">
// //             {renderReport(report.report_text)}
// //           </div>
// //           <button className="btn btn-ghost btn-sm"
// //                   onClick={() => setReport(null)}>
// //             Regenerate
// //           </button>
// //         </div>
// //       )}
// //     </div>
// //   );
// // };


// // // ================================================================
// // // STATS BAR
// // // ================================================================
// // const StatsBar = ({ uploadData }) => {
// //   if (!uploadData) return null;
// //   const cols = uploadData.column_info || [];
// //   const numericCount  = cols.filter(c => c.dtype.includes("int") || c.dtype.includes("float")).length;
// //   const categoryCount = cols.filter(c => !c.dtype.includes("int") && !c.dtype.includes("float") && !c.dtype.includes("datetime")).length;
// //   const dateCount     = cols.filter(c => c.dtype.includes("datetime")).length;

// //   return (
// //     <div className="stats-bar">
// //       {[
// //         { val: uploadData.rows?.toLocaleString(), label: "Total Rows" },
// //         { val: uploadData.columns, label: "Columns" },
// //         { val: numericCount, label: "Numeric" },
// //         { val: categoryCount, label: "Categorical" },
// //         { val: dateCount, label: "Date" },
// //       ].map(({ val, label }) => (
// //         <div key={label} className="stat-item">
// //           <div className="stat-val">{val}</div>
// //           <div className="stat-label">{label}</div>
// //         </div>
// //       ))}
// //     </div>
// //   );
// // };


// // // ================================================================
// // // DOWNLOAD DASHBOARD  (generates HTML file)
// // // ================================================================
// // const downloadDashboard = (charts, uploadData, prompt) => {
// //   const chartScripts = charts.map((chart, i) => {
// //     const figJson = JSON.stringify(chart.figure_json);
// //     return `
// //     (function() {
// //       var fig = ${figJson};
// //       fig.layout.paper_bgcolor = 'white';
// //       fig.layout.plot_bgcolor  = '#f8faff';
// //       fig.layout.font = {family: "'DM Sans', sans-serif", size: 12};
// //       fig.layout.hoverlabel = {bgcolor: '#111827', font: {color: 'white'}};
// //       if (fig.layout.yaxis) fig.layout.yaxis.tickformat = '.2s';
// //       Plotly.newPlot('c${i}', fig.data, fig.layout, {responsive:true, displayModeBar:true, displaylogo:false});
// //     })();`;
// //   }).join("\n");

// //   const chartDivs = charts.map((c, i) =>
// //     `<div class="card"><div class="card-title">${c.title}</div><div id="c${i}" style="height:420px"></div></div>`
// //   ).join("");

// //   const html = `<!DOCTYPE html>
// // <html><head><meta charset="UTF-8">
// // <title>AI Dashboard — ${uploadData?.filename}</title>
// // <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
// // <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
// // <style>
// // *{box-sizing:border-box;margin:0;padding:0}
// // body{font-family:'DM Sans',sans-serif;background:#f1f3f9;padding:24px}
// // .header{background:#1a1a2e;color:white;padding:20px 28px;border-radius:14px;margin-bottom:20px;display:flex;justify-content:space-between;align-items:center}
// // .header h1{font-size:20px;font-weight:700}
// // .header p{font-size:12px;opacity:0.6;margin-top:4px}
// // .badge{background:#6ee7b7;color:#1a1a2e;font-size:11px;font-weight:600;padding:5px 14px;border-radius:99px}
// // .prompt{background:white;border-radius:12px;padding:14px 20px;margin-bottom:20px;font-size:13px;color:#6b7280;border:1px solid #e5e7eb}
// // .prompt b{color:#1a1a2e}
// // .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(580px,1fr));gap:18px}
// // .card{background:white;border-radius:14px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,0.07);border:1px solid #e5e7eb}
// // .card-title{font-size:14px;font-weight:600;color:#1a1a2e;margin-bottom:14px;padding-bottom:12px;border-bottom:2px solid #f3f4f6}
// // .footer{text-align:center;padding:20px;font-size:11px;color:#9ca3af;margin-top:12px}
// // </style>
// // </head>
// // <body>
// // <div class="header">
// //   <div><h1>AI Dashboard Generator</h1><p>Powered by LLaMA 3.2 · Local · No API cost</p></div>
// //   <span class="badge">✅ ${uploadData?.filename} · ${uploadData?.rows?.toLocaleString()} rows</span>
// // </div>
// // <div class="prompt"><b>Prompt:</b> ${prompt}</div>
// // <div class="grid">${chartDivs}</div>
// // <div class="footer">Generated by AI Dashboard Generator · Hover charts for interactive values · Scroll to zoom</div>
// // <script>${chartScripts}</script>
// // </body></html>`;

// //   const blob = new Blob([html], { type: "text/html" });
// //   const url  = URL.createObjectURL(blob);
// //   const a    = document.createElement("a");
// //   a.href = url; a.download = "dashboard.html"; a.click();
// //   URL.revokeObjectURL(url);
// // };


// // // ================================================================
// // // MAIN APP
// // // ================================================================
// // export default function App() {
// //   const [uploadData,  setUploadData]  = useState(null);
// //   const [charts,      setCharts]      = useState([]);
// //   const [chartsLoading, setChartsLoading] = useState(false);
// //   const [chartsError,   setChartsError]   = useState("");
// //   const [lastPrompt,    setLastPrompt]    = useState("");
// //   const [activeTab,     setActiveTab]     = useState("chat"); // "chat" | "report"

// //   const handleUpload = (data) => {
// //     setUploadData(data);
// //     setCharts([]);
// //     setChartsError("");
// //     setLastPrompt("");
// //   };

// //   const handleGenerate = async (prompt) => {
// //     setChartsLoading(true);
// //     setChartsError("");
// //     setLastPrompt(prompt);
// //     try {
// //       const { data } = await api.post("/generate-charts", { prompt });
// //       setCharts(data.charts || []);
// //     } catch (e) {
// //       setChartsError(e.response?.data?.detail || "Chart generation failed. Try a different prompt.");
// //     } finally {
// //       setChartsLoading(false);
// //     }
// //   };

// //   return (
// //     <div className="app">
// //       {/* ── NAVBAR ─────────────────────────────────────────────── */}
// //       <nav className="navbar">
// //         <div className="nav-brand">
// //           <span className="brand-icon">⚡</span>
// //           AI Dashboard <span className="brand-accent">Generator</span>
// //         </div>
// //         <div className="nav-meta">
// //           Powered by LLaMA 3.2 · Local · No API cost
// //         </div>
// //         {uploadData && (
// //           <div className="nav-status">
// //             <span className="status-dot" />
// //             {uploadData.filename}
// //           </div>
// //         )}
// //       </nav>

// //       {/* ── MAIN LAYOUT ────────────────────────────────────────── */}
// //       <div className="layout">

// //         {/* LEFT SIDEBAR */}
// //         <aside className="sidebar">
// //           <UploadPanel onUploadSuccess={handleUpload} uploadedFile={uploadData} />

// //           {/* BOTTOM TABS */}
// //           <div className="tab-bar">
// //             <button className={`tab ${activeTab === "chat" ? "active" : ""}`}
// //                     onClick={() => setActiveTab("chat")}>
// //               <Icon.Bot /> Chat
// //             </button>
// //             <button className={`tab ${activeTab === "report" ? "active" : ""}`}
// //                     onClick={() => setActiveTab("report")}>
// //               <Icon.Report /> Report
// //             </button>
// //           </div>

// //           {activeTab === "chat"
// //             ? <ChatPanel disabled={!uploadData} />
// //             : <ReportPanel disabled={!uploadData} />}
// //         </aside>

// //         {/* MAIN CONTENT */}
// //         <main className="content">
// //           {/* Stats bar */}
// //           {uploadData && <StatsBar uploadData={uploadData} />}

// //           {/* Prompt bar */}
// //           <PromptBar
// //             onGenerate={handleGenerate}
// //             disabled={!uploadData}
// //             loading={chartsLoading}
// //           />

// //           {/* Charts area */}
// //           {chartsLoading && (
// //             <div className="loading-state">
// //               <Spinner size={40} />
// //               <p>LLaMA 3.2 is generating your dashboard...</p>
// //               <p className="loading-sub">This takes 15–30 seconds</p>
// //             </div>
// //           )}

// //           {chartsError && !chartsLoading && (
// //             <div className="error-banner">⚠️ {chartsError}</div>
// //           )}

// //           {!chartsLoading && charts.length > 0 && (
// //             <DashboardGrid
// //               charts={charts}
// //               onDownload={() => downloadDashboard(charts, uploadData, lastPrompt)}
// //             />
// //           )}

// //           {!chartsLoading && charts.length === 0 && !chartsError && (
// //             <div className="empty-state">
// //               <div className="empty-icon">📊</div>
// //               {uploadData
// //                 ? <><p>Enter a prompt above to generate your dashboard</p>
// //                      <p className="empty-sub">Try: "Show total sales by store and holiday impact"</p></>
// //                 : <><p>Upload a dataset to get started</p>
// //                      <p className="empty-sub">Supports CSV, Excel, JSON, Parquet</p></>}
// //             </div>
// //           )}
// //         </main>

// //       </div>
// //     </div>
// //   );
// // }


// // ================================================================
// // AI DASHBOARD GENERATOR — Fixed App.jsx
// // Fixes:
// //   1. Chart respects prompt filters (store 20, year wise, monthly)
// //   2. Chat bot answers questions (model name resolved in backend)
// //   3. Report generates correctly (model name fix in backend)
// //   4. Downloaded dashboard renders charts correctly (sanitized JSON)
// //   5. Chat history persists when switching tabs
// // ================================================================

// import { useState, useRef, useEffect, useCallback } from "react";
// import axios from "axios";
// import Plot from "react-plotly.js";

// const API = "http://localhost:8000";
// const api = axios.create({ baseURL: API, timeout: 300000 });


// // ================================================================
// // ICONS
// // ================================================================
// const Icon = {
//   Upload:   () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/></svg>,
//   Chart:    () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>,
//   Send:     () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>,
//   Report:   () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>,
//   Download: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>,
//   Expand:   () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>,
//   Close:    () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>,
//   Spark:    () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>,
//   Bot:      () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4M8 15h.01M16 15h.01"/></svg>,
//   Clear:    () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/><path d="M10 11v6M14 11v6"/></svg>,
// };

// const Spinner = ({ size = 20, color = "#6366f1" }) => (
//   <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
//        style={{ animation: "spin 0.8s linear infinite" }}>
//     <circle cx="12" cy="12" r="10" stroke={color} strokeWidth="3" strokeOpacity="0.2"/>
//     <path d="M12 2a10 10 0 0110 10" stroke={color} strokeWidth="3" strokeLinecap="round"/>
//   </svg>
// );


// // ================================================================
// // FIX 4: Sanitize figure JSON for download
// // Plotly's to_json() uses binary encoding (dtype/bdata) for large arrays
// // which the CDN version cannot decode. We must convert to plain arrays.
// // ================================================================
// const sanitizeFigureForDownload = (figureJson) => {
//   const fig = JSON.parse(JSON.stringify(figureJson)); // deep clone

//   const decodeIfNeeded = (val) => {
//     // If it's already an array, return as-is
//     if (Array.isArray(val)) return val;
//     // If it's a binary-encoded object {dtype, bdata}, return empty array
//     // The chart will re-render from layout info
//     if (val && typeof val === "object" && val.bdata !== undefined) return [];
//     return val;
//   };

//   if (fig.data) {
//     fig.data = fig.data.map(trace => {
//       const t = { ...trace };
//       ["x", "y", "z", "text", "marker"].forEach(key => {
//         if (t[key] !== undefined) t[key] = decodeIfNeeded(t[key]);
//       });
//       if (t.marker && typeof t.marker === "object") {
//         if (t.marker.color !== undefined)
//           t.marker = { ...t.marker, color: decodeIfNeeded(t.marker.color) };
//       }
//       return t;
//     });
//   }
//   return fig;
// };


// // ================================================================
// // DOWNLOAD DASHBOARD — Fixed: uses sanitized JSON
// // ================================================================
// const downloadDashboard = (charts, uploadData, prompt) => {
//   const chartDivs = charts.map((c, i) =>
//     `<div class="card"><div class="ct">${c.title}</div><div id="c${i}" style="height:420px;width:100%"></div></div>`
//   ).join("");

//   // FIX: sanitize before embedding in HTML
//   const chartScripts = charts.map((chart, i) => {
//     const sanitized = sanitizeFigureForDownload(chart.figure_json);
//     const figStr    = JSON.stringify(sanitized);
//     return `
//   (function(){
//     try {
//       var f=${figStr};
//       f.layout=f.layout||{};
//       f.layout.paper_bgcolor='white';
//       f.layout.plot_bgcolor='#f8faff';
//       f.layout.font={family:"'DM Sans',sans-serif",size:12,color:'#374151'};
//       f.layout.hoverlabel={bgcolor:'#111827',font:{color:'white',size:12}};
//       f.layout.autosize=true;
//       if(f.layout.yaxis)f.layout.yaxis.tickformat='.2s';
//       if(f.layout.xaxis){f.layout.xaxis.gridcolor='#f0f1f6';f.layout.xaxis.zeroline=false;}
//       if(f.layout.yaxis){f.layout.yaxis.gridcolor='#f0f1f6';f.layout.yaxis.zeroline=false;}
//       Plotly.newPlot('c${i}',f.data,f.layout,{responsive:true,displayModeBar:true,displaylogo:false,
//         toImageButtonOptions:{format:'png',filename:'${chart.title.replace(/'/g,"")}',height:600,width:1200,scale:2}});
//     } catch(e){document.getElementById('c${i}').innerHTML='<p style="color:red;padding:20px">Chart error: '+e+'</p>';}
//   })();`;
//   }).join("\n");

//   const html = `<!DOCTYPE html>
// <html lang="en"><head>
// <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
// <title>AI Dashboard — ${uploadData?.filename || "Report"}</title>
// <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"><\/script>
// <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
// <style>
// *{box-sizing:border-box;margin:0;padding:0}
// body{font-family:'DM Sans',sans-serif;background:#f1f3f9;padding:24px;min-height:100vh}
// .header{background:#1a1a2e;color:white;padding:20px 28px;border-radius:14px;margin-bottom:20px;
//         display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}
// .header h1{font-size:20px;font-weight:700}.header h1 span{color:#818cf8}
// .header p{font-size:12px;opacity:0.5;margin-top:4px}
// .badge{background:#6ee7b7;color:#1a1a2e;font-size:11px;font-weight:600;padding:5px 14px;border-radius:99px}
// .prompt{background:white;border-radius:12px;padding:14px 20px;margin-bottom:20px;
//         font-size:13px;color:#6b7280;border:1px solid #e5e7eb}
// .prompt b{color:#1a1a2e}
// .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(560px,1fr));gap:18px}
// .card{background:white;border-radius:14px;padding:20px;
//       box-shadow:0 2px 8px rgba(0,0,0,0.07);border:1px solid #e5e7eb}
// .ct{font-size:14px;font-weight:600;color:#1a1a2e;margin-bottom:14px;
//     padding-bottom:12px;border-bottom:2px solid #f3f4f6}
// .footer{text-align:center;padding:24px;font-size:11px;color:#9ca3af;margin-top:12px}
// </style></head><body>
// <div class="header">
//   <div><h1>AI <span>Dashboard</span> Generator</h1>
//   <p>Powered by LLaMA 3.2 · Local · No API cost · ${new Date().toLocaleDateString()}</p></div>
//   <span class="badge">✅ ${uploadData?.filename || ""} · ${uploadData?.rows?.toLocaleString() || ""} rows</span>
// </div>
// <div class="prompt"><b>Prompt used:</b> ${prompt}</div>
// <div class="grid">${chartDivs}</div>
// <div class="footer">
//   AI Dashboard Generator · Hover charts for exact values · Scroll to zoom · 📷 Camera icon to download each chart as PNG
// </div>
// <script>${chartScripts}<\/script>
// </body></html>`;

//   const blob = new Blob([html], { type: "text/html" });
//   const url  = URL.createObjectURL(blob);
//   const a    = document.createElement("a");
//   a.href = url; a.download = "ai_dashboard.html"; a.click();
//   URL.revokeObjectURL(url);
// };


// // ================================================================
// // UPLOAD PANEL
// // ================================================================
// const UploadPanel = ({ onUploadSuccess, uploadedFile }) => {
//   const [dragging, setDragging] = useState(false);
//   const [loading,  setLoading]  = useState(false);
//   const [error,    setError]    = useState("");
//   const inputRef = useRef();

//   const handleFile = useCallback(async (file) => {
//     if (!file) return;
//     const ext = "." + file.name.split(".").pop().toLowerCase();
//     if (![".csv",".xlsx",".xls",".json",".parquet",".tsv"].includes(ext)) {
//       setError(`Unsupported format: ${ext}`); return;
//     }
//     setLoading(true); setError("");
//     try {
//       const fd = new FormData();
//       fd.append("file", file);
//       const { data } = await api.post("/upload", fd,
//         { headers: { "Content-Type": "multipart/form-data" } });
//       onUploadSuccess(data);
//     } catch (e) {
//       setError(e.response?.data?.detail || "Upload failed. Is FastAPI running?");
//     } finally { setLoading(false); }
//   }, [onUploadSuccess]);

//   return (
//     <div className="panel upload-panel">
//       <div className="panel-title">
//         <span className="icon-wrap"><Icon.Upload /></span>
//         Upload Dataset
//       </div>
//       {!uploadedFile ? (
//         <div className={`drop-zone ${dragging?"dragging":""} ${loading?"loading":""}`}
//              onDragOver={(e)=>{e.preventDefault();setDragging(true);}}
//              onDragLeave={()=>setDragging(false)}
//              onDrop={(e)=>{e.preventDefault();setDragging(false);handleFile(e.dataTransfer.files[0]);}}
//              onClick={()=>inputRef.current?.click()}>
//           <input ref={inputRef} type="file" accept=".csv,.xlsx,.xls,.json,.parquet,.tsv"
//                  style={{display:"none"}} onChange={(e)=>handleFile(e.target.files[0])}/>
//           {loading
//             ? <div className="drop-content"><Spinner size={32}/><p>Processing data...</p></div>
//             : <div className="drop-content">
//                 <div className="drop-icon">📂</div>
//                 <p className="drop-main">Drag & drop your file here</p>
//                 <p className="drop-sub">CSV · Excel · JSON · Parquet · TSV</p>
//                 <button className="btn btn-outline">Browse files</button>
//               </div>}
//         </div>
//       ) : (
//         <div className="upload-success">
//           <div className="success-header">
//             <span className="success-icon">✅</span>
//             <div>
//               <div className="success-name">{uploadedFile.filename}</div>
//               <div className="success-meta">{uploadedFile.rows?.toLocaleString()} rows · {uploadedFile.columns} columns</div>
//             </div>
//           </div>
//           <div className="cleaning-tags">
//             {uploadedFile.cleaning_summary?.duplicates_removed > 0 &&
//               <span className="ctag green">✓ {uploadedFile.cleaning_summary.duplicates_removed} dupes removed</span>}
//             {uploadedFile.cleaning_summary?.memory_saved_mb > 0 &&
//               <span className="ctag blue">✓ {uploadedFile.cleaning_summary.memory_saved_mb?.toFixed(1)}MB saved</span>}
//             <span className="ctag green">✓ Data cleaned</span>
//           </div>
//           <div className="col-list">
//             {uploadedFile.column_info?.slice(0,8).map(c=>(
//               <span key={c.name} className={`col-badge ${
//                 c.dtype.includes("int")||c.dtype.includes("float")?"num":
//                 c.dtype.includes("datetime")?"date":"cat"}`}>{c.name}</span>
//             ))}
//             {uploadedFile.column_info?.length>8 &&
//               <span className="col-badge more">+{uploadedFile.column_info.length-8} more</span>}
//           </div>
//           <button className="btn btn-ghost btn-sm"
//                   onClick={()=>{onUploadSuccess(null);setTimeout(()=>inputRef.current?.click(),100);}}>
//             Upload different file
//           </button>
//         </div>
//       )}
//       {error && <div className="error-msg">{error}</div>}
//     </div>
//   );
// };


// // ================================================================
// // PROMPT BAR
// // ================================================================
// const PromptBar = ({ onGenerate, disabled, loading }) => {
//   const [prompt, setPrompt] = useState("");
//   const examples = [
//     "Show sales by store and holiday impact",
//     "Year wise sales trend for store 20",
//     "Monthly sales comparison 2010 vs 2011",
//     "Top 10 stores by total sales",
//   ];
//   const submit = () => { if (!prompt.trim()||loading) return; onGenerate(prompt.trim()); };
//   return (
//     <div className="prompt-section">
//       <div className="prompt-bar">
//         <span className="prompt-icon"><Icon.Spark /></span>
//         <input className="prompt-input"
//                placeholder="Describe what you want... e.g. 'Show year wise sales for store 20'"
//                value={prompt} onChange={e=>setPrompt(e.target.value)}
//                onKeyDown={e=>e.key==="Enter"&&submit()} disabled={disabled||loading}/>
//         <button className={`btn btn-primary ${loading?"loading":""}`}
//                 onClick={submit} disabled={disabled||loading||!prompt.trim()}>
//           {loading ? <><Spinner size={16} color="white"/> Generating...</> : "Generate Dashboard"}
//         </button>
//       </div>
//       {!disabled && (
//         <div className="example-prompts">
//           <span className="example-label">Try:</span>
//           {examples.map(ex=>(
//             <button key={ex} className="example-chip" onClick={()=>setPrompt(ex)}>{ex}</button>
//           ))}
//         </div>
//       )}
//     </div>
//   );
// };


// // ================================================================
// // CHART MODAL
// // ================================================================
// const ChartModal = ({ chart, onClose }) => {
//   useEffect(()=>{
//     const h=e=>{if(e.key==="Escape")onClose();};
//     window.addEventListener("keydown",h);
//     return ()=>window.removeEventListener("keydown",h);
//   },[onClose]);
//   return (
//     <div className="modal-overlay" onClick={onClose}>
//       <div className="modal-box" onClick={e=>e.stopPropagation()}>
//         <div className="modal-header">
//           <span className="modal-title">{chart.title}</span>
//           <button className="icon-btn" onClick={onClose}><Icon.Close/></button>
//         </div>
//         <div className="modal-body">
//           <Plot data={chart.figure_json.data}
//                 layout={{...chart.figure_json.layout, autosize:true,
//                          paper_bgcolor:"white", plot_bgcolor:"#f8faff",
//                          font:{family:"'DM Sans',sans-serif",size:13},
//                          hoverlabel:{bgcolor:"#111827",font:{color:"white",size:12}},
//                          margin:{l:70,r:40,t:60,b:70}}}
//                 config={{responsive:true,displayModeBar:true,displaylogo:false,
//                          modeBarButtonsToRemove:["lasso2d","select2d"],
//                          toImageButtonOptions:{format:"png",filename:chart.title,scale:2}}}
//                 style={{width:"100%",height:"100%"}} useResizeHandler/>
//         </div>
//       </div>
//     </div>
//   );
// };


// // ================================================================
// // DASHBOARD GRID
// // ================================================================
// const DashboardGrid = ({ charts, onDownload }) => {
//   const [fullscreen, setFullscreen] = useState(null);
//   if (!charts.length) return null;
//   const plotLayout = (chart) => ({
//     ...chart.figure_json.layout, autosize:true,
//     paper_bgcolor:"white", plot_bgcolor:"#f8faff",
//     font:{family:"'DM Sans',sans-serif",size:11,color:"#374151"},
//     hoverlabel:{bgcolor:"#111827",font:{color:"white",size:11},bordercolor:"#111827"},
//     hovermode:"closest", margin:{l:55,r:20,t:45,b:55},
//     showlegend:true,
//     legend:{bgcolor:"rgba(255,255,255,0.9)",bordercolor:"#e5e7eb",borderwidth:1,font:{size:10}},
//     xaxis:{...chart.figure_json.layout?.xaxis,gridcolor:"#f0f1f6",linecolor:"#e5e7eb",zeroline:false},
//     yaxis:{...chart.figure_json.layout?.yaxis,gridcolor:"#f0f1f6",linecolor:"#e5e7eb",zeroline:false,tickformat:".2s"},
//   });
//   return (
//     <>
//       <div className="dashboard-header">
//         <h2 className="section-title">
//           <span className="icon-wrap"><Icon.Chart/></span>
//           Dashboard — {charts.length} charts
//         </h2>
//         <button className="btn btn-outline btn-sm" onClick={onDownload}>
//           <Icon.Download/> Download Dashboard
//         </button>
//       </div>
//       <div className={`charts-grid cols-${Math.min(charts.length,2)}`}>
//         {charts.map((chart,i)=>(
//           <div key={i} className="chart-card">
//             <div className="chart-card-header">
//               <span className="chart-card-title">{chart.title}</span>
//               <button className="icon-btn" title="Fullscreen"
//                       onClick={()=>setFullscreen(chart)}><Icon.Expand/></button>
//             </div>
//             <div className="chart-wrap">
//               <Plot data={chart.figure_json.data} layout={plotLayout(chart)}
//                     config={{responsive:true,displayModeBar:true,displaylogo:false,
//                              modeBarButtonsToRemove:["lasso2d","select2d","autoScale2d"],
//                              toImageButtonOptions:{format:"png",filename:chart.title,
//                                height:600,width:1200,scale:2}}}
//                     style={{width:"100%",height:"100%"}} useResizeHandler/>
//             </div>
//           </div>
//         ))}
//       </div>
//       {fullscreen && <ChartModal chart={fullscreen} onClose={()=>setFullscreen(null)}/>}
//     </>
//   );
// };


// // ================================================================
// // FIX 5: CHAT PANEL — receives messages + setMessages from parent
// // so history persists when switching between Chat and Report tabs
// // ================================================================
// const ChatPanel = ({ disabled, messages, setMessages }) => {
//   const [question, setQuestion] = useState("");
//   const [loading,  setLoading]  = useState(false);
//   const bottomRef = useRef();

//   useEffect(()=>{
//     bottomRef.current?.scrollIntoView({behavior:"smooth"});
//   },[messages]);

//   const ask = async () => {
//     if (!question.trim()||loading||disabled) return;
//     const q = question.trim();
//     setQuestion("");
//     setMessages(m=>[...m,{role:"user",text:q}]);
//     setLoading(true);
//     try {
//       const {data} = await api.post("/ask",{question:q});
//       setMessages(m=>[...m,{
//         role:"bot", text:data.answer,
//         query:data.pandas_query, result:data.raw_result, chart:data.mini_chart
//       }]);
//     } catch(e) {
//       setMessages(m=>[...m,{
//         role:"bot",
//         text:e.response?.data?.detail||"Could not answer. Check if Ollama is running.",
//         error:true
//       }]);
//     } finally { setLoading(false); }
//   };

//   const suggestions = [
//     "Which store had the highest total sales?",
//     "What is the average weekly sales across all stores?",
//     "How many weeks had holiday=1?",
//     "What is the total revenue for 2011?",
//     "Which store had the lowest sales?",
//     "What was the max weekly sales ever recorded?",
//   ];

//   return (
//     <div className="panel chat-panel">
//       <div className="panel-title">
//         <span className="icon-wrap"><Icon.Bot/></span>
//         Ask Business Questions
//         {messages.length>0 && (
//           <button className="icon-btn ml-auto" title="Clear chat"
//                   onClick={()=>setMessages([])}><Icon.Clear/></button>
//         )}
//       </div>
//       <div className="chat-body">
//         {messages.length===0 ? (
//           <div className="chat-empty">
//             <div className="chat-empty-icon">💬</div>
//             <p>Ask anything about your data</p>
//             {!disabled && (
//               <div className="suggestions">
//                 {suggestions.map(s=>(
//                   <button key={s} className="suggestion-chip"
//                           onClick={()=>setQuestion(s)}>{s}</button>
//                 ))}
//               </div>
//             )}
//             {disabled && <p className="chat-disabled">Upload a dataset first</p>}
//           </div>
//         ) : (
//           messages.map((m,i)=>(
//             <div key={i} className={`message ${m.role}`}>
//               <div className={`bubble ${m.role} ${m.error?"error":""}`}>
//                 <p>{m.text}</p>
//                 {m.query && (
//                   <details className="query-details">
//                     <summary>View Pandas query used</summary>
//                     <code>{m.query}</code>
//                   </details>
//                 )}
//                 {m.chart && (
//                   <div className="mini-chart">
//                     <Plot data={m.chart.data}
//                           layout={{...m.chart.layout, autosize:true,
//                                    paper_bgcolor:"transparent", plot_bgcolor:"transparent",
//                                    margin:{l:40,r:10,t:30,b:40}, font:{size:10}, showlegend:false}}
//                           config={{displayModeBar:false,responsive:true}}
//                           style={{width:"100%",height:"180px"}} useResizeHandler/>
//                   </div>
//                 )}
//               </div>
//             </div>
//           ))
//         )}
//         {loading && (
//           <div className="message bot">
//             <div className="bubble bot typing">
//               <Spinner size={14} color="#6366f1"/>
//               <span>Analysing your data...</span>
//             </div>
//           </div>
//         )}
//         <div ref={bottomRef}/>
//       </div>
//       <div className="chat-input-row">
//         <input className="chat-input" placeholder="Ask a business question..."
//                value={question} onChange={e=>setQuestion(e.target.value)}
//                onKeyDown={e=>e.key==="Enter"&&ask()} disabled={disabled||loading}/>
//         <button className="btn btn-primary btn-icon" onClick={ask}
//                 disabled={disabled||loading||!question.trim()}>
//           {loading ? <Spinner size={16} color="white"/> : <Icon.Send/>}
//         </button>
//       </div>
//     </div>
//   );
// };


// // ================================================================
// // REPORT PANEL
// // ================================================================
// const ReportPanel = ({ disabled }) => {
//   const [report,  setReport]  = useState(null);
//   const [loading, setLoading] = useState(false);
//   const [error,   setError]   = useState("");

//   const generate = async () => {
//     setLoading(true); setError("");
//     try {
//       const {data} = await api.post("/report");
//       setReport(data);
//     } catch(e) {
//       const msg = e.response?.data?.detail || "Report generation failed.";
//       setError(msg);
//     } finally { setLoading(false); }
//   };

//   const download = () => {
//     if (!report) return;
//     const blob = new Blob([report.report_text],{type:"text/plain"});
//     const url  = URL.createObjectURL(blob);
//     const a    = document.createElement("a");
//     a.href=url; a.download="executive_report.txt"; a.click();
//     URL.revokeObjectURL(url);
//   };

//   const renderReport = (text) => text.split("\n").map((line,i)=>{
//     line=line.trim();
//     if (!line) return <div key={i} className="report-spacer"/>;
//     if ((line.startsWith("**")&&line.endsWith("**"))||line.match(/^\d\./))
//       return <div key={i} className="report-h">{line.replace(/\*\*/g,"")}</div>;
//     if (line.startsWith("•")||line.startsWith("-")||line.startsWith("*"))
//       return <div key={i} className="report-bullet">{line}</div>;
//     return <div key={i} className="report-p">{line}</div>;
//   });

//   return (
//     <div className="panel report-panel">
//       <div className="panel-title">
//         <span className="icon-wrap"><Icon.Report/></span>
//         Executive Report
//         {report && (
//           <button className="btn btn-outline btn-sm ml-auto" onClick={download}>
//             <Icon.Download/> Download
//           </button>
//         )}
//       </div>
//       {!report ? (
//         <div className="report-empty">
//           <div className="report-empty-icon">📄</div>
//           <p>Generate a full executive report with key findings and recommendations</p>
//           <button className={`btn btn-primary ${loading?"loading":""}`}
//                   onClick={generate} disabled={disabled||loading}>
//             {loading ? <><Spinner size={16} color="white"/> Generating...</> : "Generate Report"}
//           </button>
//           {error && <div className="error-msg" style={{marginTop:10,maxWidth:260,textAlign:"center"}}>{error}</div>}
//         </div>
//       ) : (
//         <div className="report-body">
//           <div className="report-meta">Generated {report.generated_at} · LLaMA 3.2</div>
//           <div className="report-content">{renderReport(report.report_text)}</div>
//           <button className="btn btn-ghost btn-sm" onClick={()=>setReport(null)}>Regenerate</button>
//         </div>
//       )}
//     </div>
//   );
// };


// // ================================================================
// // STATS BAR
// // ================================================================
// const StatsBar = ({ uploadData }) => {
//   if (!uploadData) return null;
//   const cols = uploadData.column_info || [];
//   const num  = cols.filter(c=>c.dtype.includes("int")||c.dtype.includes("float")).length;
//   const cat  = cols.filter(c=>!c.dtype.includes("int")&&!c.dtype.includes("float")&&!c.dtype.includes("datetime")).length;
//   const dat  = cols.filter(c=>c.dtype.includes("datetime")).length;
//   return (
//     <div className="stats-bar">
//       {[
//         {val:uploadData.rows?.toLocaleString(),label:"Total Rows"},
//         {val:uploadData.columns,label:"Columns"},
//         {val:num,label:"Numeric"},
//         {val:cat,label:"Categorical"},
//         {val:dat,label:"Date"},
//       ].map(({val,label})=>(
//         <div key={label} className="stat-item">
//           <div className="stat-val">{val}</div>
//           <div className="stat-label">{label}</div>
//         </div>
//       ))}
//     </div>
//   );
// };


// // ================================================================
// // MAIN APP
// // FIX 5: chatMessages lives here (App level) — persists across tab switches
// // ================================================================
// export default function App() {
//   const [uploadData,      setUploadData]      = useState(null);
//   const [charts,          setCharts]          = useState([]);
//   const [chartsLoading,   setChartsLoading]   = useState(false);
//   const [chartsError,     setChartsError]     = useState("");
//   const [lastPrompt,      setLastPrompt]      = useState("");
//   const [activeTab,       setActiveTab]       = useState("chat");

//   // FIX 5: chat history lives in App so it persists across tab switches
//   const [chatMessages, setChatMessages] = useState([]);

//   const handleUpload = (data) => {
//     setUploadData(data);
//     setCharts([]);
//     setChartsError("");
//     setLastPrompt("");
//     // Clear chat when new dataset is uploaded
//     setChatMessages([]);
//   };

//   const handleGenerate = async (prompt) => {
//     setChartsLoading(true); setChartsError(""); setLastPrompt(prompt);
//     try {
//       const {data} = await api.post("/generate-charts",{prompt});
//       setCharts(data.charts||[]);
//     } catch(e) {
//       setChartsError(e.response?.data?.detail||"Chart generation failed. Try a different prompt.");
//     } finally { setChartsLoading(false); }
//   };

//   return (
//     <div className="app">
//       <nav className="navbar">
//         <div className="nav-brand">
//           <span className="brand-icon">⚡</span>
//           AI Dashboard <span className="brand-accent">Generator</span>
//         </div>
//         <div className="nav-meta">Powered by LLaMA 3.2 · Local · No API cost</div>
//         {uploadData && (
//           <div className="nav-status">
//             <span className="status-dot"/>
//             {uploadData.filename}
//           </div>
//         )}
//       </nav>

//       <div className="layout">
//         {/* ── SIDEBAR ──────────────────────────────────────── */}
//         <aside className="sidebar">
//           <UploadPanel onUploadSuccess={handleUpload} uploadedFile={uploadData}/>

//           <div className="tab-bar">
//             <button className={`tab ${activeTab==="chat"?"active":""}`}
//                     onClick={()=>setActiveTab("chat")}>
//               <Icon.Bot/> Chat
//               {/* FIX 5: show message count badge */}
//               {chatMessages.length>0 &&
//                 <span className="tab-badge">{chatMessages.filter(m=>m.role==="user").length}</span>}
//             </button>
//             <button className={`tab ${activeTab==="report"?"active":""}`}
//                     onClick={()=>setActiveTab("report")}>
//               <Icon.Report/> Report
//             </button>
//           </div>

//           {/* FIX 5: pass messages and setter to ChatPanel */}
//           {activeTab==="chat"
//             ? <ChatPanel disabled={!uploadData}
//                          messages={chatMessages}
//                          setMessages={setChatMessages}/>
//             : <ReportPanel disabled={!uploadData}/>}
//         </aside>

//         {/* ── MAIN CONTENT ─────────────────────────────────── */}
//         <main className="content">
//           {uploadData && <StatsBar uploadData={uploadData}/>}

//           <PromptBar onGenerate={handleGenerate}
//                      disabled={!uploadData} loading={chartsLoading}/>

//           {chartsLoading && (
//             <div className="loading-state">
//               <Spinner size={40}/>
//               <p>LLaMA 3.2 is planning your dashboard...</p>
//               <p className="loading-sub">This takes 15–30 seconds</p>
//             </div>
//           )}

//           {chartsError && !chartsLoading && (
//             <div className="error-banner">⚠️ {chartsError}</div>
//           )}

//           {!chartsLoading && charts.length>0 && (
//             <DashboardGrid charts={charts}
//                            onDownload={()=>downloadDashboard(charts,uploadData,lastPrompt)}/>
//           )}

//           {!chartsLoading && charts.length===0 && !chartsError && (
//             <div className="empty-state">
//               <div className="empty-icon">📊</div>
//               {uploadData
//                 ? <><p>Enter a prompt above to generate your dashboard</p>
//                      <p className="empty-sub">Try: "Year wise sales for store 20" or "Show holiday impact"</p></>
//                 : <><p>Upload a dataset to get started</p>
//                      <p className="empty-sub">Supports CSV · Excel · JSON · Parquet</p></>}
//             </div>
//           )}
//         </main>
//       </div>
//     </div>
//   );
// }
