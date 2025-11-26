import click
import json
import os
import dspy
from agent.graph_hybrid import HybridAgent

import logging

# Setup logging
logging.basicConfig(
    filename='agent_trace.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@click.command()
@click.option('--batch', required=True, help='Path to input JSONL file')
@click.option('--out', required=True, help='Path to output JSONL file')
def main(batch, out):
    logging.info(f"Starting agent run with batch={batch}, out={out}")
    
    # Setup DSPy LM
    # Assuming Ollama is running
    try:
        lm = dspy.LM(model='ollama/phi3.5:3.8b-mini-instruct-q4_K_M', api_base='http://localhost:11434', max_tokens=1000)
    except Exception as e:
        logging.error(f"Failed to initialize DSPy LM: {e}")
        raise e
        
    dspy.settings.configure(lm=lm)
    
    # Initialize Agent
    agent = HybridAgent(
        db_path="data/northwind.sqlite",
        docs_dir="docs"
    )
    app = agent.build_graph()
    
    results = []
    
    with open(batch, 'r') as f:
        for line in f:
            item = json.loads(line)
            print(f"Processing: {item['id']}")
            
            initial_state = {
                "question": item["question"],
                "format_hint": item["format_hint"],
                "classification": "",
                "sql_query": None,
                "sql_result": None,
                "retrieved_docs": [],
                "final_answer": None,
                "explanation": "",
                "citations": [],
                "error": None,
                "repair_count": 0
            }
            
            final_state = app.invoke(initial_state)
            
            logging.info(f"Processed {item['id']}. Final Answer: {final_state['final_answer']}")
            if final_state.get('error'):
                logging.error(f"Error in {item['id']}: {final_state['error']}")
            
            output = {
                "id": item["id"],
                "final_answer": final_state["final_answer"],
                "sql": final_state["sql_query"] if final_state["sql_query"] else "",
                "confidence": final_state.get("confidence", 0.0),
                "explanation": final_state["explanation"],
                "citations": final_state["citations"]
            }
            results.append(output)
            
    # Write results
    with open(out, 'w') as f:
        for res in results:
            f.write(json.dumps(res) + "\n")
            
    print(f"Done. Results written to {out}")

if __name__ == '__main__':
    main()
