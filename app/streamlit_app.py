# app/streamlit_app.py
import streamlit as st
import sys
import os
from datetime import datetime
import pandas as pd

# Add parent directory so imports for sibling folders work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ====== Database & Agents ======
from app.database import create_table, save_result, fetch_results
from agents.explainer_agent import create_topic_explainer_agent, llm as explainer_llm
from agents.quiz_generator import generate_mcqs
from tests.result_checker import get_correct_answers_from_llm
from agents.feedback_agent import create_feedback_agent, llm as feedback_llm

# ====== UI Modules ======
from ui.history_ui import show_history_panel
from ui.quiz_ui import show_quiz_panel, parse_mcqs
from ui.feedback_ui import show_feedback_panel
from utils.session_state import initialize_session_state

# ====== Initialize Database ======
create_table()

# ====== Streamlit Page Config ======
st.set_page_config(page_title="Study Assistant", layout="wide")
st.title("📚 Study Assistant")

# ====== Initialize Session State ======
initialize_session_state()

# ====== Progress Report Section ======
st.markdown("---")
st.header("📊 Your Progress Report")
if st.button("View Progress"):
    results = fetch_results()
    if results:
        df = pd.DataFrame(results, columns=[
            "Correct", "Incorrect", "Marks Obtained", "Total Marks", "Percentage", "Date"
        ])
        df["Percentage"] = df["Percentage"].map("{:.0f}%".format)
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%d %b %Y")
        st.table(df)
    else:
        st.info("No quiz results found. Take some quizzes first!")

# ====== Layout: Left = History, Right = Main ======
left_col, right_col = st.columns([1, 2])

with left_col:
    show_history_panel(st)

with right_col:
    # ⭐ CRITICAL: Check if quiz is submitted - if yes, skip topic input
    if not st.session_state.get("quiz_submitted", False):
        # ====== Topic Input & Explanation ======
        st.header("💬 Main Chat & Quiz")

        user_topic = st.text_input("Enter your topic/query:", "")
        if st.button("Explain Topic") and user_topic.strip():
            with st.spinner("Generating explanation..."):
                initial_state = {
                    "topic": user_topic,
                    "user_query": user_topic,
                    "explanation": "",
                    "examples": [],
                    "summary": "",
                    "messages": []
                }
                explainer_agent = create_topic_explainer_agent(explainer_llm)
                result = explainer_agent.invoke(initial_state)

                st.subheader("📝 Explanation")
                st.write(result.get("explanation", "N/A"))

                st.subheader("💡 Examples")
                for ex in result.get("examples", []):
                    st.write(f"- {ex}")

                st.subheader("🗒 Summary")
                st.write(result.get("summary", "N/A"))

                st.session_state.topic_for_quiz = user_topic
                st.session_state.history.append(f"Topic entered: {user_topic}")
                st.session_state.history.append(f"Explanation generated")

    # ====== Quiz Panel - ALWAYS SHOW (it handles its own logic) ======
    show_quiz_panel(
        st,
        generate_mcqs_fn=generate_mcqs,
        parse_mcqs_fn=parse_mcqs,
        explainer_llm=explainer_llm,
        get_correct_answers_fn=get_correct_answers_from_llm,
        save_result_fn=save_result
    )

# ====== Feedback Panel ======
if not st.session_state.get("quiz_submitted", False):
    show_feedback_panel(
        st,
        create_feedback_agent_fn=create_feedback_agent,
        feedback_llm=feedback_llm
    )