"""Debug why Q15 and Q17 miss in RAG evaluation."""
from __future__ import annotations
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, 'src')
from ai_scrum_master.retrieval.vector_store import search_context

queries = [
    ("Q15", "Write user story with acceptance criteria Given When Then"),
    ("Q17", "Split oversized requirement into multiple user stories across sprints"),
]

for qid, query in queries:
    print(f"\n=== {qid}: {query} ===")
    matches = search_context(query, n_results=5)
    for m in matches:
        source = m.get("metadata", {}).get("source", "?")
        # Normalize to filename
        source_name = source.replace("\\", "/").split("/")[-1]
        print(f"  score={m['score']:.3f}  {source_name}")
    if not matches:
        print("  [NO RESULTS]")
