import os

from .core.loader import load_document
from .core.chunker import chunk_document
from .core.langchain_doc import create_langchain_document
from .core.embed import add_to_vector_store


# Absolute path to the current directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Data directory is one level up
DATA_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "data")


def ingest_document(file_path: str, category: str):
    """Ingest the documents and store in the respective category collection"""

    try:
        # ingestion pipeline
        elements = load_document(file_path)
        chunks = chunk_document(elements)
        langchain_documents = create_langchain_document(chunks)
        add_to_vector_store(langchain_documents, category=category)

        return {
            "message": "Document loaded successfully",
            "total_chunks": len(langchain_documents)
        }
    
    except Exception as e:
        print(f"Error loading document: {e}")


def ingest_all():
    """Iterates through all subdirectories in the data folder and ingests PDFs into their respective collections."""
    print(f"Looking for data in: {DATA_DIR}")
    if not os.path.exists(DATA_DIR):
        print("Data directory not found.")
        return

    # iterate through subdirectories in data/
    for category in os.listdir(DATA_DIR):
        category_path = os.path.join(DATA_DIR, category)
        
        # Only process directories
        if os.path.isdir(category_path):
            print(f"\n--- Processing category: {category} ---")
            for filename in os.listdir(category_path):
                if filename.endswith(".pdf"):
                    file_path = os.path.join(category_path, filename)
                    print(f"Ingesting {filename} into {category} collection...")
                    try:
                        result = ingest_document(file_path=file_path, category=category)
                        print(f"Result: {result}")
                    except Exception as e:
                        print(f"Failed to ingest {filename}: {e}")


if __name__ == "__main__":
    ingest_all()