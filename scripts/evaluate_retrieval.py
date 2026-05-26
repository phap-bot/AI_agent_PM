import json
import logging
from pathlib import Path
import chromadb

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "scrum_kb"


def get_relevant_chunks_with_metadata(query: str, k: int = 3):
    """Retrieve chunks kèm metadata từ ChromaDB."""
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_collection(COLLECTION_NAME)
    results = collection.query(query_texts=[query], n_results=k)
    
    chunks = []
    if results['documents'] and results['documents'][0]:
        for i in range(len(results['documents'][0])):
            chunks.append({
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i] if results['metadatas'] else {}
            })
    return chunks


def evaluate_retrieval(test_queries_path: str, k: int = 3):
    with open(test_queries_path, 'r', encoding='utf-8') as f:
        queries = json.load(f)
    
    hit_count = 0
    total_recall = 0.0
    details = []
    
    for item in queries:
        query = item['query']
        expected_sources = set(item['expected_sources'])
        
        retrieved = get_relevant_chunks_with_metadata(query, k=k)
        
        # Lấy source từ metadata của các chunk trả về
        found_sources = set()
        for chunk in retrieved:
            source = chunk['metadata'].get('source', '')
            # Chuẩn hóa tên source (bỏ .pdf, .txt)
            source_clean = source.replace('.pdf', '').replace('.txt', '')
            for exp in expected_sources:
                exp_clean = exp.replace('.pdf', '').replace('.txt', '')
                if exp_clean == source_clean or source_clean == exp_clean:
                    found_sources.add(exp)
                    break
        
        if found_sources:
            hit_count += 1
        
        recall = len(found_sources) / len(expected_sources) if expected_sources else 0
        total_recall += recall
        
        details.append({
            'query': query[:60],
            'expected': list(expected_sources),
            'found': list(found_sources),
            'recall': recall
        })
    
    hit_rate = hit_count / len(queries)
    recall_at_k = total_recall / len(queries)
    
    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    print(f"Total queries: {len(queries)}")
    print(f"k = {k}")
    print(f"\nHit Rate@{k}: {hit_rate:.2%} ({hit_count}/{len(queries)})")
    print(f"Recall@{k}: {recall_at_k:.2%}")
    
    print("\n" + "-" * 60)
    print("DETAILS BY QUERY")
    print("-" * 60)
    for d in details:
        status = "✓" if d['recall'] > 0 else "✗"
        print(f"{status} Query: {d['query']}...")
        print(f"   Expected: {d['expected']} | Found: {d['found']}")
    
    return hit_rate, recall_at_k


if __name__ == "__main__":
    test_file = Path(__file__).parent.parent / "data" / "test_queries.json"
    if not test_file.exists():
        print(f"Error: {test_file} not found.")
    else:
        evaluate_retrieval(str(test_file), k=3)