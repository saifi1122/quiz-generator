# app/ui/quiz_ui.py
import streamlit as st
import re
from datetime import datetime

# Helper function for rerun (compatible with old and new Streamlit versions)
def safe_rerun():
    """Use st.rerun() if available, otherwise st.experimental_rerun()"""
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()


def parse_mcqs(mcqs_text):
    """Parse raw MCQs text into structured questions with options."""
    blocks = [b.strip() for b in re.split(r'\n\s*\n', mcqs_text) if b.strip()]
    parsed = []
    for block in blocks:
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        opt_start_idx = None
        for i, ln in enumerate(lines):
            if re.match(r'^[abcd]\)', ln.lower()):
                opt_start_idx = i
                break
        if opt_start_idx is None:
            q_text = lines[0]
            opts = lines[1:5]
        else:
            q_text = " ".join(lines[:opt_start_idx]).strip()
            opts = lines[opt_start_idx:opt_start_idx+4]
        opts_clean = []
        for o in opts:
            if re.match(r'^[abcd]\)', o.lower()):
                opts_clean.append(o)
            else:
                m = re.match(r'^[abcd]\)\s*(.*)', o, re.I)
                if m:
                    opts_clean.append(f"{o[0]}) {m.group(1)}")
                else:
                    opts_clean.append(o)
        while len(opts_clean) < 4:
            opts_clean.append("a) [missing option]")
        parsed.append({"question": q_text, "options": opts_clean})
    return parsed[:10]


def show_quiz_panel(
    st,
    generate_mcqs_fn,
    parse_mcqs_fn,
    explainer_llm,
    get_correct_answers_fn,
    save_result_fn
):
    """Main quiz panel: generation, display, submission, results."""

    # ====== Initialize session state ======
    defaults = {
        "history": [],
        "quiz_submitted": False,
        "show_feedback_button": False,
        "generated": False,
        "show_level_selection": False,
        "selected_level": "",
        "questions": [],
        "user_answers": [],
        "score": None,
        "mcqs_text": "",
        "correct_answers": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ========================================================================
    # STEP 1: If quiz is submitted, ONLY show results and STOP
    # ========================================================================
    if st.session_state.quiz_submitted:
        st.markdown("---")
        st.header(f"✅ Quiz Results - {st.session_state.selected_level.title()} Level")
        st.write(f"**Topic:** {st.session_state.get('topic_for_quiz', 'N/A')}")
        
        # Score display
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Your Score", value=f"{st.session_state.score}/{len(st.session_state.questions)}")
        with col2:
            percentage = (st.session_state.score / len(st.session_state.questions)) * 100
            st.metric(label="Percentage", value=f"{percentage:.1f}%")
        
        st.info(f"📅 Date: {datetime.now().strftime('%d %B %Y, %I:%M %p')}")

        st.markdown("---")
        st.markdown("### 📊 Detailed Results")
        
        for i, q in enumerate(st.session_state.questions):
            user = st.session_state.user_answers[i]
            corr = st.session_state.correct_answers[i]
            
            if user == corr:
                st.success(f"✓ **Question {i+1}** - Correct")
            else:
                st.error(f"✗ **Question {i+1}** - Incorrect")
            
            st.write(f"**{q['question']}**")
            st.write(f"👤 Your answer: **{user.upper()})**")
            st.write(f"✅ Correct answer: **{corr.upper()})**")
            
            for opt in q['options']:
                if opt.lower().startswith(corr + ')'):
                    st.write(f"📝 Correct option: {opt}")
                    break
            
            st.markdown("---")

        # Feedback button
        if st.session_state.show_feedback_button:
            if st.button("💬 Give Feedback", use_container_width=True):
                st.info("📝 Feedback functionality coming soon!")

        st.markdown("---")
        if st.button("🔄 Generate New Quiz", type="primary", use_container_width=True):
            # Reset all states
            for key in ["generated", "quiz_submitted", "show_level_selection", "show_feedback_button", 
                       "selected_level", "questions", "user_answers", "score", "mcqs_text", "correct_answers"]:
                if key in ["generated", "quiz_submitted", "show_level_selection", "show_feedback_button"]:
                    st.session_state[key] = False
                elif key in ["questions", "user_answers", "correct_answers"]:
                    st.session_state[key] = []
                else:
                    st.session_state[key] = "" if key == "selected_level" or key == "mcqs_text" else None
            safe_rerun()
        
        # ⭐ CRITICAL: Return here to prevent showing quiz below
        return

    # ========================================================================
    # STEP 2: Generate Quiz Button (only if not generated yet)
    # ========================================================================
    if st.session_state.get("topic_for_quiz") and not st.session_state.show_level_selection and not st.session_state.generated:
        if st.button("📝 Generate Quiz", type="primary"):
            st.session_state.show_level_selection = True
            safe_rerun()

    # ========================================================================
    # STEP 3: Level Selection
    # ========================================================================
    if st.session_state.show_level_selection and not st.session_state.generated:
        st.markdown("---")
        st.subheader("🎯 Select Difficulty Level")
        st.write(f"**Topic:** {st.session_state['topic_for_quiz']}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### 🟢 Beginner")
            st.write("Basic concepts")
            if st.button("Select Beginner", key="btn_beginner", use_container_width=True):
                st.session_state.selected_level = "beginner"
                safe_rerun()
        with col2:
            st.markdown("### 🟡 Intermediate")
            st.write("Moderate difficulty")
            if st.button("Select Intermediate", key="btn_intermediate", use_container_width=True):
                st.session_state.selected_level = "intermediate"
                safe_rerun()
        with col3:
            st.markdown("### 🔴 Advanced")
            st.write("Expert level")
            if st.button("Select Advanced", key="btn_advanced", use_container_width=True):
                st.session_state.selected_level = "advanced"
                safe_rerun()

    # ========================================================================
    # STEP 4: Generate Quiz
    # ========================================================================
    if st.session_state.selected_level and not st.session_state.generated:
        level = st.session_state.selected_level
        
        with st.spinner(f"🔄 Generating {level.title()} level quiz... Please wait."):
            try:
                mcqs_text = generate_mcqs_fn(st.session_state["topic_for_quiz"], level)
                st.session_state.mcqs_text = mcqs_text
                st.session_state.questions = parse_mcqs_fn(mcqs_text)
                st.session_state.user_answers = [""] * len(st.session_state.questions)
                st.session_state.correct_answers = []
                st.session_state.score = None
                st.session_state.quiz_submitted = False
                st.session_state.generated = True
                st.session_state.show_level_selection = False
                st.success(f"✅ {level.title()} level quiz generated! Scroll down to answer.")
                st.session_state.history.append(f"🤖 Quiz generated ({level.title()} level)")
                safe_rerun()
            except Exception as e:
                st.error(f"❌ Failed to generate quiz: {e}")
                st.session_state.selected_level = ""
                return

    # ========================================================================
    # STEP 5: Show Quiz (Only if generated and NOT submitted)
    # ========================================================================
    if st.session_state.generated and st.session_state.questions and not st.session_state.quiz_submitted:
        st.markdown("---")
        st.header(f"📝 Quiz - {st.session_state.selected_level.title()} Level")
        st.write(f"**Topic:** {st.session_state['topic_for_quiz']}")
        st.info(f"📊 Total Questions: {len(st.session_state.questions)}")

        # ====== Quiz Form ======
        with st.form(key="quiz_form"):
            st.markdown("### 📋 Answer all questions below:")
            
            temp_answers = []
            
            for i, q in enumerate(st.session_state.questions):
                st.markdown(f"#### Question {i+1}")
                st.write(f"**{q['question']}**")
                
                choice = st.radio(
                    f"Select your answer:",
                    q["options"],
                    key=f"q{i}",
                    label_visibility="collapsed"
                )
                
                m = re.match(r'^\s*([abcd])\)', choice.lower())
                if m:
                    temp_answers.append(m.group(1))
                else:
                    try:
                        idx = q["options"].index(choice)
                        temp_answers.append(["a","b","c","d"][idx])
                    except:
                        temp_answers.append("")
                
                st.markdown("---")

            submit_btn = st.form_submit_button("✅ Submit Answers", type="primary", use_container_width=True)

        # ====== Handle Submission ======
        if submit_btn:
            st.session_state.user_answers = temp_answers
            
            if not all(ans in ["a","b","c","d"] for ans in st.session_state.user_answers):
                st.warning("⚠️ Please answer all questions before submitting.")
            else:
                with st.spinner("🔄 Evaluating your answers..."):
                    try:
                        correct = get_correct_answers_fn(explainer_llm, st.session_state.mcqs_text)
                        st.session_state.correct_answers = correct[:len(st.session_state.questions)]
                        
                        st.session_state.score = sum(
                            1 for u, c in zip(st.session_state.user_answers, st.session_state.correct_answers) 
                            if u == c
                        )
                        
                        total_q = len(st.session_state.questions)
                        
                        save_result_fn(
                            st.session_state.score, 
                            total_q - st.session_state.score,
                            st.session_state.score, 
                            total_q,
                            st.session_state.score / total_q * 100
                        )
                        
                        # ⭐ Set flag and reload
                        st.session_state.quiz_submitted = True
                        st.session_state.show_feedback_button = True
                        st.session_state.history.append(
                            f"👤 Quiz submitted. Score: {st.session_state.score}/{total_q}"
                        )
                        
                        safe_rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error evaluating quiz: {e}")
                        st.write("Error details:", str(e))