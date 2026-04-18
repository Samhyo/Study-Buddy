import json
import os
import time
import re
from collections import defaultdict
from typing import List

import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
# VISSIIN TURHA ??
#from requests import request

load_dotenv()


# ─── Setup ─────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not set")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

app = FastAPI(title="LLM Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Rate limiting ─────────────────────────────────────────────
RATE_LIMIT_REQUESTS = 20
RATE_LIMIT_WINDOW = 60

request_timestamps: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(session_id: str) -> bool:
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    request_timestamps[session_id] = [
        t for t in request_timestamps[session_id] if t > window_start
    ]
    if len(request_timestamps[session_id]) >= RATE_LIMIT_REQUESTS:
        return False
    request_timestamps[session_id].append(now)
    return True

def normalize_history(history: list[dict]) -> list[dict]:
    role_map = {
        "user": "USER",
        "assistant": "MODEL",
        "system": "SYSTEM",
    }

    normalized = []
    for item in history:
        if "parts" in item:
            normalized.append(item)
        elif "role" in item and "content" in item:
            role = item["role"].lower()
            if role not in role_map:
                raise HTTPException(status_code=400, detail=f"Unsupported role: {item['role']}")
            normalized.append({"role": role_map[role], "parts": [item["content"]]})
        else:
            raise HTTPException(status_code=400, detail="Invalid history item format")
    return normalized

# ─── Cost estimation ───────────────────────────────────────────
INPUT_COST_PER_M = 0.10
OUTPUT_COST_PER_M = 0.40


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens / 1_000_000) * INPUT_COST_PER_M + \
           (output_tokens / 1_000_000) * OUTPUT_COST_PER_M


# ─── Study Buddy state (materiaalit + quiz tila) ───────────────
session_material_chunks: dict[str, List[str]] = {}
session_last_question: dict[str, str] = {}


# ─── Study engine (chunking + context + promptit) ──────────────
def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100):
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + chunk_size])
        start += chunk_size - overlap
    return chunks


def get_relevant_chunks(chunks, query, top_k=3):
    scores = []
    query_words = set(re.findall(r"\w+", query.lower()))

    for chunk in chunks:
        chunk_words = set(re.findall(r"\w+", chunk.lower()))
        score = len(query_words & chunk_words)
        scores.append((score, chunk))

    scores.sort(key=lambda x: x[0], reverse=True)
    return [c for s, c in scores[:top_k] if s > 0]


def build_context(chunks, query):
    relevant = get_relevant_chunks(chunks, query)
    return "\n\n---\n\n".join(relevant) if relevant else ""


def build_explain_prompt(context):
    return f"""
You are a study buddy.
Explain clearly using the material below.
Material:
{context}
"""


def build_quiz_prompt(context):
    return f"""
You are a study buddy.
Ask ONE question based on the material.
Do not explain yet.
Material:
{context}
"""


def build_evaluation_prompt(context, question, answer):
    return f"""
You are a study assistant.

Question:
{question}

User answer:
{answer}

Material:
{context}

Evaluate the answer (correct / partial / incorrect) and ask a new question.
"""


# ─── Request model ─────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    session_id: str = "default"
    mode: str = "explain"

def convert_history(history: list[dict]):
    converted = []

    for msg in history:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if role not in ["user", "assistant"]:
            role = "user"

        converted.append({
            "role": role,
            "parts": [content]
        })

    return converted

def build_contents(request: ChatRequest):
    if request.mode == "quiz":
        system_prompt = (
            "You are Study Buddy in quiz mode. "
            "Do not immediately give the full answer. "
            "Ask the student guiding questions, one small step at a time."
        )
    else:
        system_prompt = (
            "You are Study Buddy in explain mode. "
            "Explain clearly, simply, and in a student-friendly way."
        )

    converted_history = convert_history(request.history)

    contents = [
        {"role": "user", "parts": [system_prompt]}
    ] + converted_history + [
        {"role": "user", "parts": [request.message]}
    ]

    return contents

# ─── Health check ──────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}


# ─── Upload (materiaalin syöttö AI:lle) ────────────────────────
@app.post("/upload")
async def upload(file: UploadFile = File(...), session_id: str = "default"):
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")

    chunks = chunk_text(text)
    session_material_chunks[session_id] = chunks

    return {"status": "uploaded", "chunks": len(chunks)}


# ─── Chat (non-stream) ─────────────────────────────────────────
@app.post("/chat")
async def chat(request: ChatRequest):
    if not check_rate_limit(request.session_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")

    chunks = session_material_chunks.get(request.session_id, [])
    context = build_context(chunks, request.message)

    if request.mode == "quiz":
        last_q = session_last_question.get(request.session_id)
        if last_q:
            system_prompt = build_evaluation_prompt(context, last_q, request.message)
            session_last_question[request.session_id] = None
        else:
            system_prompt = build_quiz_prompt(context)
    else:
        system_prompt = build_explain_prompt(context)

    contents = (
        [{"role": "user", "parts": [system_prompt]}]
        + [{"role": m["role"], "parts": [m["content"]]} for m in request.history]
        + [{"role": "user", "parts": [request.message]}]
    )

    response = model.generate_content(contents)
    usage = response.usage_metadata

    if request.mode == "quiz":
        session_last_question[request.session_id] = response.text

    return {
        "response": response.text,
        "usage": {
            "input_tokens": usage.prompt_token_count,
            "output_tokens": usage.candidates_token_count,
            "estimated_cost_usd": estimate_cost(
                usage.prompt_token_count,
                usage.candidates_token_count,
            ),
        },
    }


# ─── Chat (streaming SSE) ──────────────────────────────────────
@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    if not check_rate_limit(request.session_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")

    def generate():
        chunks = session_material_chunks.get(request.session_id, [])
        context = build_context(chunks, request.message)

        if request.mode == "quiz":
            last_q = session_last_question.get(request.session_id)
            if last_q:
                system_prompt = build_evaluation_prompt(context, last_q, request.message)
                session_last_question[request.session_id] = None
            else:
                system_prompt = build_quiz_prompt(context)
        else:
            system_prompt = build_explain_prompt(context)

        contents = (
            [{"role": "user", "parts": [system_prompt]}]
            + [{"role": m["role"], "parts": [m["content"]]} for m in request.history]
            + [{"role": "user", "parts": [request.message]}]
        )

        response = model.generate_content(contents, stream=True)

        full_text = ""

        for chunk in response:
            if chunk.text:
                full_text += chunk.text
                yield f"data: {json.dumps({'type': 'text', 'content': chunk.text})}\n\n"

        if request.mode == "quiz":
            session_last_question[request.session_id] = full_text

        usage = response.usage_metadata

        yield f"data: {json.dumps({'type': 'done', 'usage': {'input_tokens': usage.prompt_token_count, 'output_tokens': usage.candidates_token_count}})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )