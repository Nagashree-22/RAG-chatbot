import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from groq import APIError, Groq
from pydantic import BaseModel, Field

from models.chat_history import (
    clear_history,
    create_history_database,
    load_history,
    save_message,
)
from models.emotion import detect_emotion
from models.rag import retrieve_documents


PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

logger = logging.getLogger(__name__)
app = FastAPI(title="MindCare AI API")
app.mount(
    "/assets",
    StaticFiles(directory=str(PROJECT_ROOT / "assets")),
    name="assets",
)

Emotion = Literal[
    "joy",
    "sadness",
    "anger",
    "fear",
    "love",
    "surprise",
    "neutral",
    "health_issue",
    "fever",
    "headache",
    "stomach_ache",
    "cold",
    "period",
    "cramps",
    "pms",
    "mood_swing",
    "stress",
    "loneliness",
]

ROBOT_IMAGES = {
    "joy": "robot_happy.png",
    "sadness": "robot_sad.png",
    "anger": "robot_angry.png",
    "fear": "robot_fear.png",
    "love": "robot_love.png",
    "surprise": "robot_surprised.png",
    "neutral": "robot_neutral.png",
    "health_issue": "robot_caring.png",
    "fever": "robot_caring.png",
    "headache": "robot_caring.png",
    "stomach_ache": "robot_caring.png",
    "cold": "robot_caring.png",
    "period": "robot_caring.png",
    "cramps": "robot_caring.png",
    "pms": "robot_caring.png",
    "mood_swing": "robot_caring.png",
    "stress": "robot_sad.png",
    "loneliness": "robot_sad.png",
}


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


@lru_cache(maxsize=1)
def get_groq_client(api_key: str) -> Groq:
    return Groq(api_key=api_key)


def _emotion_payload(message: str) -> dict[str, object]:
    result = detect_emotion(message)
    emotion = result["emotion"]
    return {
        "emotion": emotion,
        "confidence": result["confidence"],
        "suggestions": result["suggestions"],
        "robot_image": f"/assets/{ROBOT_IMAGES[emotion]}",
    }


@app.on_event("startup")
def initialize_history() -> None:
    create_history_database()


@app.get("/api/health")
def health_check() -> dict[str, bool | str | int]:
    from models.rag import collection

    return {
        "status": "ok",
        "groq_configured": bool(os.getenv("GROQ_API_KEY")),
        "knowledge_documents": collection.count(),
    }


@app.get("/api/history")
def get_history() -> list[dict[str, str]]:
    return load_history()


@app.delete("/api/history")
def delete_history() -> dict[str, str]:
    clear_history()
    return {"status": "cleared"}


@app.post("/api/emotion")
def preview_emotion(request: ChatRequest) -> dict[str, object]:
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="Message cannot be blank.")
    return _emotion_payload(message)


@app.post("/api/chat")
def chat(request: ChatRequest) -> StreamingResponse:
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="Message cannot be blank.")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="GROQ_API_KEY is missing. Add it to the project .env file.",
        )

    local_emotion = _emotion_payload(message)
    try:
        documents = retrieve_documents(message)
        context = "\n\n".join(documents)
        client = get_groq_client(api_key)
    except APIError as error:
        logger.exception("Groq request failed")
        raise HTTPException(
            status_code=502,
            detail="The AI service could not complete the request. Please try again.",
        ) from error

    def stream_answer():
        parts = []
        try:
            with client.chat.completions.create(
                model=os.getenv("GROQ_MODEL", "allam-2-7b"),
                max_completion_tokens=220,
                temperature=0.8,
                stream=True,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are MindCare AI, but speak like a genuinely caring human friend who is calm, warm, and emotionally aware. "
                            "Do not sound robotic, clinical, or distant. Talk directly to the person as if you are comforting a friend: gentle, supportive, and natural. "
                            "If the person sounds sad, overwhelmed, lonely, exhausted, or in pain, respond with sincere empathy first, acknowledge what they are feeling, and comfort them without judgment. "
                            "If they mention physical pain, discomfort, or health issues, respond with reassurance, calm guidance, and practical, non-diagnostic support. "
                            "Use emotional understanding before advice. Say things like 'That sounds really tough', 'I’m sorry you’re going through this', or 'You don’t have to carry this alone.' "
                            "Keep responses conversational, warm, and personal, usually 2-5 sentences, and avoid sounding like a bot or a textbook. "
                            "Ask one simple follow-up question only if it helps them feel heard or supported. "
                            "Never diagnose, pretend to be a doctor, or invent medical facts. Be truthful about limits, but remain kind and comforting."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Relevant context:\n{context or 'None'}\n\n"
                            f"User message: {message}\n\n"
                            "Please respond in a direct, human, comforting way, like someone who understands emotion and truly cares."
                        ),
                    },
                ],
            ) as response:
                for chunk in response:
                    content = chunk.choices[0].delta.content
                    if content:
                        parts.append(content)
                        yield json.dumps(
                            {"type": "token", "content": content},
                            ensure_ascii=False,
                            separators=(",", ":"),
                        ) + "\n"

            answer = "".join(parts).strip()
            if not answer:
                raise ValueError("The language model returned an empty response.")
            save_message("user", message)
            save_message("assistant", answer)
            yield json.dumps(
                {
                    "type": "done",
                    "answer": answer,
                    **local_emotion,
                    "retrieved_documents": documents,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            ) + "\n"
        except APIError as error:
            logger.exception("Groq streaming request failed")
            yield json.dumps(
                {
                    "type": "error",
                    "detail": (
                        "The AI service could not complete the request. Please try again."
                    ),
                },
                separators=(",", ":"),
            ) + "\n"
        except (TypeError, ValueError):
            logger.exception("Could not validate the streamed AI response")
            yield json.dumps(
                {
                    "type": "error",
                    "detail": (
                        "The AI service returned an invalid response. Please try again."
                    ),
                },
                separators=(",", ":"),
            ) + "\n"

    return StreamingResponse(
        stream_answer(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
