import chromadb
from chromadb.utils import embedding_functions

def check_chromadb():
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection("scrum_kb")
    count = collection.count()
    print(f"ChromaDB collection 'scrum_kb' has {count} chunks")
    if count > 0:
        sample = collection.get(limit=1)
        print(f"Sample content: {sample['documents'][0][:100]}...")
    return count

def check_embedding():
    embed_fn = embedding_functions.OllamaEmbeddingFunction(model_name="nomic-embed-text")
    vector = embed_fn(["Hello world"])
    print(f"Embedding dimension: {len(vector[0])}")
    return True

if __name__ == "__main__":
    print("=== Checking ChromaDB ===")
    check_chromadb()
    print("\n=== Checking Ollama Embedding ===")
    check_embedding()
    print("\n[SUCCESS] System ready for next tasks.")