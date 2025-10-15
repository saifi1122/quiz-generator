# app/ui/history_ui.py
import streamlit as st

def show_history_panel(st):
    """Render left column history panel using st.session_state.history"""
    st.header(" History")
    if "history" in st.session_state and st.session_state.history:
        # show latest first for better UX
        for h in reversed(st.session_state.history[-30:]):
            st.write(h)
    else:
        st.write("No history yet...")
