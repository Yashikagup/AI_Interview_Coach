import streamlit as st
import pandas as pd
import altair as alt
from auth import signup, login
from backend import generate_questions, evaluate_answer, final_feedback, get_scores
from pdf_utils import generate_pdf

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "questions" not in st.session_state:
    st.session_state.questions = []
    st.session_state.current_q = 0
    st.session_state.started = False
    st.session_state.completed = False
    st.session_state.answers = []
    st.session_state.feedbacks = []
    st.session_state.current_answer = ""
    st.session_state.scores = []

if not st.session_state.logged_in:
    st.set_page_config(page_title="AI Interview Coach - Login")
    st.title("AI Interview Coach")
    choice = st.selectbox("Choose Option", ["Login", "Sign Up"])
    username = st.text_input("Username", placeholder="Username")
    password = st.text_input("Password", type="password", placeholder="Enter Password")
    if choice == "Sign Up":
        if st.button("Create Account"):
            if signup(username, password):
                st.success(" Account created! Please login")
            else:
                st.error(" Username already exists")
    if choice == "Login":
        if st.button("Login"):
            if login(username, password):
                st.success("🎉 Login successful")
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error(" Invalid credentials")

else:
    st.set_page_config(page_title="AI Interview Coach", layout="centered")
    st.title("🤖 AI Interview Coach")

    with st.sidebar:
        st.header("📄 Upload Resume")
        uploaded_file = st.file_uploader("Choose your resume (PDF only)", type=["pdf"])
        if uploaded_file is not None:
            st.success("✅ Resume uploaded successfully!")
            with open(f"uploaded_{uploaded_file.name}", "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.info(f"Saved as uploaded_{uploaded_file.name}")
        st.markdown("---")
        st.header("🔹 User Actions")
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

    st.markdown("""
<style>
.stApp { background-color: #f8fafc; }
.login-card { background-color: gray; padding: 30px; border-radius: 15px; width: 350px; margin: auto; margin-top: 120px; box-shadow: 0px 15px 30px rgba(0,0,0,0.45); }
input { background-color: #f8fafc !important; color: black !important; }
input::placeholder { color: gray !important; }
button { width: 100%; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

    role = st.text_input("Enter Job Role (optional)", value="Software Engineer")
    round_type = st.selectbox("Select Interview Round", ["Technical", "Behavioral", "HR"])

    if st.button("Start Interview"):
        st.session_state.questions = generate_questions(role, round_type)
        st.session_state.started = True
        st.session_state.completed = False
        st.session_state.current_q = 0
        st.session_state.answers = []
        st.session_state.feedbacks = []
        st.session_state.current_answer = ""
        st.session_state.scores = []
        st.success("✅ Interview Started")

    if st.session_state.started and not st.session_state.completed:
        if st.session_state.questions:
            total = len(st.session_state.questions)
            idx = st.session_state.current_q
            if idx < total:
                st.progress((idx + 1)/total)
                st.markdown(f"### Question {idx+1}/{total}")
                st.markdown(f"<div class='question-box'>{st.session_state.questions[idx]}</div>", unsafe_allow_html=True)
                if "current_answer" not in st.session_state:
                    st.session_state.current_answer = ""
                with st.form(key=f"form_{idx}"):
                    answer = st.text_area("Your Answer", value=st.session_state.current_answer, height=120)
                    submit = st.form_submit_button("Submit Answer")
                if submit:
                    if answer.strip() != "":
                        result = evaluate_answer(st.session_state.questions[idx], answer)
                        score = result.get("score", 0)
                        fb = result.get("feedback", "No feedback provided.")
                        st.session_state.answers.append(answer)
                        st.session_state.feedbacks.append(fb)
                        st.session_state.scores.append(score)
                        st.session_state.current_q += 1
                        st.session_state.current_answer = ""
                        st.rerun()
                    else:
                        st.warning("⚠️ Please enter an answer before submitting")
                st.session_state.current_answer = answer
            else:
                st.session_state.completed = True
                st.rerun()
        else:
            st.info("No questions available. Please start the interview first.")

    if st.session_state.completed:
     st.success("✅ Interview Completed")

    if st.session_state.scores:
        st.subheader("Final Feedback")
        feedback_text = final_feedback().replace("\n", "<br>")
        st.markdown(feedback_text, unsafe_allow_html=True)

        df = pd.DataFrame({
            "Question": [f"Q{i+1}" for i in range(len(st.session_state.scores))],
            "Score": st.session_state.scores
        })

        chart = alt.Chart(df).mark_bar(color="#888").encode(
            x="Question:N",
            y=alt.Y("Score:Q", scale=alt.Scale(domain=[0,10])),
            tooltip=["Question","Score"]
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)

        st.markdown("<div class='card'><h3>📄 Download Interview Report</h3></div>", unsafe_allow_html=True)
        if st.button("Generate PDF"):
            pdf = generate_pdf(
                role, round_type,
                st.session_state.questions,
                st.session_state.answers,
                st.session_state.feedbacks,
                st.session_state.scores
            )
            with open(pdf, "rb") as f:
                st.download_button("Download PDF", f, file_name="Interview_Report.pdf")
    else:
        st.info("No answers submitted. Start the interview to see feedback and scores.")
