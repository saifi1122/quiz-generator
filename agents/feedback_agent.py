
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os

#============Load environment variables
load_dotenv()


#==========Define State Schema using Pydantic===========

class FeedbackState(BaseModel):
    topic: str
    score: int
    total_q: int
    percentage: float
    output: str = Field(default="")  


#============Initialize LLM===============

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.5,
    api_key=os.getenv("GOOGLE_API_KEY")
)


#==========Create Feedback Agent===============

def create_feedback_agent(llm):

    #========Create StateGraph with schema=========
    workflow = StateGraph(
        FeedbackState,
        start="generate_feedback",
        end=END
    )

    #=========Node Action=================
    def generate_feedback_action(state: FeedbackState):
        prompt = f"""
        You are an AI tutor. A student took a quiz on the topic: '{state.topic}'.
        The student answered {state.score} out of {state.total_q} questions correctly ({state.percentage:.0f}%).

        Generate a friendly, constructive feedback message based on the performance:
        - If >= 80%: praise and suggest advanced practice
        - If >= 60%: encourage improvement, point out weak areas
        - If < 60%: motivate to review basics, give tips to improve

        Keep the message concise, motivating, and clear.
        """
        response = llm([HumanMessage(content=prompt)])
        state.output = response.content
        return state

    #==========Add node and edge===========
    workflow.add_node("generate_feedback", generate_feedback_action)

    #=============Define the START of the graph===========

    workflow.add_edge("__start__", "generate_feedback")
    workflow.add_edge("generate_feedback", END)

    return workflow


#=======================Test Run ===================

if __name__ == "__main__":
    agent = create_feedback_agent(llm)

    #===========Must COMPILE before invoking
    compiled_agent = agent.compile()

    test_state = FeedbackState(
        topic="Python OOP",
        score=7,
        total_q=10,
        percentage=70.0
    )

    # =====Use invoke==========
    result = compiled_agent.invoke(test_state)

    print("\n=== FEEDBACK OUTPUT ===")
    print(result["output"])
