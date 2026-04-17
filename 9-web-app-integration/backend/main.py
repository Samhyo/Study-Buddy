"""
Day 9 Demo: LLM Web App with Streaming
FastAPI backend that proxies requests to Gemini API with SSE streaming.

Key concepts:
- Why a backend? API key security, rate limiting, prompt management
- StreamingResponse + SSE format for real-time token delivery
- Per-session rate limiting (simple in-memory implementation)
- Token counting and cost estimation
"""

import json
import os
import time
from collections import defaultdict

import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

load_dotenv()

# ─── Setup ────────────────────────────────────────────────────────────────────

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not set")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemma4-31b-it")

app = FastAPI(title="LLM Chat API")

# Allow requests from the React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Rate limiting (in-memory, per session) ────────────────────────────────────
# In production: use Redis + sliding window per authenticated user

RATE_LIMIT_REQUESTS = 20   # max requests per window
RATE_LIMIT_WINDOW = 60     # seconds

request_timestamps: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(session_id: str) -> bool:
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    # Drop timestamps outside the window
    request_timestamps[session_id] = [
        t for t in request_timestamps[session_id] if t > window_start
    ]
    if len(request_timestamps[session_id]) >= RATE_LIMIT_REQUESTS:
        return False
    request_timestamps[session_id].append(now)
    return True


# ─── Cost estimation ──────────────────────────────────────────────────────────
# Gemini 2.5 Flash Lite pricing (as of 2025, per million tokens)
INPUT_COST_PER_M = 0.10
OUTPUT_COST_PER_M = 0.40


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens / 1_000_000) * INPUT_COST_PER_M + \
           (output_tokens / 1_000_000) * OUTPUT_COST_PER_M


# ─── Request model ────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []   # [{"role": "user"|"assistant", "content": "..."}]
    session_id: str = "default"



# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Non-streaming endpoint — returns the full response at once.
    Shown alongside /chat/stream so students can feel the UX difference.
    """
    if not check_rate_limit(request.session_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a moment.")

    # Build the full conversation: history + new user message
    contents = request.history + [{"role": "user", "parts": [request.message]}]
    response = model.generate_content(contents)
    usage = response.usage_metadata

    return {
        "response": response.text,
        "usage": {
            "input_tokens": usage.prompt_token_count,
            "output_tokens": usage.candidates_token_count,
            "estimated_cost_usd": estimate_cost(
                usage.prompt_token_count, usage.candidates_token_count
            ),
        },
    }


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming endpoint using Server-Sent Events (SSE).

    SSE wire format:
        data: {"type": "text", "content": "Hello"}\n\n
        data: {"type": "done", "usage": {...}}\n\n
    Each event is "data: <payload>\n\n" — the double newline ends the event.
    """
    if not check_rate_limit(request.session_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")

    def generate():
        # Build the full conversation: history + new user message
        contents = request.history + [{"role": "user", "parts": [request.message]}]
        response = model.generate_content(contents, stream=True)
        print(response)

        # Each chunk is a GenerateContentResponse with done=False until the last one.
        # Structure of each chunk:
        #   candidates[0].content.parts[0].text  — the token(s) generated in this chunk
        #   usage_metadata.prompt_token_count     — input tokens (only reliable on the last chunk)
        #   usage_metadata.candidates_token_count — output tokens so far
        # chunk.text is a shorthand for candidates[0].content.parts[0].text
        # See https://ai.google.dev/gemini-api/docs/text-generation# for details on the response structure.
        # On each iteration it blocks until Gemini sends the next chunk. So   
        # the loop:                                                                                                                                                                                  
        #   1. Asks Gemini for the next chunk — blocks here until it arrives                                                                                           
        #   2. If the chunk has text, yields it to the browser
        #   3. Goes back to step 1                                                                                                                                     
        # When Gemini signals it is done (no more chunks), the for loop exits naturally and execution continues to the usage_metadata and the final done event. 
        for chunk in response:
            if chunk.text:
                event = json.dumps({"type": "text", "content": chunk.text})
                yield f"data: {event}\n\n"

        # After iteration, usage_metadata is populated
        usage = response.usage_metadata
        done_event = json.dumps({
            "type": "done",
            "usage": {
                "input_tokens": usage.prompt_token_count,
                "output_tokens": usage.candidates_token_count,
                "estimated_cost_usd": estimate_cost(
                    usage.prompt_token_count, usage.candidates_token_count
                ),
            },
        })
        yield f"data: {done_event}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # tells nginx: don't buffer this
        },
    )
