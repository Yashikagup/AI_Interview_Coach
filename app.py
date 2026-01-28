import streamlit as st
import pandas as pd
import altair as alt

from auth import signup, login
from backend import (
    generate_questions,
    generate_questions_from_resume,
    get_scores,
    final_feedback,
)
from pdf_utils import generate_pdf

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="AI Interview Coach", layout="centered")

# ---------- SESSION STATE ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "questions" not in st.session_state:
    st.session_state.questions = []
    st.session_state.current_q = 0
    st.session_state.started = False
    st.session_state.completed = False
    st.session_state.answers = []
    st.session_state.feedbacks = []
    st.session_state.scores = []

st.markdown("""
<style>
/* ---------- Main Background ---------- */
[data-testid="stAppViewContainer"] {
    background-color: #f5f5f5;
    color: #333333;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    padding: 30px;
}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
    background-color: #ffffff;
    color: #333333;
    padding: 20px;
}
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] label {
    color: #333333;
}

/* ---------- Cards / Sections ---------- */
.card {
    background-color: #ffffff;
    color: #333333;
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}

/* ---------- Question Box ---------- */
.question-box {
    background-color: #ffffff;
    color: #333333;
    border-left: 4px solid #4a90e2;
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 20px;
    font-weight: 500;
    font-size: 15px;
}

/* ---------- Buttons ---------- */
.stButton>button {
    background-color: #4a90e2 !important;
    color: #ffffff !important;
    font-weight: 500;
    border-radius: 10px !important;
    height: 42px !important;
    width: 100% !important;
    border: 1px solid #357ABD !important;
    cursor: pointer;
    transition: all 0.2s ease;
}
.stButton>button:hover {
    background-color: #357ABD !important;
    transform: scale(1.03);
}

/* ---------- Inputs / TextArea ---------- */
.stTextInput>div>div>input,
.stTextArea>div>div>textarea {
    background-color: #fefefe !important;
    color: #333333 !important;
    border: 1px solid #dcdcdc !important;
    border-radius: 10px !important;
    padding: 10px !important;
    font-size: 15px;
}

/* ---------- SelectBox ---------- */
.css-1hwfws3, .css-1cpxqw2 {
    background-color: #fefefe !important;
    color: #333333 !important;
    border-radius: 10px !important;
}

/* ---------- File Uploader ---------- */
.stFileUpload>div {
    background-color: #fefefe !important;
    color: #333333 !important;
    border: 1px solid #dcdcdc !important;
    border-radius: 10px !important;
    padding: 10px !important;
}
.stFileUpload>div>label {
    color: #333333 !important;
}

/* ---------- Headings ---------- */
h1, h2, h3, h4, h5, h6 {
    color: #333333;
}

/* ---------- Links ---------- */
a {
    color: #4a90e2;
    text-decoration: none;
}
a:hover {
    text-decoration: underline;
}

/* ---------- Tooltips ---------- */
.vega-tooltip {
    background-color: #ffffff !important;
    color: #333333 !important;
    border: 1px solid #dcdcdc !important;
    font-size: 14px !important;
}

/* ---------- Scrollbars ---------- */
::-webkit-scrollbar {
    width: 8px;
}
::-webkit-scrollbar-track {
    background: #f5f5f5;
}
::-webkit-scrollbar-thumb {
    background: #4a90e2;
    border-radius: 4px;
}
 
</style>
""", unsafe_allow_html=True)









# ---------- LOGIN / SIGNUP ----------
if not st.session_state.logged_in:
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    st.markdown("## Welcome to AI Interview Coach")
    st.markdown("### Practice Interviews, Improve Skills")

    choice = st.selectbox("Choose Option", ["Login", "Sign Up"])
    username = st.text_input("Username", placeholder="Enter Your Name")
    password = st.text_input("Password", type="password", placeholder="Enter Password")

    if choice == "Sign Up" and st.button("Create Account"):
        if signup(username, password):
            st.success("Account created! Please login.")
        else:
            st.error("Username already exists")
    elif choice == "Login" and st.button("Login"):
        if login(username, password):
            st.success("Login successful")
            st.session_state.logged_in = True
        else:
            st.error("Invalid credentials")

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()  # Stop here until login

# ---------- MAIN APP ----------
st.markdown("<div class='interview-box'>", unsafe_allow_html=True)
st.title("AI Interview Coach")

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("Resume Upload")
    uploaded_file = st.file_uploader("Choose JPG/PNG Resume", type=["jpg", "png"])
    if uploaded_file is not None:
        file_path = f"uploaded_{uploaded_file.name}"
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("Resume uploaded successfully")

        if st.button("Generate Questions from Resume"):
            st.session_state.questions = generate_questions_from_resume(file_path)[:5]
            st.session_state.started = True
            st.session_state.completed = False
            st.session_state.current_q = 0
            st.session_state.answers = [""] * len(st.session_state.questions)
            st.session_state.feedbacks = [""] * len(st.session_state.questions)
            st.session_state.scores = [0] * len(st.session_state.questions)

    st.markdown("---")
    st.header("Actions")
    if st.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()

# ---------- INTERVIEW SETUP ----------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("Interview Setup")
role = st.text_input("Job Role", value="Software Engineer")
round_type = st.selectbox("Interview Round", ["Technical", "Behavioral", "HR"])
if st.button("Start Interview"):
    if role.strip():
        st.session_state.questions = generate_questions(role, round_type)[:5]
        st.session_state.started = True
        st.session_state.completed = False
        st.session_state.current_q = 0
        st.session_state.answers = [""] * len(st.session_state.questions)
        st.session_state.feedbacks = [""] * len(st.session_state.questions)
        st.session_state.scores = [0] * len(st.session_state.questions)
    else:
        st.warning("Please enter a Job Role")
st.markdown('</div>', unsafe_allow_html=True)


# ---------- INTERVIEW FLOW ----------
if st.session_state.started and not st.session_state.completed:
    idx = st.session_state.current_q
    total = len(st.session_state.questions)
    
    # Calculate percentage
    progress_percent = int((idx / total) * 100)
    
    # Show percentage above progress bar
    st.markdown(f"**Progress: {progress_percent}% completed**")
    st.progress(progress_percent / 100)

    if idx < total:
        st.markdown(
            f"<div class='question-box fade-in'>{st.session_state.questions[idx]}</div>",
            unsafe_allow_html=True
        )

        with st.form(key=f"form_{idx}"):
            answer = st.text_area(
                "Your Answer",
                value=st.session_state.answers[idx],
                height=120
            )
            submit = st.form_submit_button("Submit Answer")

            if submit:
                if answer.strip():
                    # Save answer
                    st.session_state.answers[idx] = answer

                    # Evaluate answer
                    result = get_scores(st.session_state.questions[idx], answer)
                    st.session_state.scores[idx] = result.get("score", 0)
                    st.session_state.feedbacks[idx] = result.get("feedback", "")

                    # Move to next question
                    st.session_state.current_q += 1
                else:
                    st.warning("Please type your answer")
    else:
        st.session_state.completed = True

# ---------- COMPLETION & REPORT ----------
if st.session_state.completed:
    st.success("Interview Completed")

    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Final Feedback")
    feedback_text = final_feedback().replace("\n", "<br>")
    st.markdown(feedback_text, unsafe_allow_html=True)

    df = pd.DataFrame({
        "Question": [f"Q{i+1}" for i in range(len(st.session_state.questions))],
        "Score": st.session_state.scores
    })

    chart = alt.Chart(df).mark_bar().encode(
        x="Question:N",
        y=alt.Y("Score:Q", scale=alt.Scale(domain=[0, 10])),
        tooltip=["Question", "Score"]
    ).properties(height=320)

    st.altair_chart(chart, use_container_width=True)

    if st.button("Generate PDF"):
        pdf = generate_pdf(
            role,
            round_type,
            st.session_state.questions,
            st.session_state.answers,
            st.session_state.feedbacks,
            st.session_state.scores
        )
        with open(pdf, "rb") as f:
            st.download_button("Download PDF", f, file_name="Interview_Report.pdf")
    st.markdown('</div>', unsafe_allow_html=True)
