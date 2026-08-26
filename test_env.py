

from dotenv import load_dotenv
import os


print("Current Directory:", os.getcwd())


loaded = load_dotenv()


print("Loaded:", loaded)


key = os.getenv("GROQ_API_KEY")


if key:
    print("✅ API Key Loaded")
    print("Starts with:", key[:8] + "...")
else:
    print("❌ API Key NOT Loaded")



