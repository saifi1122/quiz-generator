
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os


# ================Load environment variables================

load_dotenv()


#==========================Initialize LLM==================

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.4,
    api_key=os.getenv("GOOGLE_API_KEY")
)


#=================Define MCQ State Schema using Pydantic==============

class MCQState(BaseModel):
    topic: str
    level: str = Field(default="intermediate")  
    questions: str = Field(default="")         


#================Function to generate MCQs==============

def generate_mcqs(topic: str, level: str) -> str:
    """
    Generate MCQs with difficulty level
    
    Args:
        topic: Quiz topic
        level: "beginner", "intermediate", or "advanced"
    
    Returns:
        Raw text containing 10 MCQs
    """
    level_instructions = {
        "beginner": "Focus on basic concepts, simple terminology, and straightforward questions suitable for beginners. Use simple language.",
        "intermediate": "Include moderate difficulty questions that require understanding of core concepts and some analytical thinking.",
        "advanced": "Create complex scenarios requiring deep understanding, critical thinking, and application of advanced concepts."
    }

    prompt = f"""
Generate exactly 10 multiple-choice questions (MCQs) on the topic: "{topic}"

Difficulty Level: {level.upper()}
Instructions: {level_instructions.get(level, level_instructions["intermediate"])}

Rules:
- Each question must have four options: a), b), c), d)
- Adjust difficulty according to {level} level
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
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()


#==============Create MCQ Generation Agent with LangGraph============

def create_mcq_agent(llm):
    workflow = StateGraph(
        MCQState,
        start="generate_mcqs_node",
        end=END
    )

    #==================Node action using generate_mcqs function=========

    def generate_mcqs_node(state: MCQState):
        state.questions = generate_mcqs(state.topic, state.level)
        return state

    #=============Add node and edges===========

    workflow.add_node("generate_mcqs_node", generate_mcqs_node)
    workflow.add_edge("__start__", "generate_mcqs_node")
    workflow.add_edge("generate_mcqs_node", END)

    return workflow


#============Test Run ==================

if __name__ == "__main__":
    agent = create_mcq_agent(llm)
    compiled_agent = agent.compile()

    test_state = MCQState(topic="Python OOP", level="intermediate")
    result = compiled_agent.invoke(test_state)

    #==========Convert dict back to Pydantic model for dot access=========


    if not isinstance(result, MCQState):
        result = MCQState(**result)

    print("\n=== GENERATED MCQs ===")
    print(result.questions)
