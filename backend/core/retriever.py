import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# lock down the absolute path to a specific folder next to this file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# this will save the DB inside main_app/backend/core/chroma_langchain_db
DB_DIR = os.path.join(CURRENT_DIR, "chroma_langchain_db")

# globally initialize the embedding model
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def get_vector_store(category: str):
    """Retrieves or creates a specific collection for the given category in ChromaDB"""
    return Chroma(
        collection_name=category,
        persist_directory=DB_DIR,
        embedding_function=embeddings,
        collection_metadata={"hnsw:space": "cosine"}
    )

def retrieve_documents(query: str, category: str):
    """Retrieves the documents from the vector store associated with the category"""
    vector_store = get_vector_store(category)
    results = vector_store.similarity_search(
        query=query,
        k=5,
    )
    return [doc.page_content for doc in results]