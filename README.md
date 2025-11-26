# Retail Analytics Copilot

A local, free AI agent that answers retail analytics questions using DSPy and LangGraph.

## Graph Design
- **Router**: Classifies questions as RAG, SQL, or Hybrid.
- **Retriever**: Fetches relevant documentation chunks using BM25.
- **Planner**: Extracts constraints, date ranges, and KPIs from documents.
- **SQL Generator**: Converts natural language to SQLite queries using the Northwind schema.
- **Executor**: Runs the SQL queries on the local database.
- **Synthesizer**: Combines SQL results and retrieved documents to produce a typed, cited answer.
- **Repair Loop**: Retries failed SQL queries up to 2 times with error feedback.

## DSPy Optimization
- **Module**: `CoT_SQL` (NL -> SQL generation).
- **Optimizer**: `BootstrapFewShot`.
- **Metric**: Basic SQL validation (non-empty, contains SELECT).
- **Improvement**: The optimization process aims to improve the validity and accuracy of generated SQL queries by bootstrapping from a small set of examples.

## Trade-offs & Assumptions
- **CostOfGoods**: Approximated as 0.7 * UnitPrice where missing, as per assignment instructions.
- **Local Model**: Assumes `phi3.5:3.8b-mini-instruct-q4_K_M` is available via Ollama.
- **Retriever**: Uses simple paragraph-level chunking and BM25.

## How to Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Ensure Ollama is running with the required model:
   ```bash
   # Pull the model (this may take several minutes)
   ollama pull phi3.5:3.8b-mini-instruct-q4_K_M
   
   # Verify the model is available
   ollama list
   ```
3. Run the agent:
   ```bash
   python run_agent_hybrid.py --batch sample_questions_hybrid_eval.jsonl --out outputs_hybrid.jsonl
   ```
4. (Optional) Run optimization:
   ```bash
   python optimize_agent.py
   ```

## Troubleshooting
- **Model not found error**: Make sure Ollama is running (`ollama serve`) and the model is pulled.
- **Connection error**: Verify Ollama is accessible at `http://localhost:11434`.
- **Pydantic warning about "schema"**: This is expected and won't affect functionality.

