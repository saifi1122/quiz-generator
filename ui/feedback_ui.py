# app/ui/feedback_ui.py
import streamlit as st

def show_feedback_panel(st, create_feedback_agent_fn=None, feedback_llm=None):
    """
    Show feedback button and handle feedback generation.
    create_feedback_agent_fn and feedback_llm are injected from main to preserve same behavior.
    """
    if "show_feedback_button" in st.session_state and st.session_state.show_feedback_button:
        if st.button("Get Feedback", use_container_width=True):
            score = st.session_state.score
            total_q = len(st.session_state.questions) if st.session_state.questions else 0
            topic = st.session_state.topic_for_quiz
            percentage = (score / total_q) * 100 if total_q else 0

            initial_state = {
                "topic": topic,
                "score": score,
                "total_q": total_q,
                "percentage": percentage,
                "output": ""
            }

            try:
                feedback_agent = create_feedback_agent_fn(feedback_llm)
                compiled_agent = feedback_agent.compile()
                result = compiled_agent.invoke(initial_state)
                feedback_text = result.get("output", "No feedback generated.")
            except Exception as e:
                feedback_text = f"Failed to generate feedback: {e}"

            st.markdown("###  Overall Feedback")
            st.info(feedback_text)
            st.session_state.history.append(f" Feedback: {feedback_text}")
            st.session_state.show_feedback_button = False
