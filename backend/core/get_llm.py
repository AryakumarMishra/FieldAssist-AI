from langchain_ollama import ChatOllama


def get_llm():
    """Get the LLM model"""
    return ChatOllama(model="mistral")