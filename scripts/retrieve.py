# scripts/retrieve.py
import os
import chromadb
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Đường dẫn và tên collection, bạn có thể để cứng hoặc import từ config.py
CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "scrum_kb"

def get_relevant_context(query: str, k: int = 3) -> list:
    """
    Truy xuất k đoạn văn bản (chunks) liên quan nhất từ ChromaDB cho một câu hỏi.

    Args:
        query: Câu hỏi bằng tiếng Anh.
        k: Số lượng chunks muốn lấy về.

    Returns:
        Danh sách các chuỗi văn bản (content của chunks). Trả về list rỗng nếu có lỗi.
    """
    try:
        # Kết nối đến ChromaDB
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        collection = client.get_collection(COLLECTION_NAME)

        # Thực hiện truy vấn vector
        results = collection.query(
            query_texts=[query],
            n_results=k
        )

        # Trích xuất danh sách các document (chunks)
        # results['documents'] là một list of lists, ví dụ [['chunk1', 'chunk2']]
        retrieved_chunks = results['documents'][0] if results['documents'] else []
        logger.info(f"Query: '{query[:50]}...' -> Retrieved {len(retrieved_chunks)} chunks.")
        return retrieved_chunks

    except Exception as e:
        logger.error(f"Lỗi truy xuất cho query '{query}': {e}")
        return []


# --- Phần để test thử function ---
if __name__ == "__main__":
    test_query = "What is a User Story?"
    print(f"Testing retrieval for query: '{test_query}'")
    relevant_chunks = get_relevant_context(test_query, k=3)
    
    if relevant_chunks:
        print(f"\nFound {len(relevant_chunks)} relevant chunks:")
        for i, chunk in enumerate(relevant_chunks):
            print(f"\n--- Chunk {i+1} ---")
            print(f"{chunk[:300]}...")  # In 300 ký tự đầu của mỗi chunk
    else:
        print("No chunks retrieved.")