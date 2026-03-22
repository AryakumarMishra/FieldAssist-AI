import shutil
import tempfile
import os
import uuid
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate

from .schema.chat_schema import ChatInput
from .schema.history_schema import ChatSessionCreate
from .core.retriever import retrieve_documents
from .core.get_llm import get_llm
from .core.database import create_session, get_all_sessions, add_message, get_session_messages

# loading environment variables
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(CURRENT_DIR, ".env")
load_dotenv(env_path, override=True)

# setting up the backend
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/chats")
async def create_new_chat(session_data: ChatSessionCreate):
    """Creates a fresh chat session and returns its ID"""
    session_id = create_session(title=session_data.title, category=session_data.category)
    return {"session_id": session_id}


@app.get("/chats")
async def fetch_all_chats():
    """Fetches all past chats to display in the sidebar"""
    return get_all_sessions()


@app.get("/chats/{session_id}/messages")
async def fetch_chat_messages(session_id: str):
    """Fetches full chat history sequence based on session id"""
    return get_session_messages(session_id)


@app.post("/chat")
async def chat_with_doc(request: ChatInput):
    """Chat with the document"""
    if request.session_id:
        add_message(request.session_id, "user", request.query)
        
    retriever = retrieve_documents(query=request.query, category=request.category)

    if not retriever:
        return {
            "message": "No documents found",
            "answer": "No documents found"
        }

    context = "\n\n".join(retriever)

    # prompt for the llm
    system_prompt = (
        "You are FieldAssist AI, a highly secure, offline-first AI assistant designed to provide accurate, privacy-preserving legal and procedural guidance.\n\n"
        "STRICT RULES:\n"
        "1. You must base your answers SOLELY on the provided context block below.\n"
        "2. Do NOT use outside knowledge, internet sources, or prior training data. Client privacy and data security are paramount.\n"
        "3. If the answer exists in the context, extract and summarize it concisely.\n"
        "4. If the context does not contain the answer, ONLY reply 'I cannot find the relevant information in the provided document. Please consult the official manual.'\n"
        "5. Every claim MUST be supported by the context.\n"
        "6. When quoting laws, sections, or military/medical procedures, be highly precise.\n\n"
        "Answer Guidelines:\n"
        "- Answer the question professionally and objectively.\n"
        "- Keep responses to 3-5 concise sentences unless detailed steps are required.\n"
        "- Focus on technical and legal specificity.\n\n"
        "Required Output Format:\n"
        "Answer: <concise, context-grounded answer>\n"
        "Supporting Context: <exact excerpts used>\n\n"
        "CONTEXT:\n"
        "{context}"
    )

    human_prompt = "{query}"

    chat_template = ChatPromptTemplate.from_messages([
        {"role": "system", "content": system_prompt},
        {"role": "human", "content": human_prompt}
    ])

    final_prompt = chat_template.format_messages(
        context=context,
        query=request.query
    )

    llm = get_llm()
    llm_response = llm.invoke(final_prompt)

    if request.session_id:
        add_message(request.session_id, "assistant", llm_response.content)

    return {
        "answer": llm_response.content,
        "source_documents": retriever
    }