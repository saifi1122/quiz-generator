from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from agents.explainer_agent import create_topic_explainer_agent, llm as explainer_llm
from agents.quiz_generator import generate_mcqs
from tests.result_checker import get_correct_answers_from_llm
from agents.feedback_agent import create_feedback_agent, llm as feedback_llm
from app.database import create_table, save_result, fetch_results

# Initialize database
create_table()

app = FastAPI(title="Study Assistant API")

# ------------------ Request Models ------------------
class TopicRequest(BaseModel):
    topic: str

class SubmitQuizRequest(BaseModel):
    topic: str
    level: str
    user_answers: List[str]

# ------------------ Endpoints ------------------

@app.post("/explain_topic")
def explain_topic(req: TopicRequest):
    try:
        initial_state = {
            "topic": req.topic,
            "user_query": req.topic,
            "explanation": "",
            "examples": [],
            "summary": "",
            "messages": []
        }
        agent = create_topic_explainer_agent(explainer_llm)
        result = agent.invoke(initial_state)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_quiz")
def generate_quiz(req: SubmitQuizRequest):
    try:
        mcqs_text = generate_mcqs(req.topic, req.level)
        return {"mcqs_text": mcqs_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/submit_quiz")
def submit_quiz(req: SubmitQuizRequest):
    try:
        mcqs_text = generate_mcqs(req.topic, req.level)
        correct_answers = get_correct_answers_from_llm(mcqs_text)[:len(req.user_answers)]
        
        score = sum(1 for u, c in zip(req.user_answers, correct_answers) if u == c)
        total_q = len(req.user_answers)
        incorrect = total_q - score
        marks_obtained = score
        total_marks = total_q
        percentage = (marks_obtained / total_marks) * 100 if total_q else 0

        save_result(score, incorrect, marks_obtained, total_marks, percentage)

        return {
            "topic": req.topic,
            "level": req.level,
            "score": score,
            "incorrect": incorrect,
            "marks_obtained": marks_obtained,
            "total_marks": total_marks,
            "percentage": percentage,
            "correct_answers": correct_answers
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/progress")
def get_progress():
    try:
        results = fetch_results()
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
