
import sys
import os


# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)


import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq


from models.emotion import detect_emotion
from models.rag import retriever


# Load environment variables
load_dotenv()


api_key = os.getenv("GROQ_API_KEY")


if not api_key:
    st.error("❌ GROQ_API_KEY not found in .env file")
    st.stop()


# Load LLM
llm = ChatGroq(
    model_name="openai/gpt-oss-20b",
    api_key=api_key
)


# Streamlit page settings
st.set_page_config(
    page_title="Emotion Aware RAG Chatbot",
    page_icon="🤖",
    layout="centered"
)


st.title("🤖 Emotion Aware RAG Chatbot")
st.write("Ask me anything about your emotions or health.")


# User input
question = st.text_input("Enter your question")


if st.button("Send"):


    if question.strip() == "":
        st.warning("Please enter a question.")
        st.stop()


    # Detect emotion
    emotion = detect_emotion(question)


    # Retrieve knowledge
    docs = retriever.invoke(question)


    context = ""


    for doc in docs:
        context += doc.page_content + "\n"


    # Prompt for LLM
    prompt = f"""
You are an empathetic AI assistant.


Detected Emotion:
{emotion['emotion']}


Confidence:
{emotion['confidence']:.2f}


Knowledge Base:
{context}


User Question:
{question}


Instructions:
- Respond naturally.
- Be empathetic.
- Use the knowledge base if relevant.
- If the knowledge base doesn't contain the answer, answer politely using general knowledge.
"""


    # Get response
    response = llm.invoke(prompt)


    # Display emotion
    st.subheader("😊 Detected Emotion")
    st.success(emotion["emotion"])


    # Display confidence
    st.subheader("🎯 Confidence")
    st.write(f"{emotion['confidence']:.2%}")


    # Display chatbot response
    st.subheader("🤖 AI Response")
    st.write(response.content)


    # Display suggestions
    st.subheader("💡 Suggestions")
    for suggestion in emotion["suggestions"]:
        st.write(f"• {suggestion}")


    # Display retrieved knowledge
    with st.expander("📚 Retrieved Knowledge"):
        st.write(context)


#python -m streamlit run frontend\streamlit_app.py  (To exectute)