import os
import json
from dotenv import load_dotenv
from groq import Groq
import streamlit as st
from PIL import Image
import pytesseract
from pdfminer.high_level import extract_text

# ---------------- OCR UTILS ----------------
# Define OCR function here to avoid import issues
pytesseract.pytesseract.tesseract_cmd = r"D:\Tesseract-OCR\tesseract.exe"

def extract_text_from_image(image_path):
    """Extract text from an image using pytesseract."""
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print("Error in OCR:", e)
        return ""


# ---------------- ENV & API ----------------
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise ValueError("❌ GROQ_API_KEY missing in .env")

client = Groq(api_key=API_KEY)
MODEL = "llama-3.1-8b-instant"

SYSTEM_PROMPT = """
You are an AI Interview Coach.

You must answer ONLY interview-related questions such as:
- Technical interview questions
- HR and behavioral interview questions
- Resume or project explanation
- Mock interview practice
- Career guidance related to interviews

If the user asks anything else, reply only:
"I am designed to help only with interview-related questions. Please ask an interview-related question."
"""


# ---------------- GROQ CALL ----------------
def call_groq(prompt: str) -> str:
    """Call Groq LLM and return text response."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=400
    )
    return response.choices[0].message.content.strip()


# ---------------- GENERATE QUESTIONS ----------------
def generate_questions(role: str, round_type: str):
    """Generate 5 interview questions based on role and round type"""
    prompt = f"""
Generate exactly 5 {round_type} interview questions
for the role of {role}.
Rules:
- One question per line
- No numbering
- No explanations
"""
    text = call_groq(prompt)
    questions = [q.strip() for q in text.split("\n") if q.strip()]
    return questions[:5]


def generate_questions_from_resume(file_path: str):
    """Generate 5 interview questions from PDF or image resume"""
    resume_text = ""

    # PDF
    if file_path.lower().endswith(".pdf"):
        try:
            resume_text = extract_text(file_path)
        except Exception:
            resume_text = ""

    # Image
    elif file_path.lower().endswith((".png", ".jpg", ".jpeg")):
        resume_text = extract_text_from_image(file_path)

    else:
        return ["❌ Unsupported resume format. Upload PDF, JPG, or PNG."]

    if not resume_text or len(resume_text.strip()) < 20:
        return ["❌ Unable to read resume properly. Please upload a clear file."]

    prompt = f"""
This is the candidate resume:
{resume_text}

Generate exactly 5 interview questions based on this resume.
Rules:
- One question per line
- No numbering
- No explanations
"""
    text = call_groq(prompt)
    questions = [q.strip() for q in text.split("\n") if q.strip()]
    return questions[:5]


def get_scores(question: str, answer: str):
    """Evaluate candidate answer and return score + feedback"""
    prompt = f"""
    You are evaluating an interview answer.
    Question: {question}
    Candidate Answer: {answer}
    Evaluate based on:
      - Relevance
      - Clarity
      - Technical correctness
      - Completeness
    Respond ONLY in valid JSON format:
    {{
      "score": <integer between 0 and 10>,
      "feedback": "<2–3 lines of constructive feedback>"
    }}
    """
    try:
        raw_response = call_groq(prompt)
        data = json.loads(raw_response)
        score = int(data.get("score", 0))
        feedback = data.get("feedback", "No feedback provided.")
        score = max(0, min(score, 10))
    except Exception:
        score = 0
        feedback = "Unable to evaluate the answer properly."

    # DO NOT modify session_state here. Return result instead.
    return {"score": score, "feedback": feedback}


# ---------------- FINAL FEEDBACK ----------------
def final_feedback():
    """Calculate overall average score and provide verdict"""
    scores = st.session_state.get("scores", [])
    if not scores:
        return "No interview data available."

    avg = sum(scores) / len(scores)

    if avg >= 8:
        verdict = "🌟 Excellent! Interview ready."
    elif avg >= 5:
        verdict = "👍 Good, but needs more practice."
    else:
        verdict = "⚠️ Needs significant improvement."

    return (
        f"Average Score: {avg:.1f} / 10\n"
        f"Total Questions: {len(scores)}\n"
        f"Overall Verdict:\n{verdict}"
    )
