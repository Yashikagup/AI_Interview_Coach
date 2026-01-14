import os
import json
from dotenv import load_dotenv
from groq import Groq


load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise ValueError("❌ GROQ_API_KEY missing")

client = Groq(api_key=API_KEY)

MODEL = "llama-3.1-8b-instant"


scores = []



def call_groq(prompt: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a strict but fair interview evaluator. "
                    "You must analyze answers carefully and score realistically."
                )
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=400
    )

    content = response.choices[0].message.content
    return content.strip() if content else ""



def generate_questions(role: str, round_type: str):
    global scores
    scores = []  

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
  "strengths": "<1–2 lines explaining what was good>",
  "weaknesses": "<1–2 lines explaining what was missing or incorrect>",
  "improvement_tip": "<1 actionable suggestion to improve>",
  "summary_feedback": "<2 lines overall feedback>"
}}
"""

    raw_response = call_groq(prompt)

    try:
        raw_response = raw_response.strip()
        start = raw_response.find("{")
        end = raw_response.rfind("}") + 1
        json_str = raw_response[start:end]

        data = json.loads(json_str)

        score = int(data.get("score", 0))
        strengths = data.get("strengths", "Not specified.")
        weaknesses = data.get("weaknesses", "Not specified.")
        improvement = data.get("improvement_tip", "No suggestion provided.")
        summary = data.get("summary_feedback", "No feedback provided.")

        score = max(0, min(score, 10))

    except Exception:
        score = 0
        strengths = "Unable to analyze strengths."
        weaknesses = "Unable to analyze weaknesses."
        improvement = "Try answering with clearer structure."
        summary = "Evaluation failed."

    scores.append(score)

    return f"""
Score: {score}/10

✅ Strengths:
{strengths}

❌ Weaknesses:
{weaknesses}

💡 How to Improve:
{improvement}

📝 Overall Feedback:
{summary}
"""



def get_scores():
    return scores



def final_feedback():
    if not scores:
        return "No interview data available."

    avg = sum(scores) / len(scores)

    if avg >= 8:
        verdict = "🌟 Excellent! Interview ready."
    elif avg >= 5:
        verdict = "👍 Good, but needs more practice."
    else:
        verdict = "⚠️ Needs significant improvement."

    return f"""
Average Score: {avg:.1f} / 10
Total Questions: {len(scores)}

Overall Verdict:
{verdict}
"""
