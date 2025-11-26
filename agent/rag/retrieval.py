import os
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
import glob

class Retriever:
    def __init__(self, docs_dir: str):
        self.docs_dir = docs_dir
        self.chunks: List[Dict[str, Any]] = []
        self.bm25 = None
        self._load_documents()

    def _load_documents(self):
        """Loads and chunks documents from the docs directory."""
        file_paths = glob.glob(os.path.join(self.docs_dir, "*.md"))
        
        for file_path in file_paths:
            filename = os.path.basename(file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Simple chunking by sections (headers) or paragraphs
            # For this assignment, splitting by double newlines is a reasonable start
            # or splitting by headers if they exist.
            # Let's try to split by '## ' to capture sections, or fall back to paragraphs.
            
            # Simple chunking by paragraphs
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            
            for j, para in enumerate(paragraphs):
                chunk_id = f"{filename.replace('.md', '')}::chunk{j}"
                self.chunks.append({
                    "id": chunk_id,
                    "content": para,
                    "source": filename
                })

        # Initialize BM25
        tokenized_corpus = [chunk["content"].lower().split() for chunk in self.chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def retrieve(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Retrieves top-k chunks for a given query."""
        if not self.chunks:
            return []
            
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get top-k indices
        top_n = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        
        results = []
        for i in top_n:
            # Filter out very low scores if needed, but for now return top k
            results.append({
                **self.chunks[i],
                "score": float(scores[i])
            })
            
        return results
