import dspy
from typing import List, Optional

class Router(dspy.Signature):
    """Classify the user question into one of the following categories: 'rag', 'sql', 'hybrid'."""
    
    question = dspy.InputField(desc="The user's question about retail analytics.")
    classification = dspy.OutputField(desc="One of: 'rag', 'sql', 'hybrid'.")

class GenerateSQL(dspy.Signature):
    """Generate a SQLite query based on the question, schema, and plan."""
    
    question = dspy.InputField()
    plan = dspy.InputField(desc="Execution plan with constraints and entities.")
    db_schema = dspy.InputField(desc="Schema of the available tables.")
    sql_query = dspy.OutputField(desc="The SQLite query to answer the question.")

class Planner(dspy.Signature):
    """Extract constraints, date ranges, and entities from the question and docs."""
    
    question = dspy.InputField()
    retrieved_docs = dspy.InputField(desc="Relevant document chunks.")
    plan = dspy.OutputField(desc="Step-by-step plan including date ranges, KPIs, and entities.")

class SynthesizeAnswer(dspy.Signature):
    """Synthesize a final answer based on the question, SQL results, and retrieved documents."""
    
    question = dspy.InputField()
    sql_query = dspy.InputField(desc="The SQL query executed, if any.")
    sql_result = dspy.InputField(desc="The result of the SQL query, if any.")
    retrieved_docs = dspy.InputField(desc="Relevant document chunks from the knowledge base.")
    format_hint = dspy.InputField(desc="The expected format of the answer (e.g., int, float, list[dict]).")
    
    final_answer = dspy.OutputField(desc="The answer matching the format hint.")
    explanation = dspy.OutputField(desc="A brief explanation (<= 2 sentences).")
    citations = dspy.OutputField(desc="List of DB tables and doc chunk IDs used.")

# Modules
class CoT_Router(dspy.Module):
    def __init__(self):
        super().__init__()
        self.prog = dspy.ChainOfThought(Router)
    
    def forward(self, question):
        return self.prog(question=question)

class CoT_Planner(dspy.Module):
    def __init__(self):
        super().__init__()
        self.prog = dspy.ChainOfThought(Planner)
    
    def forward(self, question, retrieved_docs):
        return self.prog(question=question, retrieved_docs=retrieved_docs)

class CoT_SQL(dspy.Module):
    def __init__(self):
        super().__init__()
        self.prog = dspy.ChainOfThought(GenerateSQL)
    
    def forward(self, question, db_schema, plan=""):
        return self.prog(question=question, db_schema=db_schema, plan=plan)

class CoT_Synthesizer(dspy.Module):
    def __init__(self):
        super().__init__()
        self.prog = dspy.ChainOfThought(SynthesizeAnswer)
    
    def forward(self, question, sql_query, sql_result, retrieved_docs, format_hint):
        return self.prog(
            question=question,
            sql_query=sql_query,
            sql_result=sql_result,
            retrieved_docs=retrieved_docs,
            format_hint=format_hint
        )
