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
ChatRole = Literal["user", "assistant"]

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


class ChatTurn(BaseModel):
    role: ChatRole
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation: list[ChatTurn] = Field(default_factory=list, max_length=8)


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


def _chat_messages(
    message: str,
    context: str,
    conversation: list[ChatTurn],
) -> list[dict[str, str]]:
    messages = [
        {
            "role": "system",
            "content": (
                "You are MindCare AI, a warm, friendly wellbeing companion who sounds like a caring friend. "
                "Keep replies short, relaxed, and natural, like a real conversation. "
                "Acknowledge the user's feelings in a simple way, then gently encourage them to tell you more. "
                "Do not sound robotic or give a list of tips. Be warm, personal, and easy to talk to. "
                "Remember the recent conversation and avoid repeating earlier advice. "
                "When someone is stressed, sad, lonely, or in pain, respond with empathy before offering support. "
                "Never diagnose, pretend to be a doctor, or invent medical facts. "
                "Usually reply in 1-3 sentences, with a soft, comforting tone."
            ),
        },
        *[
            {"role": turn.role, "content": turn.content}
            for turn in conversation
        ],
        {
            "role": "user",
            "content": (
                f"Relevant context:\n{context or 'None'}\n\n"
                f"User message: {message}"
            ),
        },
    ]
    return messages


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
                max_completion_tokens=160,
                temperature=0.8,
                stream=True,
                messages=_chat_messages(
                    message,
                    context,
                    request.conversation,
                ),
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
