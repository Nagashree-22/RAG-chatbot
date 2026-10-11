# MindCare AI

MindCare AI uses a React frontend with a Python API. The API retrieves relevant
passages from the existing Chroma index and calls Groq for a concise response.
Emotion is classified locally, so the matching robot image can appear before
the AI response arrives.

## Run locally on Windows

1. Add `GROQ_API_KEY=your_key` to the project-root `.env` file.
   Optionally set `GROQ_MODEL=allam-2-7b` to choose the Groq model.
   Replies stream into the chat as the model generates them.
2. Install the Python dependencies in the project environment:

   ```powershell
   .\venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

3. Install the frontend dependencies:

   ```powershell
   cd frontend
   npm install
   ```

4. Start the API in one terminal from the project root:

   ```powershell
   .\venv\Scripts\python.exe app.py
   ```

5. Start React in another terminal:

   ```powershell
   cd frontend
   npm run dev
   ```

6. Open <http://127.0.0.1:5173>.

The API is available at <http://127.0.0.1:8000/api/health>. The React
development server proxies API and image requests to it. The app uses Chroma's
ONNX text embedder and the Groq SDK directly; it does not import Streamlit,
Transformers, or PyTorch to run the React experience.

## Run the backend checks

From the project root:

```powershell
.\venv\Scripts\python.exe test.py
```
