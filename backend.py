import os
import requests
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("❌ GEMINI_API_KEY missing")


MODEL = "gemini-1.5-pro"

API_URL = f"https://generativelanguage.googleapis.com/v1/models/{MODEL}:generateContent?key={API_KEY}"

scores = []



def call_gemini(prompt: str) -> str:
    response = requests.post(
        API_URL,
        headers={"Content-Type": "application/json"},
        json={
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }
    )

    if response.status_code != 200:
        raise RuntimeError(response.text)

    return response.json()["candidates"][0]["content"]["parts"][0]["text"]



def generate_questions(role):
    global scores
    scores = []

    prompt = f"""
Generate exactly 5 interview questions for the role of {role}.
Return only the questions, each on a new line.
"""

    text = call_gemini(prompt)
    return [q.strip() for q in text.split("\n") if q.strip()]


def evaluate_answer(question, answer):
    prompt = f"""
Question: {question}
Answer: {answer}

Give:
1) Score out of 10
2) Short feedback (2 lines)
"""

    text = call_gemini(prompt)

    score = 0
    for line in text.splitlines():
        digits = "".join(filter(str.isdigit, line))
        if digits:
            score = min(int(digits), 10)
            break

    scores.append(score)
    return text


def final_feedback():
    if not scores:
        return "No interview data available."

    avg = sum(scores) / len(scores)

    if avg >= 8:
        verdict = "🌟 Excellent! Interview ready."
    elif avg >= 5:
        verdict = "👍 Good, but needs practice."
    else:
        verdict = "⚠️ Needs improvement."

    return f"""
Average Score: {avg:.1f} / 10
Questions Answered: {len(scores)}

Overall Verdict:
{verdict}
"""
