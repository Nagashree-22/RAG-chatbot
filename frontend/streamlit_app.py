


import sys
import os
import base64
import streamlit as st


# -----------------------------
# Project Path
# -----------------------------
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)


from dotenv import load_dotenv
from langchain_groq import ChatGroq


from models.emotion import detect_emotion
from models.rag import retriever
from models.chat_history import (
    create_history_database,
    save_message,
    load_history,
    clear_history
)
create_history_database()

# -----------------------------
# Environment
# -----------------------------
load_dotenv(os.path.join(project_root, ".env"))


api_key = os.getenv("GROQ_API_KEY")
llm = ChatGroq(
    model_name="openai/gpt-oss-20b",
    api_key=api_key
)


# -----------------------------
# Page
# -----------------------------
st.set_page_config(
    page_title="MindCare AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# -----------------------------
# Helpers
# -----------------------------
@st.cache_data
def get_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()
# -----------------------------
# Emotion Robot Function
# -----------------------------
def show_emotion_robot(emotion):

    emotion_images = {
        "joy": "robot_happy.png",
        "happy": "robot_happy.png",
        "sadness": "robot_sad.png",
        "sad": "robot_sad.png",
        "anger": "robot_angry.png",
        "angry": "robot_angry.png",
        "fear": "robot_fear.png",
        "surprise": "robot_surprised.png",
        "surprised": "robot_surprised.png",
        "love": "robot_love.png",
        "caring": "robot_caring.png",
        "neutral": "robot_neutral.png"
    }

    # Clean emotion name
    emotion = emotion.lower().strip()

    # Select robot
    robot_file = emotion_images.get(
        emotion,
        "robot_neutral.png"
    )

    robot_path = os.path.join(
        project_root,
        "assets",
        robot_file
    )

    robot_base64 = get_base64(robot_path)

    # IMPORTANT:
    robot_html = (
    f'<div class="emotion-robot-popup">'
    f'<img src="data:image/png;base64,{robot_base64}" '
    f'class="emotion-robot-image">'
    f'</div>'
)

    st.markdown(
        robot_html,
        unsafe_allow_html=True
    )


bg = get_base64(os.path.join(project_root, "assets", "background.jpg"))
bot = get_base64(os.path.join(project_root, "assets", "chatbot.png"))


# -----------------------------
# Load CSS
# -----------------------------
with open(os.path.join(project_root, "css", "style.css")) as f:
    css = f.read()

st.markdown(
    f"""
<style>
{css}

.stApp {{
    background-image: url("data:image/jpeg;base64,{bg}") !important;
    background-repeat: no-repeat !important;
    background-size: cover !important;
    background-position: center center !important;
    background-attachment: fixed !important;
}}

</style>
""",
    unsafe_allow_html=True
)
# -----------------------------
# Starting Welcome Robot
# -----------------------------
if "welcome_robot_shown" not in st.session_state:
    st.session_state.welcome_robot_shown = False

if not st.session_state.welcome_robot_shown:
    st.markdown(
        f"""<div class="welcome-robot">
<img src="data:image/png;base64,{bot}" class="welcome-robot-img">
</div>""",
        unsafe_allow_html=True
    )

    st.session_state.welcome_robot_shown = True

with st.sidebar:

    st.image(
        os.path.join(project_root, "assets", "logo.png"),
        width=120
    )

    st.markdown("# 🤖 MindCare AI")

    st.markdown("---")

    if st.button("💬 New Chat"):
       st.session_state.messages = []
       st.rerun()

    # HISTORY ICON
    if "show_history" not in st.session_state:
        st.session_state.show_history = False

    if st.button("🕘", help="Chat History"):
        st.session_state.show_history = not st.session_state.show_history

    if st.session_state.show_history:

        st.markdown("### 🕘 Chat History")

        history = load_history()

        if history:
            for message in history:

                if message["role"] == "user":
                    st.markdown(
                        f"👤 **You:** {message['content']}"
                    )
                else:
                    st.markdown(
                        f"🤖 **MindCare:** {message['content']}"
                    )

                st.markdown("---")

        else:
            st.caption("No chat history yet.")

    st.button("⚙ Settings")

    st.markdown("---")

    st.caption("Emotion Aware RAG Assistant")
    # -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display current conversation
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
# -----------------------------
# Chat Input
# -----------------------------
question = st.chat_input(
    "💬 Share what's on your mind..."
)

if question:

    # Save user message
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    save_message("user", question)

    # Display user message
    with st.chat_message("user"):
        st.markdown(question)

    # -----------------------------
    # Emotion Detection
    # -----------------------------
    emotion_result = detect_emotion(question)

    emotion = emotion_result["emotion"]
    confidence = emotion_result["confidence"]
    suggestions = emotion_result["suggestions"]

    # -----------------------------
    # POP-UP EMOTION ROBOT
    # -----------------------------
    show_emotion_robot(emotion)

    # -----------------------------
    # Retrieve Knowledge
    # -----------------------------
    docs = retriever.invoke(question)

    context = "\n\n".join(
        [doc.page_content for doc in docs]
    )

    # -----------------------------
    # Prompt
    # -----------------------------
    prompt = f"""
You are MindCare AI.

Detected Emotion:
{emotion}

Knowledge:
{context}

User:
{question}

Respond naturally.
Be empathetic.
Use the knowledge if relevant.
Do not mention that you are using RAG.
Keep the response conversational.
"""

       # -----------------------------
    # Assistant Response
    # -----------------------------
    try:
        response = llm.invoke(prompt)
        answer = response.content

    except Exception as e:
        answer = f"Sorry, something went wrong: {e}"

    # Store assistant message
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

    # Display assistant message
    with st.chat_message("assistant"):
        st.markdown(answer)

    # Save to database
    save_message("assistant", answer)
    # -----------------------------
    # Emotion Analysis
    # -----------------------------
    st.markdown("---")

    st.markdown(
        """
        <h2 style="color:white;">
        😊 Emotion Analysis
        </h2>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f"""
            <div class="info-card">
                😊 Emotion: <b>{emotion.title()}</b>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="info-card">
                🎯 Confidence: <b>{confidence:.2f}</b>
            </div>
            """,
            unsafe_allow_html=True
        )

    # -----------------------------
    # Suggestions
    # -----------------------------
    st.markdown("### 💡 Suggestions")

    for tip in suggestions:
        st.markdown(
            f"""
            <div class="suggestion-card">
                ✨ {tip}
            </div>
            """,
            unsafe_allow_html=True
        )

    # -----------------------------
    # Retrieved Knowledge
    # -----------------------------
    with st.expander("📚 Retrieved Knowledge"):

        if docs:
            for doc in docs:
                st.write(doc.page_content)
        else:
            st.write("No relevant knowledge found.")
st.markdown(
    """
    <hr>


    <center>


    <p style="color:white">


    🤖 MindCare AI • Emotion-Aware RAG Chatbot


    </p>


    </center>
    """,
    unsafe_allow_html=True
)

