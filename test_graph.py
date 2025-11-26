import unittest
from agent.graph_hybrid import HybridAgent

class TestHybridAgent(unittest.TestCase):
    def test_graph_structure(self):
        # Initialize with dummy paths (files don't need to exist for graph build, 
        # but tools init might check. Let's assume they exist or mock them if needed.
        # Since we created empty files in setup, this should be fine.)
        agent = HybridAgent("data/northwind.sqlite", "docs")
        
        # Check nodes
        nodes = agent.app.nodes
        self.assertIn("router", nodes)
        self.assertIn("retriever", nodes)
        self.assertIn("planner", nodes)
        self.assertIn("sql_generator", nodes)
        self.assertIn("executor", nodes)
        self.assertIn("synthesizer", nodes)
        self.assertIn("repair", nodes)
        
        print("Graph structure verified.")

if __name__ == '__main__':
    unittest.main()
