import streamlit as st
import pandas as pd
import altair as alt

from backend import (
    generate_questions,
    evaluate_answer,
    final_feedback,
    get_scores
)
from pdf_utils import generate_pdf


st.set_page_config(
    page_title="AI Interview Coach",
    layout="centered"
)

st.title("🤖 AI Interview Coach")


st.sidebar.title("Interview Coach")
st.sidebar.write("Practice smart, succeed faster")

st.sidebar.markdown("---")
st.sidebar.subheader("💡 Viva Questions")

st.sidebar.markdown("""
**What is an AI Interview Coach?**  
An AI Interview Coach is an intelligent system that simulates real interview scenarios,
asks role-based questions, evaluates answers, and provides feedback to help candidates
improve their interview performance.

**Why is Streamlit used?**  
Streamlit is used because it enables rapid development of interactive web applications
using only Python, without requiring frontend technologies.

**Where does AI run – locally or online?**  
AI can run locally for lightweight models or online using cloud-based APIs for powerful
language models, depending on the system design.
""")


# Professional Dark Styling

st.markdown("""
<style>
.stApp {
    background-color: #0B0B0B;
    color: #E5E5E5;
}
header {
    background-color: #0B0B0B !important;
    border-bottom: 1px solid #2A2A2A;
}
h1, h2, h3, h4 {
    color: #E5E5E5;
    font-weight: 600;
}
label {
    color: #B0B0B0 !important;
}
input, textarea, select {
    background-color: #1A1A1A !important;
    color: #E5E5E5 !important;
    border: 1px solid #333 !important;
    border-radius: 6px;
}
.stButton > button {
    background-color: #2A2A2A;
    color: #E5E5E5;
    border: 1px solid #444;
    border-radius: 8px;
    padding: 8px 18px;
}
.stButton > button:hover {
    background-color: #3A3A3A;
    border-color: #666;
}
.stProgress > div > div {
    background-color: #666 !important;
}
.stAlert {
    background-color: #1A1A1A !important;
    color: #E5E5E5 !important;
    border-left: 4px solid #666 !important;
}
.card {
    background-color: #1A1A1A;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #333;
    margin-bottom: 20px;
}
.question-box {
    background-color: #1A1A1A;
    padding: 18px;
    border-radius: 10px;
    border-left: 4px solid #555;
    margin-bottom: 14px;
}
.feedback-box {
    background-color: #121212;
    padding: 15px;
    border-radius: 8px;
    border-left: 4px solid #444;
}
svg text {
    fill: #E5E5E5 !important;
}
.block-container {
    padding-top: 2rem;
}
</style>
""", unsafe_allow_html=True)



# Session State Initialization

if "questions" not in st.session_state:
    st.session_state.questions = []
    st.session_state.current_q = 0
    st.session_state.started = False
    st.session_state.completed = False
    st.session_state.answers = []
    st.session_state.feedbacks = []



# Interview Setup (Task 1)

role = st.selectbox(
    "Select Job Role",
    ["Software Developer", "Data Analyst", "ML Engineer"]
)

round_type = st.selectbox(
    "Select Interview Round",
    ["Technical", "Behavioral", "HR"]
)



# Start Interview

if st.button("Start Interview", key="start"):
    with st.spinner("Generating interview questions..."):
        try:
            st.session_state.questions = generate_questions(role, round_type)
            st.session_state.current_q = 0
            st.session_state.started = True
            st.session_state.completed = False
            st.session_state.answers = []
            st.session_state.feedbacks = []
            st.success("Interview started successfully!")
        except Exception as e:
            st.error(str(e))



# Interview Flow

if st.session_state.started and not st.session_state.completed:
    q_index = st.session_state.current_q
    total = len(st.session_state.questions)

    if q_index < total:
        st.progress((q_index + 1) / total)

        st.markdown(f"### ❓ Question {q_index + 1} of {total}")
        st.markdown(
            f"<div class='question-box'>{st.session_state.questions[q_index]}</div>",
            unsafe_allow_html=True
        )

        answer = st.text_area(
            "Your Answer",
            height=120,
            key=f"answer_{q_index}"
        )

        if st.button("Submit Answer", key=f"submit_{q_index}"):
            if not answer.strip():
                st.warning("Please enter your answer.")
            else:
                with st.spinner("Evaluating answer..."):
                    feedback = evaluate_answer(
                        st.session_state.questions[q_index],
                        answer
                    )

                st.session_state.answers.append(answer)
                st.session_state.feedbacks.append(feedback)

                scores = get_scores()
                st.info(f"Score for this answer: {scores[-1]} / 10")

                st.markdown("#### 💡 Feedback")
                st.markdown(
                    f"<div class='feedback-box'>{feedback}</div>",
                    unsafe_allow_html=True
                )

                st.session_state.current_q += 1
                st.rerun()
    else:
        st.session_state.completed = True
        st.rerun()



# Final Feedback & Analytics

if st.session_state.completed:
    st.success("Interview completed.")

    st.markdown("## 📊 Final Feedback")
    st.write(final_feedback())

    scores = get_scores()
    df = pd.DataFrame({
        "Question": [f"Q{i+1}" for i in range(len(scores))],
        "Score": scores
    })

    st.markdown("<div class='card'><h3>📈 Score Visualization</h3>", unsafe_allow_html=True)

    chart = (
        alt.Chart(df)
        .mark_bar(color="#777777")
        .encode(
            x=alt.X("Question:N", title="Question"),
            y=alt.Y("Score:Q", scale=alt.Scale(domain=[0, 10]), title="Score"),
            tooltip=["Question", "Score"]
        )
        .properties(height=300)
    )

    st.altair_chart(chart, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'><h3>📄 Download Interview Report</h3>", unsafe_allow_html=True)

    if st.button("Generate PDF Report"):
        pdf_file = generate_pdf(
            role=role,
            round_type=round_type,
            questions=st.session_state.questions,
            answers=st.session_state.answers,
            feedbacks=st.session_state.feedbacks,
            scores=scores
        )

        with open(pdf_file, "rb") as f:
            st.download_button(
                label="Download PDF",
                data=f,
                file_name=pdf_file,
                mime="application/pdf"
            )

    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Restart Interview", key="restart"):
        st.session_state.clear()
        st.rerun()
