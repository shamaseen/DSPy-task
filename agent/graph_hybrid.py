import os
import dspy
from typing import TypedDict, Annotated, List, Dict, Any, Union, Optional
from langgraph.graph import StateGraph, END
from agent.tools.sqlite_tool import SQLiteTool
from agent.rag.retrieval import Retriever
from agent.dspy_signatures import CoT_Router, CoT_SQL, CoT_Synthesizer, CoT_Planner

# Define State
class AgentState(TypedDict):
    question: str
    format_hint: str
    classification: str
    plan: str
    sql_query: Optional[str]
    sql_result: Optional[Dict[str, Any]]
    retrieved_docs: List[Dict[str, Any]]
    final_answer: Any
    explanation: str
    citations: List[str]
    confidence: float
    error: Optional[str]
    repair_count: int

# Initialize Tools and Modules
# Note: These should be initialized with proper paths in the main execution flow or passed in.
# For now, we'll assume they are available globally or we'll initialize them inside nodes if needed.
# Better to initialize them outside and pass them to the graph creation function.

class HybridAgent:
    def __init__(self, db_path: str, docs_dir: str):
        self.db_tool = SQLiteTool(db_path)
        self.retriever = Retriever(docs_dir)
        self.schema = self.db_tool.get_schema()
        
        # DSPy Modules
        self.router = CoT_Router()
        self.planner = CoT_Planner()
        
        # Load optimized SQL generator if available
        self.sql_gen = CoT_SQL()
        if os.path.exists("agent/optimized_sql_gen.json"):
            print("Loading optimized SQL generator...")
            self.sql_gen.load("agent/optimized_sql_gen.json")
            
        self.synthesizer = CoT_Synthesizer()
        
        # Build Graph
        self.app = self.build_graph()
    
    def build_graph(self):
        workflow = StateGraph(AgentState)
        
        workflow.add_node("router", self.route_question)
        workflow.add_node("retriever", self.retrieve_docs)
        workflow.add_node("planner", self.plan_execution)
        workflow.add_node("sql_generator", self.generate_sql)
        workflow.add_node("executor", self.execute_sql)
        workflow.add_node("synthesizer", self.synthesize_answer)
        workflow.add_node("repair", self.repair_action)
        
        workflow.set_entry_point("router")
        
        workflow.add_conditional_edges(
            "router",
            self.decide_route,
            {
                "rag": "retriever",
                "sql": "sql_generator",
                "hybrid": "retriever"
            }
        )
        
        # RAG flow: Retriever -> Planner -> Synthesizer (Planner helps extract constraints even for RAG)
        # SQL flow: SQL Generator -> Executor -> Synthesizer
        # Hybrid flow: Retriever -> Planner -> SQL Generator -> Executor -> Synthesizer
        
        workflow.add_conditional_edges(
            "retriever",
            lambda state: "planner",
            {"planner": "planner"}
        )
        
        workflow.add_conditional_edges(
            "planner",
            lambda state: "sql_generator" if state["classification"] in ["sql", "hybrid"] else "synthesizer",
            {
                "sql_generator": "sql_generator",
                "synthesizer": "synthesizer"
            }
        )
        
        workflow.add_edge("sql_generator", "executor")
        
        workflow.add_conditional_edges(
            "executor",
            self.check_execution,
            {
                "synthesizer": "synthesizer",
                "repair": "repair"
            }
        )
        
        workflow.add_conditional_edges(
            "repair",
            lambda state: "sql_generator" if state["repair_count"] <= 2 else "synthesizer",
            {
                "sql_generator": "sql_generator",
                "synthesizer": "synthesizer"
            }
        )
        
        workflow.add_edge("synthesizer", END)
        
        return workflow.compile()

    def route_question(self, state: AgentState):
        print(f"Routing question: {state['question']}")
        try:
            pred = self.router(question=state['question'])
            classification = pred.classification.lower() if hasattr(pred, 'classification') else "hybrid"
            if classification not in ["rag", "sql", "hybrid"]:
                classification = "hybrid"
            return {"classification": classification}
        except Exception as e:
            print(f"Router error: {e}, defaulting to hybrid")
            return {"classification": "hybrid"}

    def decide_route(self, state: AgentState):
        return state["classification"]

    def retrieve_docs(self, state: AgentState):
        print("Retrieving docs...")
        docs = self.retriever.retrieve(state["question"])
        return {"retrieved_docs": docs}

    def plan_execution(self, state: AgentState):
        print("Planning execution...")
        try:
            retrieved_docs = str(state.get("retrieved_docs", []))
            pred = self.planner(question=state["question"], retrieved_docs=retrieved_docs)
            plan = pred.plan if hasattr(pred, 'plan') else str(pred)
            return {"plan": plan}
        except Exception as e:
            print(f"Planner error: {e}, using basic plan")
            return {"plan": f"Answer the question: {state['question']}"}

    def generate_sql(self, state: AgentState):
        print("Generating SQL...")
        try:
            pred = self.sql_gen(
                question=state["question"], 
                db_schema=self.schema, 
                plan=state.get("plan", "")
            )
            sql_query = pred.sql_query if hasattr(pred, 'sql_query') else str(pred)
            return {"sql_query": sql_query}
        except Exception as e:
            print(f"SQL generation error: {e}")
            # Fallback: set error to trigger repair or skip SQL
            return {"sql_query": None, "error": f"SQL generation failed: {str(e)}"}

    def execute_sql(self, state: AgentState):
        print(f"Executing SQL: {state['sql_query']}")
        result = self.db_tool.execute_query(state["sql_query"])
        error = result.get("error")
        return {"sql_result": result, "error": error}

    def check_execution(self, state: AgentState):
        if state.get("error"):
            print(f"Execution Error: {state['error']}")
            return "repair"
        return "synthesizer"

    def repair_action(self, state: AgentState):
        print(f"Repairing... Attempt {state['repair_count'] + 1}")
        # In a real repair, we would feed the error back to the SQL generator.
        # For this implementation, we increment the counter.
        # Ideally, we should update the plan or provide feedback to the generator in the next step.
        # We can append the error to the question or plan to inform the next generation.
        
        new_plan = state.get("plan", "") + f"\nPrevious SQL failed with error: {state['error']}. Fix the SQL."
        
        return {
            "repair_count": state["repair_count"] + 1,
            "plan": new_plan,
            "error": None # Clear error for next attempt
        }

    def synthesize_answer(self, state: AgentState):
        print("Synthesizing answer...")
        
        sql_query = state.get("sql_query", "")
        sql_result = str(state.get("sql_result", ""))
        retrieved_docs = str(state.get("retrieved_docs", []))
        
        try:
            pred = self.synthesizer(
                question=state["question"],
                sql_query=sql_query,
                sql_result=sql_result,
                retrieved_docs=retrieved_docs,
                format_hint=state["format_hint"]
            )
            
            final_answer = pred.final_answer if hasattr(pred, 'final_answer') else None
            explanation = pred.explanation if hasattr(pred, 'explanation') else "Generated answer"
            citations = pred.citations if hasattr(pred, 'citations') else []
        except Exception as e:
            print(f"Synthesizer error: {e}, using fallback")
            # Fallback: try to extract answer from SQL result
            final_answer = "Error generating answer"
            explanation = f"Synthesis failed: {str(e)}"
            citations = []
            
            if sql_result and "rows" in sql_result:
                try:
                    result_dict = eval(sql_result)
                    if result_dict.get("rows"):
                        final_answer = result_dict["rows"][0][0] if result_dict["rows"][0] else None
                except:
                    pass
        
        # Basic type conversion
        try:
            if state["format_hint"] == "int":
                final_answer = int(float(str(final_answer).strip()))
            elif state["format_hint"] == "float":
                final_answer = float(str(final_answer).strip())
        except:
            pass 
            
        if isinstance(citations, str):
            citations = [c.strip() for c in citations.split(',')]
            
        # Calculate Confidence
        confidence = 1.0
        if state.get("repair_count", 0) > 0:
            confidence -= (0.2 * state["repair_count"])
        
        if not citations:
            confidence -= 0.2
            
        if confidence < 0:
            confidence = 0.0
            
        return {
            "final_answer": final_answer,
            "explanation": explanation,
            "citations": citations,
            "confidence": round(confidence, 2)
        }
    
    def invoke(self, state):
        return self.app.invoke(state)
