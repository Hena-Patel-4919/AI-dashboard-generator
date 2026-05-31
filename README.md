# AI-dashboard-generator

# AI Dashboard Generator

AI Dashboard Generator is an AI-powered business intelligence application that enables users to upload datasets, explore data through natural language, generate interactive dashboards, and create executive reports automatically. The goal of the project is to simplify data analysis for non-technical users by allowing them to interact with data using plain English instead of writing SQL queries, Python code, or creating dashboards manually.

The system is built using FastAPI for the backend, React for the frontend, Plotly for data visualization, and Ollama with the Llama 3.2 model for AI-powered analysis. Users can upload datasets in formats such as CSV, Excel, JSON, TSV, and Parquet. Once uploaded, the dataset is automatically cleaned and preprocessed by handling missing values, removing duplicates, optimizing data types, and generating metadata that helps the AI understand the structure of the data.

For dashboard generation, the user provides a prompt such as "Show the top 10 stores by sales" or "Compare holiday and non-holiday sales." The LLM analyzes the dataset schema and user request and generates chart specifications such as chart type, X-axis column, Y-axis column, aggregation method, sorting order, and filtering conditions. These specifications are then used by the backend to build interactive Plotly visualizations, which are converted into JSON format and displayed on the frontend.

The project also includes a Question & Answer module where users can ask business-related questions in natural language. The LLM generates executable Pandas code based on the dataset schema and the user's question. This code is safely validated and executed on the dataset, after which the result is converted into a business-friendly explanation. For tabular results, the system can also generate a small visualization automatically.

Another important feature is automated report generation. The system analyzes the uploaded dataset, creates a statistical summary, and uses the LLM to generate a structured business report containing an executive summary, key findings, top performers, areas of concern, and actionable recommendations.

Workflow:

User uploads a dataset.

The dataset is cleaned and preprocessed.

Metadata and schema information are generated.

For dashboard requests, the LLM generates chart specifications and the backend builds interactive Plotly charts.

For questions, the LLM generates Pandas queries, the backend executes them, and returns business insights.

For reports, the system summarizes the dataset and generates an executive-level report.

This project demonstrates how Large Language Models can be integrated with traditional data analytics pipelines to create intelligent self-service dashboards, business reports, and conversational analytics platforms.
