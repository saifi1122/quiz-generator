from langgraph.graph import StateGraph, END
from typing import List, Literal
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
import re

#=========Load .env file for API key==========
load_dotenv()

#=============Initialize Gemini LLM=================
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.4,
    api_key=os.getenv("GOOGLE_API_KEY")
)


# ===========State Definition using Pydantic==========

class ExplainerState(BaseModel):
    topic: str
    user_query: str
    explanation: str = ""
    examples: List[str] = Field(default_factory=list)
    summary: str = ""
    messages: List[str] = Field(default_factory=list)
    next_node: Literal["explain", "examples", "summary"] | None = None


# ============ Generate Explanation=======

def generate_explanation(state: ExplainerState, llm):
    prompt = f"Explain the topic '{state.topic}' clearly in simple, easy-to-understand language."
    response = llm.invoke([HumanMessage(content=prompt)])
    state.explanation = response.content
    state.messages.append("Explanation generated")
    return state


# =======================Generate Examples========

def generate_examples(state: ExplainerState, llm):
    prompt = f"Give 3 real-life simple examples for the topic '{state.topic}'."
    response = llm.invoke([HumanMessage(content=prompt)])
    state.examples = response.content.split("\n")
    state.messages.append("Examples generated")
    return state


# ========Summarize Topic========

def summarize_topic(state: ExplainerState, llm):
    prompt = f"Write a short 3-4 line summary of the topic '{state.topic}'."
    response = llm.invoke([HumanMessage(content=prompt)])
    state.summary = response.content
    state.messages.append("Summary generated")
    return state


#===========define the router mapping (Condition)================

ROUTING_RULES = {
    r"\bexample\b|\bexamples\b": "examples",
    r"\bsummary\b": "summary",
}

def determine_next_node(state: ExplainerState):
    query = state.user_query.lower()
    for pattern, node in ROUTING_RULES.items():
        if re.search(pattern, query):
            state.messages.append(f"Routing: User query matched → '{node}'")
            return node
    state.messages.append("Routing: Default → 'explain'")
    return "explain"



#  ============langGraph Workflow============

def create_topic_explainer_agent(llm):
    workflow = StateGraph(ExplainerState)
    
    # Add nodes
    workflow.add_node("explain", lambda state: generate_explanation(state, llm))
    workflow.add_node("examples", lambda state: generate_examples(state, llm))
    workflow.add_node("summary", lambda state: summarize_topic(state, llm))
    workflow.add_node("router", lambda state: state) 

    #==============set entry point
    workflow.set_entry_point("router")

    #=========Conditional edges ==========
    workflow.add_conditional_edges(
        "router",
        lambda state: determine_next_node(state),  # use regex-based routing
        {
            "explain": "explain",
            "examples": "examples",
            "summary": "summary",
        }
    )

    #=============Sequential edges after routing
    workflow.add_edge("explain", "examples")
    workflow.add_edge("examples", "summary")
    workflow.add_edge("summary", END)

    return workflow.compile()



#============Terminal Test==================

if __name__ == "__main__":
    agent = create_topic_explainer_agent(llm)

    user_query = input("Enter your query/topic: ").strip()

    initial_state = ExplainerState(
        topic=user_query,
        user_query=user_query
    )

    # Use determine_next_node instead of router_node
    first_node_name = determine_next_node(initial_state)
    print(f"\n[DEBUG] Router selected first node: '{first_node_name}'\n")

    result = agent.invoke(initial_state)

    print("\n--- FLOW COMPLETE ---")
    print("\nMessages:", result.get("messages"))  
    print("\nExplanation:\n", result.get("explanation"))  
    print("\nExamples:\n", "\n".join(result.get("examples", [])))  
    print("\nSummary:\n", result.get("summary"))


