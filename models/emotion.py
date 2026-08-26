
from transformers import pipeline


# Load emotion detection model
emotion_model = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base",
    top_k=1
)


# Suggestions
EMOTION_SUGGESTIONS = {


    # ---------------- EMOTIONS ---------------- #


    "joy": [
        "😊 Keep enjoying this positive moment.",
        "🎉 Celebrate your achievement.",
        "📸 Capture this memory with a photo or journal.",
        "🎵 Dance or listen to your favorite songs.",
        "❤️ Share your happiness with someone close."
    ],


    "sadness": [
        "🎵 Listen to soothing music.",
        "🚶 Take a short walk in fresh air.",
        "😴 Get a good power nap.",
        "🚗 Go for a relaxing drive.",
        "📞 Talk to your friends or family.",
        "📖 Read a book or watch your favorite movie."
    ],


    "anger": [
        "😮‍💨 Take slow deep breaths.",
        "🚶 Walk away from the situation.",
        "🏃 Exercise or do a quick workout.",
        "📝 Write down your thoughts.",
        "🎧 Listen to calming music."
    ],


    "fear": [
        "🌬️ Practice deep breathing.",
        "🧘 Focus on one step at a time.",
        "👨‍👩‍👧 Talk to someone you trust.",
        "💪 Remind yourself of your strengths.",
        "☕ Take a short break and relax."
    ],


    "love": [
        "❤️ Spend quality time with loved ones.",
        "🙏 Express gratitude.",
        "💬 Tell people how much they mean to you.",
        "🤝 Accept people as they are."
    ],


    "surprise": [
        "😄 Take a moment to process what happened.",
        "🎯 Learn something from the experience.",
        "🌟 Stay open to new opportunities."
    ],


    "neutral": [
        "🌞 Have a productive day.",
        "💧 Stay hydrated.",
        "🍎 Eat healthy meals.",
        "🚶 Take small breaks during work."
    ],


    # ---------------- HEALTH ---------------- #


    "health_issue": [
        "💧 Drink plenty of water.",
        "😴 Get enough rest.",
        "🥗 Eat nutritious food.",
        "💊 Take medicines only if prescribed.",
        "🩺 Consult a doctor if symptoms worsen."
    ],


    "fever": [
        "🌡️ Monitor your temperature.",
        "💧 Drink plenty of fluids.",
        "🛌 Get enough rest.",
        "🩺 Consult a doctor if fever persists."
    ],


    "headache": [
        "💧 Drink water.",
        "😴 Rest in a quiet room.",
        "📵 Reduce screen time.",
        "🩺 Seek medical advice if severe."
    ],


    "stomach_ache": [
        "💧 Drink water slowly.",
        "🍲 Eat light food.",
        "🛌 Take some rest.",
        "🌡️ Use a warm compress if comfortable.",
        "🩺 Visit a doctor if pain continues."
    ],


    "cold": [
        "☕ Drink warm fluids.",
        "😴 Get enough sleep.",
        "🍊 Eat Vitamin C rich foods.",
        "🩺 Consult a doctor if symptoms worsen."
    ],


    # ---------------- PERIOD ---------------- #


    "period": [
        "💧 Stay hydrated.",
        "🌡️ Use a heating pad.",
        "🥗 Eat iron-rich foods.",
        "😴 Get enough rest.",
        "🚶 Do light stretching.",
        "🩺 Consult a doctor if pain is severe."
    ],


    "cramps": [
        "🌡️ Apply a heating pad.",
        "💧 Drink warm water.",
        "🧘 Stretch gently.",
        "😴 Get enough rest.",
        "🩺 Consult a doctor if cramps are severe."
    ],


    "pms": [
        "🥗 Eat healthy snacks.",
        "🚶 Exercise lightly.",
        "😴 Sleep well.",
        "🎵 Listen to calming music.",
        "🧘 Practice relaxation."
    ],


    "mood_swing": [
        "🌬️ Take deep breaths.",
        "🎵 Listen to relaxing music.",
        "🚶 Go for a short walk.",
        "📝 Journal your feelings.",
        "💬 Talk to someone you trust.",
        "😴 Get enough sleep."
    ],


    # ---------------- STRESS ---------------- #


    "stress": [
        "🧘 Practice meditation.",
        "🌬️ Take deep breaths.",
        "🚶 Go for a walk.",
        "🎧 Listen to relaxing music.",
        "☕ Take regular breaks."
    ],


    "loneliness": [
        "📞 Call a friend or family member.",
        "🎨 Spend time on a hobby.",
        "☕ Visit a nearby park or café.",
        "📚 Read a good book.",
        "❤️ Reach out to someone you trust."
    ]
}




def detect_emotion(text):


    if not text.strip():
        return {
            "emotion": "neutral",
            "confidence": 0.0,
            "suggestions": EMOTION_SUGGESTIONS["neutral"]
        }


    text = text.lower()


    # ---------------- PERIOD ---------------- #


    if any(word in text for word in ["period", "menstruation", "menstrual", "cycle"]):
        return {
            "emotion": "period",
            "confidence": 1.0,
            "suggestions": EMOTION_SUGGESTIONS["period"]
        }


    elif any(word in text for word in ["cramp", "cramps", "period pain"]):
        return {
            "emotion": "cramps",
            "confidence": 1.0,
            "suggestions": EMOTION_SUGGESTIONS["cramps"]
        }


    elif any(word in text for word in ["pms"]):
        return {
            "emotion": "pms",
            "confidence": 1.0,
            "suggestions": EMOTION_SUGGESTIONS["pms"]
        }


    elif any(word in text for word in ["mood swing", "mood swings", "hormonal", "irritable"]):
        return {
            "emotion": "mood_swing",
            "confidence": 1.0,
            "suggestions": EMOTION_SUGGESTIONS["mood_swing"]
        }


    # ---------------- HEALTH ---------------- #


    elif any(word in text for word in ["stomach ache", "stomach pain", "abdominal pain", "tummy pain"]):
        return {
            "emotion": "stomach_ache",
            "confidence": 1.0,
            "suggestions": EMOTION_SUGGESTIONS["stomach_ache"]
        }


    elif any(word in text for word in ["headache", "migraine"]):
        return {
            "emotion": "headache",
            "confidence": 1.0,
            "suggestions": EMOTION_SUGGESTIONS["headache"]
        }


    elif any(word in text for word in ["fever", "temperature"]):
        return {
            "emotion": "fever",
            "confidence": 1.0,
            "suggestions": EMOTION_SUGGESTIONS["fever"]
        }


    elif any(word in text for word in ["cold", "cough", "runny nose", "sneezing", "sore throat"]):
        return {
            "emotion": "cold",
            "confidence": 1.0,
            "suggestions": EMOTION_SUGGESTIONS["cold"]
        }


    elif any(word in text for word in [
        "body pain",
        "back pain",
        "neck pain",
        "leg pain",
        "hand pain",
        "joint pain",
        "muscle pain"
    ]):
        return {
            "emotion": "health_issue",
            "confidence": 1.0,
            "suggestions": EMOTION_SUGGESTIONS["health_issue"]
        }


    # ---------------- STRESS ---------------- #


    elif any(word in text for word in ["stress", "stressed", "pressure", "overwhelmed"]):
        return {
            "emotion": "stress",
            "confidence": 1.0,
            "suggestions": EMOTION_SUGGESTIONS["stress"]
        }


    elif any(word in text for word in ["lonely", "alone", "isolated"]):
        return {
            "emotion": "loneliness",
            "confidence": 1.0,
            "suggestions": EMOTION_SUGGESTIONS["loneliness"]
        }


    # ---------------- HUGGING FACE MODEL ---------------- #


    result = emotion_model(text)


    emotion = result[0][0]["label"]
    confidence = result[0][0]["score"]


    return {
        "emotion": emotion,
        "confidence": confidence,
        "suggestions": EMOTION_SUGGESTIONS.get(
            emotion,
            ["Take care of yourself."]
        )
    }

