import os
import asyncio
import httpx
from typing import TypedDict

from langgraph.graph import StateGraph, END
from langgraph.types import Send

from langchain_google_vertexai import ChatVertexAI, HarmCategory, HarmBlockThreshold

llm = ChatVertexAI(
    model=os.getenv("GOOGLE_MODEL", "gemini-2.5-flash"), # Vertex prefers explicit versions
    project="gensec-liav-dahari",
    location="us-central1",
    safety_settings={
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
    },
)

# ---------------------------------------------------------------------
# Graph state
# ---------------------------------------------------------------------

class State(TypedDict):
    query: str
    nba: str | None
    nfl: str | None

# ---------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------

async def fetch(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, */*"
    }
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        r = await client.get(url, headers=headers)
        r.raise_for_status() # Throw an explicit error if the site blocks us (e.g., 403 Forbidden)
        
        # Debug statement so you know the scrape worked
        print(f"[Debug] Fetched {len(r.text)} bytes from {url}")
        return r.text

async def extract_and_summarize(html: str) -> str:
    prompt = f"""
You are an expert sports news summarizer given raw HTML/XML from a sports headline feed.

1. Identify the main news article headlines in the text.
2. Summarize the current news in ONE concise paragraph.
3. Return ONLY that paragraph. Do not include conversational filler, greetings, or ask for more information.

FEED CONTENT:
{html[:12000]}
"""
    resp = await llm.ainvoke(prompt)
    return resp.content.strip()

# ---------------------------------------------------------------------
# Agents (Switched to CBS Sports)
# ---------------------------------------------------------------------

async def nba_agent(state: State):
    html = await fetch("https://www.cbssports.com/rss/headlines/nba/")
    summary = await extract_and_summarize(html)
    return {"nba": summary}

async def nfl_agent(state: State):
    html = await fetch("https://www.cbssports.com/rss/headlines/nfl/")
    summary = await extract_and_summarize(html)
    return {"nfl": summary}

async def coordinator(state: State):
    return {}

async def route(state: State):
    prompt = f"""
User request: {state['query']}

Decide which sports news is requested.
Reply with exactly one word:
nba
nfl
both
"""
    resp = await llm.ainvoke(prompt)
    decision = resp.content.lower().strip()

    if decision == "nba":
        return Send("nba", state)
    if decision == "nfl":
        return Send("nfl", state)
    return [Send("nba", state), Send("nfl", state)]

# Graph

g = StateGraph(State)

g.add_node("coord", coordinator)
g.add_node("nba", nba_agent)
g.add_node("nfl", nfl_agent)

g.set_entry_point("coord")
g.add_conditional_edges(
    "coord", 
    route, {
        "nba": "nba",
        "nfl": "nfl",
    }
)

g.add_edge("nba", END)
g.add_edge("nfl", END)

app = g.compile()

# ---------------------------------------------------------------------
# Interactive prompt 
# ---------------------------------------------------------------------

async def main():
    # Print the graph once on startup
    print("\n--- Application Graph ---")
    print(app.get_graph().draw_ascii())
    print("-------------------------\n")
    
    print("Welcome to my sports headlines summary application. Ask me to summarize news from a sport.")

    while True:
        line = input("\nllm>> ")
        if not line:
            break
            
        try:
            result = await app.ainvoke({"query": line})
            
            if result.get("nba"):
                print("\n[NBA]:", result["nba"])
            if result.get("nfl"):
                print("\n[NFL]:", result["nfl"])
                
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(main())
