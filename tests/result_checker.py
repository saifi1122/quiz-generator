
import re
import json
import logging
from typing import List, Dict
from pydantic import BaseModel, ValidationError
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# ------------------------- Logging Setup -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# ------------------------- Pydantic Models -------------------------
class MCQOption(BaseModel):
    a: str
    b: str
    c: str
    d: str

class MCQQuestion(BaseModel):
    question: str
    options: MCQOption

# ------------------------- Initialize LLM -------------------------
def init_llm(api_key: str) -> ChatGoogleGenerativeAI:
    """
    Initialize Google Gemini LLM (Gemini 2.5 Flash)
    """
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.4,
        api_key=api_key,
    )

# ------------------------- Helper Functions -------------------------
def explain_topic(llm: ChatGoogleGenerativeAI, topic: str) -> str:
    """
    Generate a simple, clear explanation of a topic using LLM.
    """
    prompt = f"Explain the topic '{topic}' clearly in simple, easy-to-understand language."
    try:
        resp = llm.invoke([HumanMessage(content=prompt)])
        return getattr(resp, "content", str(resp))
    except Exception as e:
        logging.error(f"Error in explain_topic: {e}")
        return f"Error generating explanation: {e}"

def generate_mcqs_text(llm: ChatGoogleGenerativeAI, topic: str) -> str:
    """
    Generate exactly 10 MCQs in strict format using LLM.
    """
    prompt = f"""
Generate exactly 10 multiple-choice questions (MCQs) on the topic: "{topic}"

Rules:
- Each question must have four options: a), b), c), d)
- DO NOT include correct answers
- DO NOT include explanations
- DO NOT add numbering (no 1., 2., etc.)
- Separate questions with a single blank line
- Format strictly:

Question text?
a) Option A
b) Option B
c) Option C
d) Option D

Return ONLY the questions in this exact format and nothing else.
"""
    try:
        resp = llm.invoke([HumanMessage(content=prompt)])
        return getattr(resp, "content", str(resp)).strip()
    except Exception as e:
        logging.error(f"Error in generate_mcqs_text: {e}")
        return f"Error generating MCQs: {e}"

def parse_mcqs(mcqs_text: str) -> List[Dict]:
    """
    Parse MCQs text into a list of dictionaries with question and options.
    Returns list of dicts: [{"question": str, "options": {"a": str, ...}}, ...]
    """
    blocks = [b.strip() for b in re.split(r'\n\s*\n', mcqs_text) if b.strip()]
    parsed = []

    for block in blocks:
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if not lines:
            continue
        question_text = lines[0]
        opts = {}
        for opt_line in lines[1:]:
            match = re.match(r'^([abcd])\)\s*(.+)', opt_line, re.I)
            if match:
                opts[match.group(1).lower()] = match.group(2).strip()

        if len(opts) == 4:
            # Validate using Pydantic
            try:
                mcq_option = MCQOption(**opts)
                mcq_question = MCQQuestion(question=question_text, options=mcq_option)
                parsed.append(mcq_question.dict())
            except ValidationError as e:
                logging.warning(f"Skipping invalid MCQ block due to validation error: {e}")
    return parsed

def get_correct_answers_from_llm(llm: ChatGoogleGenerativeAI, mcqs_text: str) -> List[str]:
    """
    Ask LLM to return only a JSON with correct answers for each MCQ.
    Returns list of letters ["a", "b", "c", ...]
    """
    prompt = f"""
You are an exam evaluator. Below are 10 multiple-choice questions (MCQs).
For each question, return ONLY the correct option as a single lowercase letter: a, b, c, or d.
Return the result in strict JSON format like:

{{"answers": ["b","c","a","d", ...]}}

Do NOT include any explanation, text, or additional fields.
Here are the MCQs:

{mcqs_text}
"""
    try:
        resp = llm.invoke([HumanMessage(content=prompt)])
        text = getattr(resp, "content", str(resp)).strip()

        # Try parsing JSON directly
        try:
            parsed = json.loads(text)
            answers = parsed.get("answers", [])
            if isinstance(answers, list) and len(answers) >= 10:
                return [a.lower() for a in answers[:10]]
        except Exception:
            pass

        # Fallback: extract JSON substring
        match = re.search(r'(\{.*"answers"\s*:\s*\[.*?\].*\})', text, re.S)
        if match:
            try:
                parsed = json.loads(match.group(1))
                answers = parsed.get("answers", [])
                if isinstance(answers, list) and len(answers) >= 10:
                    return [a.lower() for a in answers[:10]]
            except Exception:
                pass

        #========Final fallback regex letters========
        letters = re.findall(r'\b([abcd])\b', text.lower())
        if len(letters) >= 10:
            return letters[:10]

        raise ValueError(f"Could not parse answers from LLM response:\n{text}")

    except Exception as e:
        logging.error(f"Error in get_correct_answers_from_llm: {e}")
        return ["a"] * 10  # fallback default answers
