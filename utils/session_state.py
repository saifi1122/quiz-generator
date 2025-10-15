# app/utils/session_state.py

def initialize_session_state():
    """
    Initialize the session state keys used by the app.
    This preserves the exact keys & default values you used originally.
    Call this at start of streamlit_app.py
    """
    import streamlit as st

    keys_defaults = {
        "questions": [],
        "user_answers": [],
        "correct_answers": [],
        "score": None,
        "generated": False,
        "topic_for_quiz": "",
        "show_level_selection": False,
        "selected_level": "",
        "history": [],
        "quiz_submitted": False,
        "show_feedback_button": False,
        "mcqs_text": ""
    }

    for k, v in keys_defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
