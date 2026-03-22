from unstructured.chunking.title import chunk_by_title


def chunk_document(elements):
    """Chunk the elements using chunk_by_title"""
    chunks = chunk_by_title(
        elements=elements,
        max_characters=1000,
        new_after_n_chars=800,
        combine_text_under_n_chars=200
    ) 
    return chunks