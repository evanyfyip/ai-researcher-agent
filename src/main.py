from fastmcp import FastMCP
from src.agent import ResearcherAgent

app = FastMCP("researcher-agent")

agent = ResearcherAgent()

@app.tool()
async def pulse_research() -> str:
    """Get the latest pulse of developments from all sources."""
    return agent.pulse_search()

@app.tool()
async def targeted_research(query: str, tools: str = None) -> str:
    """Perform targeted research on a query, optionally specifying tools as comma-separated list."""
    tool_list = tools.split(',') if tools else None
    return agent.targeted_search(query, tool_list)

if __name__ == "__main__":
    app.run()
