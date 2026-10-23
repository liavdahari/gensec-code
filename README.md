# Generative Security (COT4930) - Coursework Repository

**Student:** Liav Dahari (FAU ID: Z23815316)  
**Institution:** Florida Atlantic University  
**Course:** COT4930 - Security (System) Engineering with Generative AI  

---

## Repository Structure

```text
gensec-code/
├── README.md
├── .gitignore
├── HW4/                          # Homework 4: Multi-Server MCP Agent Application
│   ├── agent.py                  # Multi-Server Coordinating Security Agent
│   ├── mcp-server.py             # Custom FastMCP SecOps Server (3 security tools)
│   ├── requirements.txt          # Python dependencies (fastmcp, mcp, requests)
│   ├── screencast_url.txt        # YouTube screencast URL placeholder
│   ├── hw4-Z23815316.docx        # Assignment submission document
│   └── README.md                 # Detailed HW4 documentation
├── HW3/                          # Homework 3: LangGraph Multi-Agent System
│   ├── agent.py                  # Main CLI application & interactive REPL
│   ├── graph.py                  # Level 3 LangGraph Multi-Agent Architecture & HITL
│   ├── tools.py                  # Modular tool suite (Retained, Level 1, Level 2)
│   ├── test_agent.py             # Automated test suite (14 passing tests)
│   ├── agent_graph.png           # Mermaid architecture diagram
│   ├── hw3-Z23815316.docx        # Assignment submission document
│   ├── HW.md                     # Homework 3 instructions
│   ├── README.md                 # Detailed HW3 documentation
│   ├── requirements.txt          # Python dependencies
│   ├── db_data/                  # SQLite reconnaissance databases
│   └── [01-08]_*.py              # Lab starter scripts (unmodified references)
└── HW2/                          # Homework 2: LangChain RAG Application
    ├── app.py                    # SmartNotebook RAG Application (CLI & Chainlit)
    ├── notebook_loader.py        # Feature 1: Custom Document Loader (BaseLoader)
    ├── test_notebook_loader.py   # Automated unit tests for Feature 1
    ├── 07_rag_loaddb.py          # Vector DB loader with Vertex AI batching & custom loader
    ├── 08_rag_docsearch.py       # Document similarity search script
    ├── 09_rag_query.py           # Grounded CLI query script
    ├── 10_chainlit_rag_query.py  # Chainlit web chat interface
    ├── wikipedia_loader.py       # Rate-limited Wikipedia loader
    ├── test_wikipedia_loader.py  # Wikipedia loader unit tests
    ├── requirements.txt          # Python dependencies
    ├── screencast_url.txt        # YouTube screencast URL placeholder
    ├── hw2-Z23815316.docx        # Assignment submission document
    └── rag_data/                 # Multimodal datasets
        ├── JSON/                 # Tabular datasets (airports, S&P 500, inflation, crops)
        ├── notes/                # Markdown research notes with YAML frontmatter
        ├── txt/                  # Plain text documents
        ├── pdf/                  # PDF documents
        ├── docx/                 # Word documents
        ├── csv/                  # CSV spreadsheets
        └── md/                   # Markdown guides
```

---

## Homework 4: Multi-Server MCP Agent Application

A coordinated **Model Context Protocol (MCP)** multi-server agent system combining external published browser automation with custom defensive security tooling:

1. **Published MCP Server (Chrome DevTools MCP):**
   - Configured via `StdioServerParameters` using `npx -y chrome-devtools-mcp@latest --headless --no-usage-statistics`.
   - Connects over `stdio` and provides 32 browser inspection and automation tools (`navigate_page`, `take_snapshot`, etc.).
2. **Custom FastMCP Server (`mcp-server.py`):**
   - Built with `FastMCP("Simple-SecOps-Tools")` running over `stdio` (patterned after `04_MCP/01_sqlite`).
   - Implements 3 custom defensive tools:
     - `check_url_security`: Audits HTTPS enforcement and defensive HTTP headers (HSTS, CSP, X-Frame-Options).
     - `scan_text_for_secrets`: Detects exposed API keys (Google, OpenAI), GitHub PATs, and plaintext credentials in live DOM content.
     - `identify_hash_type`: Analyzes cryptographic hash formats (MD5, SHA-1, SHA-256, bcrypt) and flags collision or crack vulnerabilities.
3. **Coordinating Agent (`agent.py`):**
   - Implements client architecture from `04_MCP/01_sqlite/01_stdio_mcp_client.py` using `mcp.client.stdio.stdio_client` and `ClientSession`.
   - Orchestrates an end-to-end audit: navigates to target URL, extracts live DOM text snapshot, passes content to SecOps tools, and outputs a formatted security assessment report.

See [HW4/README.md](file:///Users/liavdahari/Documents/FAU%20FALL%202026/COT4930-%20GENSEC/gensec-code/HW4/README.md) for full instructions, workflow diagrams, and sample demonstrations.

---

## Homework 3: SecurAgent Multi-Agent LangGraph System

SecurAgent coordinates specialized agents across AI security research, Azure AD database auditing, live web intelligence, and safe code execution:

1. **Retained Tools:** `PythonREPLTool` and safe `terminal_tool` with timeout guards and safety filters.
2. **Level 1 (Built-in Tools):** `DuckDuckGoSearchRun`, `WikipediaQueryRun`, and SQLite database querying.
3. **Level 2 (Custom Tools with Pydantic):**
   - `smartnotebook_rag_search`: Integrates HW2 `ResearchNoteLoader` and notes knowledge base with citations `[Source: filename]`.
   - `database_security_audit`: Pydantic-validated scanner inspecting Azure AD `roadrecon.db` and MetaCTF `metactf_users.db`.
   - `presidents_analyzer`: Analytical tool computing presidential longevity metrics from `presidents.py`.
4. **Level 3 (Custom Architecture - LangGraph):** Stateful multi-agent graph with Supervisor orchestration, ToolNode execution, `MemorySaver` checkpointer, and Human-in-the-Loop review.
5. **Testing & Quality:** 14 automated unit and integration tests passing in `test_agent.py`.

See [HW3/README.md](file:///Users/liavdahari/Documents/FAU%20FALL%202026/COT4930-%20GENSEC/gensec-code/HW3/README.md) for full instructions and sample demonstrations.

---

## Homework 2: SmartNotebook RAG Application

SmartNotebook RAG augments a LangChain retrieval-augmented generation pipeline with two core features:

1. **Feature 1 - Custom Document Loader (`ResearchNoteLoader`)**:
   - Subclasses LangChain's `BaseLoader` in `notebook_loader.py`.
   - Ingests structured JSON datasets (records, tables, stats) and Markdown research notes with YAML frontmatter metadata.
   - Tested by `test_notebook_loader.py`.

2. **Feature 2 - Grounded Q&A with Strict In-Line Citations**:
   - Implemented in `app.py`.
   - Restricts LLM responses strictly to retrieved document context.
   - Attaches verified in-line citations `[Source: filename]` to every claim and displays a verified sources list.

---

## Setup and Execution

### Homework 4: Multi-Server MCP Agent
```bash
cd HW4
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Run full coordinated security audit
python agent.py https://example.com

# Or list tools across both connected MCP servers
python agent.py --list-tools
```

### Homework 3: LangGraph Multi-Agent System
```bash
cd HW3
source .venv/bin/activate
python agent.py
```

### Homework 2: SmartNotebook RAG Application
```bash
cd HW2
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt

# Run interactive CLI
python3 app.py

# Or launch Chainlit web UI
chainlit run app.py
```
