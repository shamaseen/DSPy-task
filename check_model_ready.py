#!/usr/bin/env python3
import time
import subprocess
import sys

def check_model_available():
    """Check if the phi3.5 model is available in Ollama"""
    try:
        result = subprocess.run(
            ["ollama", "list"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        return "phi3.5:3.8b-mini-instruct-q4_K_M" in result.stdout
    except Exception as e:
        print(f"Error checking model: {e}")
        return False

def test_model():
    """Test if the model can generate a response"""
    try:
        result = subprocess.run(
            ["ollama", "run", "phi3.5:3.8b-mini-instruct-q4_K_M", "Say 'hello'"],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error testing model: {e}")
        return False

if __name__ == "__main__":
    print("Checking if Ollama model is ready...")
    
    # Wait for model to be available
    max_wait = 300  # 5 minutes
    waited = 0
    
    while waited < max_wait:
        if check_model_available():
            print("✓ Model is available!")
            
            print("\nTesting model response...")
            if test_model():
                print("✓ Model is working!")
                print("\n" + "="*50)
                print("Ready to run the agent!")
                print("="*50)
                print("\nRun:")
                print("  python run_agent_hybrid.py --batch sample_questions_hybrid_eval.jsonl --out outputs_hybrid.jsonl")
                sys.exit(0)
            else:
                print("✗ Model test failed")
                sys.exit(1)
        
        print(f"Waiting for model... ({waited}s/{max_wait}s)")
        time.sleep(10)
        waited += 10
    
    print("✗ Timeout waiting for model")
    sys.exit(1)
