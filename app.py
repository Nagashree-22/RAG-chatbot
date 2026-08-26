

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq


from models.emotion import detect_emotion
from models.rag import retriever


# Load API Key
load_dotenv()


api_key = os.getenv("GROQ_API_KEY")


if not api_key:
    raise ValueError("GROQ_API_KEY not found. Check your .env file.")


# Load LLM
llm = ChatGroq(
    model_name="openai/gpt-oss-20b",
    api_key=api_key
)


print("====================================")
print(" Emotion-Aware RAG Chatbot")
print(" Type 'exit' to quit")
print("====================================")


while True:


    user = input("\nYou: ")


    if user.lower() == "exit":
        print("Goodbye!")
        break


    # Detect emotion
    emotion = detect_emotion(user)


    # Retrieve relevant documents
    docs = retriever.invoke(user)


    context = ""


    for doc in docs:
        context += doc.page_content + "\n"


    # Build prompt
    prompt = f"""
You are a friendly, empathetic AI assistant.


Detected Emotion:
{emotion['emotion']}


Confidence:
{emotion['confidence']:.2f}


Knowledge Base:
{context}


User Question:
{user}


Instructions:
- Respond naturally.
- Show empathy when appropriate.
- Use the knowledge base if it is relevant.
- Do not make up facts if the knowledge base does not contain the answer.
- Keep the response clear and concise.
"""


    response = llm.invoke(prompt)


    print("\nAI:")
    print(response.content)


    print("\nSuggestions:")
    for i, suggestion in enumerate(emotion["suggestions"], start=1):
        print(f"{i}. {suggestion}")

