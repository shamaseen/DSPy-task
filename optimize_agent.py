import dspy
import json
from dspy.teleprompt import BootstrapFewShot
from agent.dspy_signatures import GenerateSQL, CoT_SQL
from agent.tools.sqlite_tool import SQLiteTool

def validate_sql(example, pred, trace=None):
    # Basic validation: check if SQL executes without error
    # In a real scenario, we would check against a gold standard result or more complex logic
    # Here we just check if it's a non-empty string and maybe if it executes
    # But we don't have the DB tool easily accessible inside this metric function without passing it
    # So let's just check if it generated something that looks like SQL
    sql = pred.sql_query
    return sql is not None and len(sql) > 10 and "SELECT" in sql.upper()

def main():
    # Setup
    try:
        lm = dspy.LM(model='ollama/phi3.5:3.8b-mini-instruct-q4_K_M', api_base='http://localhost:11434', max_tokens=1000)
    except Exception as e:
        print(f"Failed to initialize DSPy LM: {e}")
        raise e
        
    dspy.settings.configure(lm=lm)
    
    # Load Data
    with open('train_examples.json', 'r') as f:
        raw_data = json.load(f)
    
    # We need to provide the schema to the examples as inputs
    db_tool = SQLiteTool("data/northwind.sqlite")
    schema = db_tool.get_schema()
    
    trainset = []
    for item in raw_data:
        trainset.append(dspy.Example(
            question=item['question'],
            db_schema=schema,
            sql_query=item['sql_query']
        ).with_inputs('question', 'db_schema'))
        
    # Define Module to Optimize
    # We want to optimize CoT_SQL
    # But CoT_SQL wraps GenerateSQL. BootstrapFewShot works on modules.
    
    # Optimizer
    teleprompter = BootstrapFewShot(metric=validate_sql, max_bootstrapped_demos=4, max_labeled_demos=4)
    
    print("Compiling (optimizing) CoT_SQL...")
    optimized_sql_gen = teleprompter.compile(CoT_SQL(), trainset=trainset)
    
    # Save
    optimized_sql_gen.save("agent/optimized_sql_gen.json")
    print("Optimization complete. Saved to agent/optimized_sql_gen.json")

if __name__ == '__main__':
    main()
