import chromadb
from chromadb.utils import embedding_functions

def main():
    print("=" * 50)
    print("KIỂM TRA OLLAMA EMBEDDING FUNCTION")
    print("=" * 50)

    embed_fn = embedding_functions.OllamaEmbeddingFunction(
        model_name="nomic-embed-text"
    )

    test_text = "Scrum is a framework for agile project management."
    print(f"Test với câu: \"{test_text}\"")

    try:
        embedding = embed_fn([test_text])
        vector = embedding[0]
        print("\nKết nối và tạo embedding thành công!")
        print(f"Chiều của vector: {len(vector)}")
        print(f"5 giá trị đầu tiên: {vector[:5]}")
    except Exception as e:
        print(f"\nLỗi kết nối hoặc tạo embedding: {e}")
        print("Hãy chắc chắn Ollama đang chạy và model 'nomic-embed-text' đã được pull.")

if __name__ == "__main__":
    main()