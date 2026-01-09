import tkinter as tk
from tkinter import messagebox, scrolledtext

from backend import generate_questions, evaluate_answer, final_feedback


class AIInterviewCoachApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Interview Coach")
        self.root.geometry("760x650")
        self.root.resizable(False, False)

        tk.Label(root, text="AI Interview Coach", font=("Arial", 18, "bold")).pack(pady=10)

        tk.Label(root, text="Enter Job Role:", font=("Arial", 12)).pack()
        self.role_entry = tk.Entry(root, width=40, font=("Arial", 12))
        self.role_entry.pack(pady=5)

        self.progress_label = tk.Label(root, text="Progress: 0 / 5", font=("Arial", 10))
        self.progress_label.pack(pady=3)

        self.chat_box = scrolledtext.ScrolledText(root, width=90, height=20)
        self.chat_box.pack(pady=10)
        self.chat_box.insert(tk.END, "👋 Welcome!\nEnter a job role and click 'Start Interview'\n")

        tk.Label(root, text="Your Answer:", font=("Arial", 12)).pack()
        self.answer_box = scrolledtext.ScrolledText(root, width=90, height=4)
        self.answer_box.pack(pady=5)

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)

        self.start_btn = tk.Button(btn_frame, text="Start Interview", command=self.start_interview)
        self.start_btn.pack(side="left", padx=10)

        self.submit_btn = tk.Button(btn_frame, text="Submit Answer",
                                    command=self.submit_answer, state=tk.DISABLED)
        self.submit_btn.pack(side="left", padx=10)

        self.questions = []
        self.current_q = 0
        self.in_session = False

    def start_interview(self):
        role = self.role_entry.get().strip()
        if not role:
            messagebox.showwarning("Input Required", "Please enter a job role.")
            return

        self.chat_box.insert(tk.END, f"\n🤖 Generating questions for {role}...\n")

        try:
            self.questions = generate_questions(role)
            self.current_q = 0
            self.in_session = True
            self.submit_btn.config(state=tk.NORMAL)
            self.start_btn.config(state=tk.DISABLED)
            self.ask_next_question()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def ask_next_question(self):
        if self.current_q < len(self.questions):
            self.progress_label.config(text=f"Progress: {self.current_q + 1} / 5")
            self.chat_box.insert(tk.END, f"\nQ{self.current_q + 1}: {self.questions[self.current_q]}\n")
        else:
            self.finish_interview()

    def submit_answer(self):
        answer = self.answer_box.get("1.0", tk.END).strip()
        if not answer:
            messagebox.showwarning("Input Required", "Please enter your answer.")
            return

        question = self.questions[self.current_q]
        self.chat_box.insert(tk.END, f"🧑 Your Answer: {answer}\n")
        self.answer_box.delete("1.0", tk.END)

        feedback = evaluate_answer(question, answer)
        self.chat_box.insert(tk.END, f"💡 Feedback:\n{feedback}\n")

        self.current_q += 1
        self.ask_next_question()

    def finish_interview(self):
        self.in_session = False
        self.submit_btn.config(state=tk.DISABLED)
        self.start_btn.config(state=tk.NORMAL)
        self.progress_label.config(text="Progress: Completed")

        summary = final_feedback()
        self.chat_box.insert(tk.END, f"\n🎉 INTERVIEW COMPLETED\n📊 FINAL FEEDBACK:\n{summary}\n")


if __name__ == "__main__":
    root = tk.Tk()
    app = AIInterviewCoachApp(root)
    root.mainloop()
