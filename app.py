
"""
StudyBuddy AI - Notes Summarizer, Flashcard and Quiz Generator

Run:
    python -m streamlit run app.py
"""

import json
import os

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pypdf import PdfReader
import time


# ------------------------- CONFIGURATION -------------------------

load_dotenv()

MODEL = "gemini-3.8-flash"
MAX_CHARS = 30000

SYSTEM_PROMPT = """
You are StudyBuddy AI, an expert study assistant.
Use only the study material provided by the user.
Do not invent facts that are not supported by the material.
Return valid JSON only, without Markdown code fences.
"""


TASKS = {
    "Summary": (
        'Return JSON with this structure: '
        '{"summary": "A 150-200 word summary", '
        '"key_points": ["5-8 important points"]}.'
    ),

    "Flashcards": (
        'Return JSON with this structure: '
        '{"flashcards": [{"front": "Question or term", '
        '"back": "Concise answer"}]}. '
        'Generate exactly {n} flashcards.'
    ),

    "Quiz": (
        'Return JSON with this structure: '
        '{"quiz": [{"question": "Question", '
        '"options": ["Option A", "Option B", "Option C", "Option D"], '
        '"answer_index": 0, "explanation": "Explanation"}]}. '
        'Generate exactly {n} multiple-choice questions at '
        '{level} difficulty. The answer_index must be an integer '
        'from 0 to 3. Exactly one option must be correct.'
    ),
}


# ------------------------- FILE READING -------------------------

def read_upload(uploaded_file):
    """Extract text from a PDF or TXT file."""

    if uploaded_file.name.lower().endswith(".pdf"):
        reader = PdfReader(uploaded_file)

        text = "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

        return text

    return uploaded_file.read().decode(
        "utf-8",
        errors="ignore"
    )


# ------------------------- PROMPT CREATION -------------------------

def build_prompt(task, material, n, level):
    """Build the prompt for the selected task."""

    instruction = (
        TASKS[task]
        .replace("{n}", str(n))
        .replace("{level}", level)
    )

    return (
        f"{instruction}\n\n"
        "STUDY MATERIAL:\n"
        f"{material[:MAX_CHARS]}"
    )


# ------------------------- GEMINI API -------------------------

def call_model(api_key, prompt):
    """Call Gemini and convert its JSON response to a dictionary."""

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.4,
            response_mime_type="application/json",
        ),
    )

    if not response.text:
        raise ValueError(
            "Gemini returned an empty response. Please try again."
        )

    return json.loads(response.text.strip())


# ------------------------- PAGE SETTINGS -------------------------

st.set_page_config(
    page_title="StudyBuddy AI",
    page_icon="📚",
    layout="wide",
)

st.title("📚 StudyBuddy AI")

st.caption(
    "Turn your study notes into summaries, flashcards, "
    "and quizzes using Google Gemini."
)


# ------------------------- SIDEBAR -------------------------

with st.sidebar:
    st.header("Settings")

    api_key = os.getenv("GEMINI_API_KEY", "")

    task = st.radio(
        "What do you want to generate?",
        ["Summary", "Flashcards", "Quiz"],
    )

    if task == "Summary":
        n = 0
        level = ""

    elif task == "Flashcards":
        n = st.slider(
            "Number of flashcards",
            min_value=3,
            max_value=10,
            value=5,
        )
        level = ""

    else:
        n = st.slider(
            "Number of questions",
            min_value=3,
            max_value=10,
            value=5,
        )

        level = st.selectbox(
            "Difficulty",
            ["easy", "medium", "hard"],
            index=1,
        )

    st.markdown(f"**Model:** `{MODEL}`")


# ------------------------- MAIN LAYOUT -------------------------

col_in, col_out = st.columns(2)


with col_in:
    st.subheader("1. Provide Your Study Material")

    uploaded_file = st.file_uploader(
        "Upload a PDF or TXT file",
        type=["pdf", "txt"],
    )

    pasted_text = st.text_area(
        "Or paste your study notes here",
        height=260,
        placeholder="Paste at least 100 characters of study material...",
    )

    material = ""

    if uploaded_file is not None:
        try:
            material = read_upload(uploaded_file)
        except Exception as error:
            st.error(f"Unable to read the uploaded file: {error}")

    elif pasted_text:
        material = pasted_text

    if material:
        st.caption(
            f"{len(material):,} characters loaded"
            + (
                f" (using the first {MAX_CHARS:,} characters)"
                if len(material) > MAX_CHARS
                else ""
            )
        )

    generate_button = st.button(
        f"✨ Generate {task}",
        type="primary",
        use_container_width=True,
    )


# ------------------------- GENERATE OUTPUT -------------------------

if generate_button:

    if not api_key:
        st.error(
            "Please enter your Gemini API key in the sidebar."
        )

    elif len(material.strip()) < 100:
        st.error(
            "Please provide at least 100 characters "
            "of study material."
        )

    else:
        try:
            with st.spinner(
                "StudyBuddy AI is processing your notes..."
            ):
                prompt = build_prompt(
                    task,
                    material,
                    n,
                    level,
                )

                result = call_model(
                    api_key,
                    prompt,
                )

                st.session_state["result"] = result
                st.session_state["task"] = task
                st.session_state.pop("submitted", None)

        except json.JSONDecodeError:
            st.error(
                "The AI returned invalid JSON. Please try again."
            )

        except Exception as error:
            st.error(f"API error: {error}")


# ------------------------- DISPLAY RESULTS -------------------------

with col_out:
    st.subheader("2. Your Generated Study Aid")

    result = st.session_state.get("result")
    selected_task = st.session_state.get("task")

    if not result:
        st.info(
            "Your generated summary, flashcards, or quiz "
            "will appear here."
        )

    elif selected_task == "Summary":

        st.markdown("### Summary")

        st.write(result.get("summary", ""))

        st.markdown("### Key Points")

        for point in result.get("key_points", []):
            st.markdown(f"- {point}")

    elif selected_task == "Flashcards":

        flashcards = result.get("flashcards", [])

        for index, card in enumerate(flashcards, start=1):

            with st.expander(
                f"Card {index}: {card.get('front', 'Flashcard')}"
            ):
                st.write(card.get("back", ""))

    elif selected_task == "Quiz":

        quiz = result.get("quiz", [])

        if not quiz:
            st.warning("No quiz questions were generated.")

        else:
            st.markdown("### Test Your Knowledge")

            for index, question in enumerate(quiz):

                st.radio(
                    f"Q{index + 1}. {question['question']}",
                    question["options"],
                    index=None,
                    key=f"studybuddy_q_{index}",
                )

            if st.button("Submit Answers"):

                st.session_state["submitted"] = True

            if st.session_state.get("submitted"):

                score = 0

                for index, question in enumerate(quiz):

                    selected_answer = st.session_state.get(
                        f"studybuddy_q_{index}"
                    )

                    answer_index = question["answer_index"]

                    if not 0 <= answer_index < len(
                        question["options"]
                    ):
                        st.error(
                            f"Invalid answer data for Q{index + 1}."
                        )
                        continue

                    correct_answer = question["options"][
                        answer_index
                    ]

                    if selected_answer == correct_answer:
                        score += 1

                        st.success(
                            f"Q{index + 1}: Correct! "
                            f"{question.get('explanation', '')}"
                        )

                    else:
                        st.error(
                            f"Q{index + 1}: Incorrect. "
                            f"Correct answer: {correct_answer}. "
                            f"{question.get('explanation', '')}"
                        )

                st.metric(
                    "Your Score",
                    f"{score} / {len(quiz)}",
                )


# ------------------------- DOWNLOAD OUTPUT -------------------------

if result := st.session_state.get("result"):

    st.divider()

    st.download_button(
        label="⬇ Download Output (JSON)",
        data=json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        ),
        file_name="studybuddy_output.json",
        mime="application/json",
    )