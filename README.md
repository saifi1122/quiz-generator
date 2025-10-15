# Multi-Agent Study Assistant
**Author:** Saif Ullah

---

## Project overview
Multi-Agent Study Assistant is a small learning tool built with three cooperating agents:
- **Topic Explainer Agent** — explains a topic in simple language (LLM-powered).
- **Quiz Generator Agent** — generates 10 MCQs at Beginner / Intermediate / Advanced levels.
- **Performance Evaluator Agent** — checks answers, scores quizzes, generates feedback and saves results.

Backend: **FastAPI** (exposes endpoints)  
Frontend: **Streamlit** (interactive UI)  
Persistence: **SQLite** (`quiz_app.db`)  
Agent orchestration: **LangGraph** (where applicable)  
LLM: **Gemini / GPT** (configured via environment variable)

---

## Features
- Generate clear explanations for a topic.
- Generate 10 MCQ quizzes by difficulty level.
- Grade answers using an LLM-based checker or internal logic.
- Save results to a local SQLite DB: correct, incorrect, marks, percentage, date.
- View progress / history table from UI or API.
- Request feedback (logic or LLM based).

---

## Folder structure (what each file does)
