import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import altair as alt
import re

from auth import signup, login
from backend import (
    generate_questions,
    get_scores,
    store_text_as_json,
    chunk_text,
    call_groq
)

from pdf_utils import generate_pdf
from ocr_utils import extract_text_from_resume



st.set_page_config(
    page_title="AI Interview Coach",
    layout="wide",
    initial_sidebar_state="expanded"
)


defaults = {
    "logged_in": False,
    "questions": [],
    "current_q": 0,
    "started": False,
    "completed": False,
    "answers": [],
    "feedbacks": [],
    "scores": [],
    "candidate_name": "Candidate",
    "dark_mode": False
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)


st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at top, #E0EAFF 0%, #F8FAFC 45%);
    font-family: 'Segoe UI', sans-serif;
}
.block-container {
    padding-top: 0rem !important;
    margin-top: 0rem !important;
    max-width: 1200px;
}
header, footer { visibility: hidden; }
.stButton > button {
    background: linear-gradient(135deg, #4F46E5, #6366F1);
    color: white !important;
    border-radius: 12px !important;
    padding: 0.6em 1.4em !important;
    font-size: 16px !important;
    border: none !important;
}
</style>
""", unsafe_allow_html=True)


st.markdown("""
<div style="
    background: linear-gradient(135deg, #6366F1, #8B5CF6);
    padding: 45px;
    border-radius: 22px;
    text-align: center;
    color: white;
    margin-bottom: 35px;">
    <h1 style="font-size:48px; margin:0;">AI Interview Coach</h1>
    <p style="font-size:18px; opacity:0.9;">
        Practice smarter. Get instant AI feedback.
    </p>
</div>
""", unsafe_allow_html=True)


if not st.session_state.logged_in:

    components.html("""
    <style>
      body { margin:0; font-family: system-ui, -apple-system, Segoe UI, Roboto; }
      .title{
        text-align:center;
        font-size:28px;
        font-weight:700;
        margin: 10px 0 30px 0;
      }
      .hero{
        display:flex;
        gap:30px;
        justify-content:center;
        flex-wrap:wrap;
      }
      .card{
        background:white;
        padding:25px;
        border-radius:18px;
        width:260px;
        box-shadow:0 8px 20px rgba(0,0,0,0.08);
        transition: transform .25s ease;
      }
      .card:hover{
        transform: translateY(-8px);
      }
    </style>

    <div class="title">Unlock Your Interview Success in 3 Steps!</div>
    <div class="hero">
        <div class="card">
          <h3>1️⃣ Choose a Role</h3>
          <p>Select your target role. AI generates tailored questions.</p>
        </div>
        <div class="card">
          <h3>2️⃣ Mock Interview</h3>
          <p>Answer questions in a real interview-style flow.</p>
        </div>
        <div class="card">
          <h3>3️⃣ AI Feedback</h3>
          <p>Get scores, insights, and improvement tips instantly.</p>
        </div>
    </div>
    """, height=360)

    st.markdown("### Login / Sign Up")
    mode = st.radio("Choose", ["Login", "Sign Up"], horizontal=True)
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if mode == "Login" and st.button("Login"):
        if login(user, pwd):
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid credentials")

    if mode == "Sign Up" and st.button("Create Account"):
        if signup(user, pwd):
            st.success("Account created. Login now.")
        else:
            st.error("Username already exists")

    st.stop()


# ---------------- SIDEBAR ----------------
# ---------------- SIDEBAR ----------------
with st.sidebar:

    st.markdown("""
    <div style="
        background:#1E293B;
        color:white;
        padding:22px;
        border-radius:18px;
        margin-bottom:20px;">
        <h2>🎯 Interview Setup</h2>
        <p style="font-size:14px;opacity:0.8;">
            Upload resume & start interview
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ✅ Resume upload in sidebar
    uploaded = st.file_uploader("📄 Upload Resume", type=["pdf", "jpg", "png"])

    if uploaded:
        path = f"uploaded_{uploaded.name}"

        with open(path, "wb") as f:
            f.write(uploaded.getbuffer())

        st.success("Resume uploaded ✅")

        # ✅ Generate questions button ALSO in sidebar
        if st.button("✨ Generate Resume Questions"):
            with st.spinner("OCR → JSON → Chunking → Model..."):

                resume_text = extract_text_from_resume(path)
                doc_id = store_text_as_json(resume_text)
                chunks = chunk_text(resume_text)

                questions = []
                for chunk in chunks[:3]:
                    prompt = f"""
                    This is part of candidate resume:
                    {chunk}

                    Generate interview questions.
                    One per line. No numbering.
                    """
                    resp = call_groq(prompt)
                    qs = [q.strip() for q in resp.split("\n") if q.strip()]
                    questions.extend(qs)

                    if len(questions) >= 5:
                        break

                questions = list(dict.fromkeys(questions))[:5]

            st.session_state.questions = questions
            n = len(questions)

            st.session_state.started = True
            st.session_state.current_q = 0
            st.session_state.completed = False
            st.session_state.answers = [""] * n
            st.session_state.feedbacks = [""] * n
            st.session_state.scores = [0] * n

            st.rerun()

    st.divider()

    # Dark mode
    st.session_state.dark_mode = st.toggle("🌙 Dark Mode")

    # Logout
    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()


# ---------------- DARK MODE STYLE ----------------
if st.session_state.get("dark_mode"):
    st.markdown("""
    <style>
    .stApp {
        background:#0F172A;
        color:white;
    }
    </style>
    """, unsafe_allow_html=True)


if not st.session_state.started:
    with st.container():
        role_input = st.text_input("🎯 Job Role", "Engineer")
        round_type_input = st.selectbox("🧠 Interview Round", ["Technical","Behavioral","HR"])

        if st.button("🚀 Start Interview"):
            st.session_state.role = role_input 
            st.session_state.round_type = round_type_input
            st.session_state.questions = generate_questions(role_input, round_type_input)[:5]
            n = len(st.session_state.questions)
            st.session_state.started = True
            st.session_state.current_q = 0
            st.session_state.answers = [""]*n
            st.session_state.feedbacks = [""]*n
            st.session_state.scores = [0]*n
            st.rerun()



if st.session_state.started and not st.session_state.completed:

    i = st.session_state.current_q
    total = len(st.session_state.questions)

    # Safe progress (reaches 100% at last question)
    progress = (i + 1) / total
    st.progress(progress)

    # Show question nicely
    st.subheader(f"Question {i + 1} of {total}")
    st.info(st.session_state.questions[i])

    # Ensure answers list exists
    if "answers" not in st.session_state:
        st.session_state.answers = [""] * total

    with st.form(f"q_{i}", clear_on_submit=True):
        ans = st.text_area("Your Answer", height=160)

        submitted = st.form_submit_button("Submit Answer")

        if submitted and ans.strip():
            r = get_scores(st.session_state.questions[i], ans)

            st.session_state.answers[i] = ans
            st.session_state.scores[i] = r["score"]
            st.session_state.feedbacks[i] = r["feedback"]

            st.session_state.current_q += 1

            if st.session_state.current_q >= total:
                st.session_state.completed = True

            st.rerun()


if st.session_state.completed:

    st.success("🎉 Interview Completed!")

    role = st.session_state.get("role", "Unknown Role")
    round_type = st.session_state.get("round_type", "Unknown Round")

    scores = st.session_state.get("scores", [])
    questions = st.session_state.get("questions", [])
    answers = st.session_state.get("answers", [])
    feedbacks = st.session_state.get("feedbacks", [])

    total = len(scores)

    if total == 0:
        st.warning("No interview data available.")
        st.stop()

    # ---------------- CHART ----------------
    df = pd.DataFrame({
        "Question": [f"Q{i+1}" for i in range(total)],
        "Score": scores
    })

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("Question:O", title="Questions"),
            y=alt.Y("Score:Q", scale=alt.Scale(domain=[0, 10]), title="Score"),
            tooltip=["Question", "Score"]
        )
        .properties(height=320)
    )

    st.altair_chart(chart, use_container_width=True)

    # ---------------- SUMMARY ----------------
    avg_score = round(sum(scores) / total, 2)

    if avg_score >= 8:
        verdict = "🌟 Excellent! Interview ready."
    elif avg_score >= 5:
        verdict = "👍 Good, but needs more practice."
    else:
        verdict = "⚠️ Needs significant improvement."

    st.info(f"""
**📌 Performance Summary**

- **Average Score:** {avg_score} / 10  
- **Total Questions:** {total}  
- **Overall Verdict:** {verdict}
""")

    # ---------------- DETAILED FEEDBACK ----------------
    st.markdown("### 📝 Detailed Feedback")

    for i in range(total):
        st.markdown(f"""
**Q{i+1}:** {questions[i]}

**Your Answer:**  
{answers[i]}

**Feedback:**  
{feedbacks[i]}

**Score:** {scores[i]} / 10
---
""")

    # ---------------- PDF ----------------
    if st.button("📄 Generate PDF Report"):
        pdf_path = generate_pdf(
            role,
            round_type,
            questions,
            answers,
            feedbacks,
            scores,
            avg_score
        )

        with open(pdf_path, "rb") as f:
            st.download_button(
                "⬇️ Download PDF",
                f,
                file_name="Interview_Report.pdf"
            )
