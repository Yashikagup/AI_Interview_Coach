import os
import json
from dotenv import load_dotenv
from groq import Groq
import streamlit as st

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise ValueError("❌ GROQ_API_KEY missing")

client = Groq(api_key=API_KEY)
MODEL = "llama-3.1-8b-instant"

def call_groq(prompt: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a strict but fair interview evaluator. You must analyze answers carefully and score realistically."
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=400
    )
    return response.choices[0].message.content.strip()

def generate_questions(role: str, round_type: str):
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
    if "scores" not in st.session_state:
        st.session_state.scores = []
    st.session_state.scores = []
    return questions[:5]

def evaluate_answer(question: str, answer: str):
    prompt = f"""
You are evaluating an interview answer.
Question:
{question}
Candidate Answer:
{answer}
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
    raw_response = call_groq(prompt)
    try:
        data = json.loads(raw_response)
        score = int(data.get("score", 0))
        feedback = data.get("feedback", "No feedback provided.")
        score = max(0, min(score, 10))
    except Exception:
        score = 0
        feedback = "Unable to evaluate the answer properly."
    return {"score": score, "feedback": feedback}

def get_scores():
    return st.session_state.get("scores", [])

def final_feedback():
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
    return f"Average Score: {avg:.1f} / 10\nTotal Questions: {len(scores)}\nOverall Verdict:\n{verdict}"
