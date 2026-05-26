import os
import logging
import chromadb
from chromadb.utils import embedding_functions
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ================== CẤU HÌNH ==================
DATA_DIR = "data"
CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "scrum_kb"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
# =============================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_documents(data_dir: str):
    """Load all .txt and .pdf files from the data directory."""
    documents = []
    for filename in os.listdir(data_dir):
        file_path = os.path.join(data_dir, filename)
        try:
            if filename.endswith('.txt'):
                loader = TextLoader(file_path, encoding="utf-8")
            elif filename.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
            else:
                continue
            documents.extend(loader.load())
            logger.info(f"Loaded {filename}")
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
    return documents


def connect_chromadb(db_path: str, collection_name: str):
    """Connect to ChromaDB and return collection."""
    client = chromadb.PersistentClient(path=db_path)
    embed_fn = embedding_functions.OllamaEmbeddingFunction(
        model_name="nomic-embed-text"
    )
    # Test connectivity
    embed_fn(["test"])
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embed_fn
    )
    logger.info(f"Connected to ChromaDB collection '{collection_name}'")
    return collection


def process_documents(documents, chunk_size: int, chunk_overlap: int):
    """Chunk documents and prepare data for insertion."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    
    ids = []
    texts = []
    metadatas = []
    
    for idx, chunk in enumerate(chunks):
        chunk_id = f"chunk_{idx}"
        ids.append(chunk_id)
        texts.append(chunk.page_content)
        source = chunk.metadata.get("source", "unknown")
        metadatas.append({
            "source": os.path.basename(source),
            "chunk_index": idx
        })
    
    return ids, texts, metadatas


def insert_into_chromadb(collection, ids, texts, metadatas):
    """Insert chunks into ChromaDB."""
    if not ids:
        logger.warning("No data to insert")
        return False
    try:
        collection.add(ids=ids, documents=texts, metadatas=metadatas)
        logger.info(f"Successfully inserted {len(ids)} chunks into ChromaDB")
        return True
    except Exception as e:
        logger.error(f"Failed to insert: {e}")
        return False


def main():
    logger.info("Starting ingestion pipeline for real documents")
    try:
        # 1. Load all documents
        docs = load_documents(DATA_DIR)
        if not docs:
            raise ValueError(f"No .txt or .pdf documents found in '{DATA_DIR}'.")
        logger.info(f"Loaded {len(docs)} document page(s).")

        # 2. Connect to ChromaDB
        collection = connect_chromadb(CHROMA_DB_PATH, COLLECTION_NAME)

        # 3. Process documents (chunking)
        ids, docs_content, metas = process_documents(docs, CHUNK_SIZE, CHUNK_OVERLAP)
        logger.info(f"Created {len(ids)} chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")

        # 4. Insert into ChromaDB
        if insert_into_chromadb(collection, ids, docs_content, metas):
            final_count = collection.count()
            logger.info(f"Ingestion completed. Total chunks in DB: {final_count}")
            logger.info(f"Database location: {os.path.abspath(CHROMA_DB_PATH)}")
        else:
            logger.error("Ingestion failed")

    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")


if __name__ == "__main__":
    main()