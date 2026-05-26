# scripts/inspect_chromadb.py
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("scrum_kb")

# Lấy 5 chunks mẫu
sample = collection.get(limit=5)
for i in range(len(sample['ids'])):
    print(f"ID: {sample['ids'][i]}")
    print(f"Metadata: {sample['metadatas'][i]}")
    print(f"Content preview: {sample['documents'][i][:100]}...")
    print("-" * 50)