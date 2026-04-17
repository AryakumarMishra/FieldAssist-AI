import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# lock down the absolute path to a specific folder next to this file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# this will save the DB inside main_app/backend/core/chroma_langchain_db
DB_DIR = os.path.join(CURRENT_DIR, "chroma_langchain_db")

# globally initialize the embedding model
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


def contextualize_query(query: str, history: list[dict]) -> str:
    """
    If the query is a follow-up (short, no legal keywords), prepend
    the last assistant turn's topic so the vector search stays on track.
    """
    if not history:
        return query

    # Only contextualize if query looks like a follow-up (short sentence, no section numbers, no legal nouns)
    is_followup = len(query.split()) < 12 and not any(
        kw in query.lower() for kw in ["section", "bns", "ipc", "offence", "robbery", "theft", "murder"]
    )
    if not is_followup:
        return query

    # Grab the last user message that was substantive
    last_user_msg = ""
    for msg in reversed(history):
        if msg["role"] == "user" and len(msg["content"].split()) > 8:
            last_user_msg = msg["content"]
            break

    if last_user_msg:
        return f"{last_user_msg} — {query}"
    return query


def get_vector_store(category: str):
    """Retrieves or creates a specific collection for the given category in ChromaDB"""
    return Chroma(
        collection_name=category,
        persist_directory=DB_DIR,
        embedding_function=embeddings,
        collection_metadata={"hnsw:space": "cosine"}
    )



def retrieve_documents(query: str, category: str, score_threshold: float = 0.35):
    """
    Retrieves documents from ChromaDB with a relevance score filter.
    Cosine similarity: 1.0 = identical, 0.0 = unrelated.
    Chunks scoring below threshold are discarded.
    """
    vector_store = get_vector_store(category)

    results_with_scores = vector_store.similarity_search_with_relevance_scores(
        query=query,
        k=6,
    )

    filtered = [
        doc.page_content
        for doc, score in results_with_scores
        if score >= score_threshold
    ]

    # Fallback: if filtering was too aggressive, return top 3 anyway
    if not filtered:
        filtered = [doc.page_content for doc, _ in results_with_scores[:3]]

    return filtered