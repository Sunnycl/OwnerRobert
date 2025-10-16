from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from dotenv import load_dotenv

from .db import Database

load_dotenv()

app = FastAPI(title="Voice Chatbot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static UI
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


class ChatRequest(BaseModel):
    message: str
    persona: str | None = None
    conversation_id: str | None = None
    enable_search: bool = False


class ChatResponse(BaseModel):
    conversation_id: str
    reply: str


db = Database()


@app.on_event("startup")
async def on_startup() -> None:
    await db.initialize()


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    # Lazy import to avoid circular dependency at import time
    from .services.llm import LLMService

    # Persist user message
    conversation_id = await db.ensure_conversation(req.conversation_id)
    await db.add_message(conversation_id, role="user", content=req.message)

    # Compose system prompt with persona
    persona = req.persona or os.getenv("PERSONA", "calm, helpful")
    system_prompt = os.getenv(
        "SYSTEM_PROMPT",
        "You are a helpful voice assistant. Be concise and friendly.",
    )
    system_prompt = f"{system_prompt}\nStyle: {persona}"

    # Optional: lightweight web search signal
    search_snippets: list[str] = []
    if req.enable_search:
        try:
            from .services.search import SearchService

            search = SearchService()
            search_snippets = await search.quick_snippets(req.message)
        except Exception:
            search_snippets = []

    context_block = "\n\n".join(search_snippets) if search_snippets else ""

    # Build history for grounding
    history = await db.get_recent_messages(conversation_id, limit=12)

    llm = LLMService()
    reply_text = await llm.generate_reply(
        system_prompt=system_prompt,
        history=history,
        user_message=req.message,
        context_snippets=context_block,
    )

    await db.add_message(conversation_id, role="assistant", content=reply_text)

    return ChatResponse(conversation_id=conversation_id, reply=reply_text)


@app.get("/api/history/search")
async def history_search(q: str, limit: int = 10):
    results = await db.search_messages(q, limit=limit)
    return {"results": results}
