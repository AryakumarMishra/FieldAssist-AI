import shutil
import tempfile
import os
import uuid
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate

from .schema.chat_schema import ChatInput
from .schema.history_schema import ChatSessionCreate
from .core.retriever import retrieve_documents, contextualize_query
from .core.get_llm import get_llm
from .core.database import create_session, get_all_sessions, add_message, get_session_messages, delete_session

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


@app.delete("/chats/{session_id}")
async def remove_chat(session_id: str):
    """Deletes a chat session and all its messages natively"""
    delete_session(session_id)
    return {"status": "success", "session_id": session_id}


@app.post("/chat")
async def chat_with_doc(request: ChatInput):
    """Chat with the document (Streams Response)"""

    history = get_session_messages(request.session_id) if request.session_id else []

    if request.session_id:
        add_message(request.session_id, "user", request.query)

    retrieval_query = contextualize_query(request.query, history)
    retriever = retrieve_documents(query=retrieval_query, category=request.category)

    if not retriever:
        async def mock_stream():
            msg = "I cannot find the relevant information in the provided document. Please consult the official manual."
            yield msg
            if request.session_id:
                add_message(request.session_id, "assistant", msg)
        return StreamingResponse(mock_stream(), media_type="text/plain")

    context = "\n\n".join(retriever)


    history_text = ""
    if history:
        recent = history[-6:]  # last 3 turns (user + assistant pairs)
        history_text = "\n".join(
            f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
            for m in recent
        )


    system_prompt = (
        "You are FieldAssist AI, a highly secure, offline-first AI assistant that provides accurate, "
        "privacy-preserving legal and procedural guidance based strictly on the Bharatiya Nyaya Sanhita (BNS) 2023 "
        "and other official documents.\n\n"

        "STRICT RULES:\n"
        "1. Base your answers SOLELY on the CONTEXT block provided below.\n"
        "2. Do NOT use outside knowledge, internet sources, or prior training data.\n"
        "3. If the answer is in the context, extract and summarize it clearly and concisely.\n"
        "4. If the context does not contain a sufficient answer, reply ONLY: "
        "'I cannot find the relevant information in the provided document. Please consult the official manual.'\n"
        "5. Every legal claim MUST cite the specific BNS section number from the context.\n"
        "6. When the user asks a follow-up question (e.g., 'what should I do next?'), "
        "use the CONVERSATION HISTORY to understand what situation they are referring to, "
        "then answer in that context using the retrieved documents.\n\n"

        "ANSWER GUIDELINES:\n"
        "- Be practical and direct. If the user is describing a situation they experienced, "
        "explain what offence occurred, which section applies, and what their immediate options are.\n"
        "- Do not just recite raw legal text. Interpret it for the user's situation.\n"
        "- Keep responses to 4-6 sentences unless detailed steps are required.\n"
        "- For victim scenarios: mention (1) the applicable offence & section, "
        "(2) the practical step (e.g., file FIR at nearest police station), "
        "(3) cognizability and bailability if available in context.\n\n"

        "OUTPUT FORMAT:\n"
        "Answer: <clear, practical, context-grounded answer with section references>\n"
        "Supporting Context: <brief exact excerpt(s) from context that support the answer>\n\n"

        "CONVERSATION HISTORY (for follow-up context only — do not answer from this):\n"
        "{history}\n\n"

        "CONTEXT (answer ONLY from this):\n"
        "{context}"
    )

    human_prompt = "User's current question: {query}"


    chat_template = ChatPromptTemplate.from_messages([
        {"role": "system", "content": system_prompt},
        {"role": "human", "content": human_prompt}
    ])

    final_prompt = chat_template.format_messages(
        context=context,
        history=history_text if history_text else "No prior conversation.",
        query=request.query
    )

    llm = get_llm()

    async def generate_response():
        full_response = ""
        for chunk in llm.stream(final_prompt):
            content = chunk.content
            full_response += content
            yield content

        yield "\n__SOURCES_JSON__" + json.dumps(retriever) + "__END_SOURCES__"

        if request.session_id:
            add_message(request.session_id, "assistant", full_response)

    return StreamingResponse(generate_response(), media_type="text/plain")