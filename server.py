from mcp.server import MCPServer

# Create MCP server at module level
mcp = MCPServer("Tutorial MCP Server")


@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtract two numbers."""
    return a - b

@mcp.resource("tutorial://company-info")
def company_info() -> str:
    """Return sample company information."""

    return """
    Company: ABC Technologies
    Department: Data Science
    Specialization: Generative AI and Agentic AI
    Location: India
    """

@mcp.prompt()
def analyze_company(company_name: str, objective: str) -> str:
    """Generate a structured company analysis prompt."""

    return f"""
    You are an expert business analyst.

    Analyze the following company:

    Company Name: {company_name}

    Analysis Objective: {objective}

    Provide:
    1. Company Overview
    2. Business Opportunities
    3. Potential Challenges
    4. Technology Recommendations
    5. Final Recommendations
    """