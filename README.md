# StudyBuddy AI

A GenAI web app that turns study notes (pasted text or PDF/TXT) into a summary,
flashcards or an interactive quiz using Google Gemini.

## Setup
1. Install Python 3.10+.
2. Get a free API key at https://aistudio.google.com/apikey
3. In this folder:
   ```
   python -m venv venv
   venv\Scripts\activate        # Windows  (Mac/Linux: source venv/bin/activate)
   pip install -r requirements.txt
   copy .env.example .env       # then paste your key inside .env
   streamlit run app.py
   ```
4. Open http://localhost:8501

## Files
- `app.py` - whole application (UI, prompt builder, Gemini call)
- `requirements.txt` - dependencies
- `.env.example` - template for your API key (never upload your real `.env`)

## Deploy (free)
Push to GitHub -> https://share.streamlit.io -> New app -> select `app.py`
-> add `GEMINI_API_KEY` under Advanced settings > Secrets.
