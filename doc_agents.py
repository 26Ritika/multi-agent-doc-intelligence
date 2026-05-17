from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict
import os


class DocumentState(TypedDict):
    text: str
    question: str
    doc_type: str
    summary_oneline: str
    summary_full: str
    entities: list
    risks: list
    insights: list
    qa_answer: str
    qa_quality: str
    retry_count: int
    current_agent: str

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

def orchestrator_agent(state: DocumentState):
    response = llm.invoke(f"Identify document type in 5 words: {state['text'][:300]}")
    return {**state, "doc_type": response.content, "current_agent": "summarizer"}

def summarizer_agent(state: DocumentState):
    response = llm.invoke(f"""Summarize this document.
ONE LINE: (max 20 words)
FULL: (max 100 words)
Document: {state['text'][:3000]}""")
    oneline, full = "", ""
    for line in response.content.split("\n"):
        if line.startswith("ONE LINE:"):
            oneline = line.replace("ONE LINE:", "").strip()
        elif line.startswith("FULL:"):
            full = line.replace("FULL:", "").strip()
    return {**state, "summary_oneline": oneline, "summary_full": full, "current_agent": "analyzer"}

def analyzer_agent(state: DocumentState):
    response = llm.invoke(f"""Extract:
ENTITIES: 5 items separated by |
RISKS: 3 risks separated by |
INSIGHTS: 3 insights separated by |
Document: {state['text'][:3000]}""")
    entities, risks, insights = [], [], []
    for line in response.content.split("\n"):
        if line.startswith("ENTITIES:"):
            entities = [e.strip() for e in line.replace("ENTITIES:", "").split("|")]
        elif line.startswith("RISKS:"):
            risks = [r.strip() for r in line.replace("RISKS:", "").split("|")]
        elif line.startswith("INSIGHTS:"):
            insights = [i.strip() for i in line.replace("INSIGHTS:", "").split("|")]
    return {**state, "entities": entities, "risks": risks, "insights": insights, "current_agent": "qa"}

def qa_agent(state: DocumentState):
    if not state.get("question"):
        return {**state, "current_agent": "aggregator"}
    response = llm.invoke(f"""Answer from document only.
Document: {state['text'][:4000]}
Question: {state['question']}""")
    return {**state, "qa_answer": response.content, "current_agent": "aggregator"}

def aggregator_agent(state: DocumentState):
    return {**state, "current_agent": "done"}

def router(state: DocumentState):
    return state["current_agent"]

def build_graph():
    graph = StateGraph(DocumentState)
    graph.add_node("orchestrator", orchestrator_agent)
    graph.add_node("summarizer", summarizer_agent)
    graph.add_node("analyzer", analyzer_agent)
    graph.add_node("qa", qa_agent)
    graph.add_node("aggregator", aggregator_agent)
    graph.set_entry_point("orchestrator")
    graph.add_conditional_edges("orchestrator", router, {"summarizer": "summarizer"})
    graph.add_conditional_edges("summarizer", router, {"analyzer": "analyzer"})
    graph.add_conditional_edges("analyzer", router, {"qa": "qa"})
    graph.add_conditional_edges("qa", router, {"aggregator": "aggregator"})
    graph.add_edge("aggregator", END)
    return graph.compile()

agent_graph = build_graph()

def run_agents(text: str, question: str = ""):
    result = agent_graph.invoke({
        "text": text, "question": question,
        "doc_type": "", "summary_oneline": "",
        "summary_full": "", "entities": [],
        "risks": [], "insights": [],
        "qa_answer": "", "qa_quality": "",
        "retry_count": 0, "current_agent": "orchestrator"
    })
    return result
