import os
import chromadb

# ================== CẤU HÌNH ==================
CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "scrum_kb"
# =============================================

def main():
    print("=" * 50)
    print("KIỂM TRA DỮ LIỆU TRONG ChromaDB")
    print("=" * 50)

    if not os.path.exists(CHROMA_DB_PATH):
        print(f"Lỗi: Không tìm thấy thư mục ChromaDB tại '{CHROMA_DB_PATH}'.")
        print("Hãy chắc chắn bạn đã chạy 'scripts/ingest.py' thành công.")
        return

    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception as e:
        print(f"Lỗi: Không thể lấy collection '{COLLECTION_NAME}'. Chi tiết: {e}")
        return

    count = collection.count()
    print(f"Tên Collection: {collection.name}")
    print(f"Số lượng chunks: {count}")

    if count > 0:
        sample = collection.get(limit=1)
        print("\n--- Mẫu chunk đầu tiên ---")
        print(f"ID: {sample['ids'][0]}")
        print(f"Metadata: {sample['metadatas'][0]}")
        print(f"Nội dung: {sample['documents'][0][:150]}...")
    else:
        print("Collection trống.")

if __name__ == "__main__":
    main()