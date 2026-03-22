from unstructured.partition.auto import partition

def load_document(file_path: str):
    """Load the documents or audio and return the elements"""
    elements = partition(filename=file_path)
    return elements