# combined_mcp.py
import os
import socket
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# -----------------------------
# Utility: find free port
# -----------------------------
def get_free_port(start_port=8000, end_port=9000):
    """Return the first available port in the given range."""
    for port in range(start_port, end_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free ports available")

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# -----------------------------
# Initialize FastMCP
# -----------------------------
mcp = FastMCP("UnifiedLawMCP")

# -----------------------------
# Setup LLM (ChatGroq)
# -----------------------------
try:
    from langchain_groq import ChatGroq
    llm = ChatGroq(model="llama3-70b-8192", api_key=GROQ_API_KEY)
except Exception:
    llm = None

# -----------------------------
# Optional DuckDuckGo search
# -----------------------------
try:
    from duckduckgo_search import DDGS
    HAS_DDG = True
except Exception:
    HAS_DDG = False

# -----------------------------
# Helper: Run LLM or Mock
# -----------------------------
def run_llm_or_mock(prompt: str) -> str:
    try:
        if llm:
            resp = llm.invoke(prompt)
            return getattr(resp, "content", str(resp))
    except Exception as e:
        return f"[LLM error] {e}\n\nPrompt:\n{prompt}"
    return f"[Mock response] Prompt:\n\n{prompt}"

# ==========================================================
# 📘 Case-Specific Legal Tools
# ==========================================================
@mcp.tool()
def rti_info(facts: str) -> str:
    prompt = (
        "You are an expert on Indian RTI (Right to Information) process.\n\n"
        f"FACTS: {facts}\n\n"
        "List relevant Acts/sections, the procedure to file an RTI (portals/forms/fees), "
        "and provide a short sample RTI application template with placeholders."
    )
    return run_llm_or_mock(prompt)

@mcp.tool()
def divorce_info(facts: str) -> str:
    prompt = (
        "You are an expert on family law & divorce in India.\n\n"
        f"FACTS: {facts}\n\n"
        "List likely legal provisions/sections, procedural steps (mediation, court filings), "
        "documents required, timelines, and provide a short sample petition template."
    )
    return run_llm_or_mock(prompt)

@mcp.tool()
def consumer_complaint_info(facts: str) -> str:
    prompt = (
        "You are an expert on consumer protection in India.\n\n"
        f"FACTS: {facts}\n\n"
        "List relevant portions of the Consumer Protection Act, how to approach consumer forums, "
        "documents to attach, approximate fees, and sample complaint structure."
    )
    return run_llm_or_mock(prompt)

@mcp.tool()
def property_dispute_info(facts: str) -> str:
    prompt = (
        "You are an expert on property law in India.\n\n"
        f"FACTS: {facts}\n\n"
        "Identify relevant statutes/sections, likely remedies (civil suit, injunction, possession), "
        "documents to gather, and next-step recommendations."
    )
    return run_llm_or_mock(prompt)

@mcp.tool()
def workplace_issue_info(facts: str) -> str:
    prompt = (
        "You are an expert on Indian labour & employment law.\n\n"
        f"FACTS: {facts}\n\n"
        "Identify applicable statutes/sections (payment, termination, POSH if applicable), "
        "procedural steps, and an action plan (letters, conciliation, complaints)."
    )
    return run_llm_or_mock(prompt)

@mcp.tool()
def family_law_info(facts: str) -> str:
    prompt = (
        "You are an expert on family law in India (maintenance, custody, adoption, guardianship).\n\n"
        f"FACTS: {facts}\n\n"
        "List relevant legal provisions, likely steps, documents, and suggested next actions."
    )
    return run_llm_or_mock(prompt)

@mcp.tool()
def cybercrime_info(facts: str) -> str:
    prompt = (
        "You are an expert on cybercrime law in India (IT Act, IPC supplements).\n\n"
        f"FACTS: {facts}\n\n"
        "List likely offences and sections, steps for preservation of evidence, how to file a police complaint/FIR, "
        "and online portals to report cybercrime."
    )
    return run_llm_or_mock(prompt)

# ==========================================================
# 💡 Guide & Support Tools
# ==========================================================
@mcp.tool()
def guide_steps(case_type: str) -> str:
    """Provide step-by-step practical instructions for a case type in India with law references."""
    prompt = (
        f"You are a legal expert in Indian law. Provide a clear, step-by-step practical guide for a '{case_type}' case. "
        "Include relevant Acts, Sections, and Rules (e.g., RTI Act, 2005; Consumer Protection Act, 2019; Hindu Marriage Act, 1955) "
        "and explain how it's relevant to the case. Also mention required documents, online portals, fees, and timelines."
    )
    return run_llm_or_mock(prompt)

@mcp.tool()
def draft_letter(case_type: str, facts: str) -> str:
    """Return a ready-to-use letter template (RTI, complaint, notice) citing relevant Acts/Sections."""
    prompt = (
        f"Draft a formal, editable legal letter for '{case_type}' based on these facts:\n\n{facts}\n\n"
        "Include placeholders like [Name], [Date], [Recipient]. "
        "Ensure the draft cites at least one relevant law or section (e.g., Section 6(1) of the RTI Act, 2005)."
    )
    return run_llm_or_mock(prompt)

@mcp.tool()
def web_search(query: str) -> str:
    """Return short search results (title + link + snippet) using DuckDuckGo or mock if unavailable."""
    if HAS_DDG:
        try:
            ddgs = DDGS()
            results = ddgs.text(query, max_results=5)
            formatted = []
            for r in results:
                t = r.get("title") or "No title"
                href = r.get("href") or r.get("url") or ""
                body = r.get("body") or ""
                formatted.append(f"- {t}\n  {href}\n  {body}")
            return "\n\n".join(formatted) if formatted else "No results found."
        except Exception as e:
            return f"Search error: {e}"
    else:
        return f"[Search unavailable] DuckDuckGo not installed. Query was: {query}"

# -----------------------------
# Run MCP server
# -----------------------------
if __name__ == "__main__":
    # Use Render-assigned port or default to 10000
    port = int(os.environ.get("PORT", 10000))

    os.environ["FASTMCP_HOST"] = "0.0.0.0"
    os.environ["FASTMCP_PORT"] = str(port)

    print(f"✅ GuideSupportMCP starting on port {port}...")
    mcp.run("streamable-http")


