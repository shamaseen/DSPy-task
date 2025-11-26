# Retail Analytics Copilot

A hybrid RAG + SQL agent for retail analytics using DSPy and LangGraph. Combines document retrieval with database queries to answer analytics questions with typed, auditable results.

## Features

- **Hybrid RAG+SQL**: Combines document search (BM25) with SQL queries over Northwind database
- **7-Node LangGraph**: Router, Retriever, Planner, SQL Generator, Executor, Synthesizer, Repair Loop
- **DSPy Optimization**: Optimized SQL generation with BootstrapFewShot
- **Typed Outputs**: Returns answers in specified format (int, float, objects, lists)
- **Citations**: Tracks sources from both database tables and document chunks
- **Repair Loop**: Automatically retries failed SQL queries (up to 2 attempts)
- **100% Local**: Runs entirely on your machine with Ollama

## Architecture

```
Question → Router → Retriever → Planner → SQL Gen → Executor → Synthesizer → Answer
                                             ↓ error ↓
                                            Repair (x2)
```

## Requirements

- Python 3.9+
- Ollama running locally
- 16GB RAM recommended

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Pull Ollama model:**
```bash
ollama pull phi3.5:3.8b-mini-instruct-q4_K_M
```

3. **Verify database:**
```bash
ls -lh data/northwind.sqlite
```

## Usage

### Run Agent

Process evaluation questions:

```bash
python run_agent_hybrid.py \
  --batch sample_questions_hybrid_eval.jsonl \
  --out outputs_hybrid.jsonl
```

### Optimize SQL Generator

Train the SQL generator with examples:

```bash
python optimize_agent.py
```

This creates `agent/optimized_sql_gen.json` which the agent automatically loads.

## Output Format

Each output in `outputs_hybrid.jsonl`:

```json
{
  "id": "question_id",
  "final_answer": <typed_value>,
  "sql": "SELECT ...",
  "confidence": 0.8,
  "explanation": "Brief explanation",
  "citations": ["Orders", "Products", "kpi_definitions::chunk2"]
}
```

## Project Structure

```
├── agent/
│   ├── dspy_signatures.py      # DSPy modules (Router, Planner, SQL, Synthesizer)
│   ├── graph_hybrid.py         # LangGraph workflow
│   ├── rag/retrieval.py        # BM25 document search
│   ├── tools/sqlite_tool.py    # Database access
│   └── optimized_sql_gen.json  # Trained SQL generator
├── data/
│   └── northwind.sqlite        # Retail database
├── docs/
│   ├── marketing_calendar.md   # Campaign dates
│   ├── kpi_definitions.md      # Metric formulas
│   ├── catalog.md              # Product categories
│   └── product_policy.md       # Return policies
├── run_agent_hybrid.py         # Main CLI
├── optimize_agent.py           # DSPy training script
├── train_examples.json         # SQL training data
└── requirements.txt            # Dependencies
```

## How It Works

1. **Router** classifies question (RAG/SQL/Hybrid)
2. **Retriever** searches documents with BM25
3. **Planner** extracts constraints (dates, KPIs) from docs
4. **SQL Generator** writes SQLite query using schema
5. **Executor** runs query on Northwind database
6. **Repair** retries on SQL errors (up to 2x)
7. **Synthesizer** creates typed answer with citations

## Technologies

- **DSPy**: Declarative LLM programming & optimization
- **LangGraph**: Stateful agent workflow
- **Ollama**: Local LLM inference (Phi-3.5)
- **BM25**: Document ranking algorithm
- **SQLite**: Local database (Northwind)
- **Pydantic**: Type validation

## License

MIT
