import os
import logging
import chromadb
from chromadb.utils import embedding_functions
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ================== CONFIGURATION ==================
DATA_DIR = "data"
CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "scrum_kb"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
# ===================================================

def get_text_files(data_dir: str) -> list:
    """Return list of .txt files in the given directory."""
    if not os.path.isdir(data_dir):
        raise FileNotFoundError(f"Directory '{data_dir}' does not exist.")
    
    files = [f for f in os.listdir(data_dir) if f.endswith('.txt')]
    if not files:
        raise ValueError(f"No .txt files found in '{data_dir}'.")
    
    return files

def connect_chromadb(path: str, collection_name: str):
    """Connect to ChromaDB and return the collection."""
    try:
        client = chromadb.PersistentClient(path=path)
        embedding_fn = embedding_functions.OllamaEmbeddingFunction(
            model_name="nomic-embed-text"
        )
        # Verify Ollama connectivity with a dummy call
        embedding_fn(["test"])
        
        collection = client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_fn
        )
        logger.info(f"Connected to ChromaDB collection '{collection_name}'")
        return collection
    except Exception as e:
        logger.error(f"Failed to connect to Ollama or ChromaDB: {e}")
        raise

def process_documents(file_paths: list, chunk_size: int, chunk_overlap: int):
    """Load, chunk documents and prepare data for insertion."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )
    
    all_ids = []
    all_documents = []
    all_metadatas = []
    
    for file_path in file_paths:
        try:
            loader = TextLoader(file_path, encoding="utf-8")
            documents = loader.load()
            chunks = text_splitter.split_documents(documents)
            base_name = os.path.basename(file_path).replace('.txt', '')
            
            for idx, chunk in enumerate(chunks):
                chunk_id = f"{base_name}_{idx}"
                all_ids.append(chunk_id)
                all_documents.append(chunk.page_content)
                all_metadatas.append({
                    "source": os.path.basename(file_path),
                    "chunk_index": idx
                })
            logger.info(f"Processed {file_path} -> {len(chunks)} chunks")
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            continue
    
    return all_ids, all_documents, all_metadatas

def insert_into_chromadb(collection, ids, documents, metadatas):
    """Insert chunks into ChromaDB."""
    if not ids:
        logger.warning("No data to insert")
        return False
    
    try:
        collection.add(ids=ids, documents=documents, metadatas=metadatas)
        logger.info(f"Successfully inserted {len(ids)} chunks into ChromaDB")
        return True
    except Exception as e:
        logger.error(f"Failed to insert into ChromaDB: {e}")
        return False

def main():
    logger.info("Starting ingestion pipeline")
    
    try:
        # 1. Get .txt files
        txt_files = get_text_files(DATA_DIR)
        logger.info(f"Found {len(txt_files)} file(s): {', '.join(txt_files)}")
        
        # 2. Connect to ChromaDB
        collection = connect_chromadb(CHROMA_DB_PATH, COLLECTION_NAME)
        
        # 3. Prepare full paths
        file_paths = [os.path.join(DATA_DIR, f) for f in txt_files]
        
        # 4. Process documents
        ids, docs, metas = process_documents(file_paths, CHUNK_SIZE, CHUNK_OVERLAP)
        
        # 5. Insert into ChromaDB
        if insert_into_chromadb(collection, ids, docs, metas):
            final_count = collection.count()
            logger.info(f"Ingestion completed. Total chunks in DB: {final_count}")
            logger.info(f"Database location: {os.path.abspath(CHROMA_DB_PATH)}")
        else:
            logger.error("Ingestion failed")
            
    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")

if __name__ == "__main__":
    main()