# SecurAgent: Video Screencast Presentation Script
**Course:** COT4930 - Security (System) Engineering with Generative AI (FAU)  
**Student:** Liav Dahari (FAU ID: Z23815316)  
**Assignment:** Homework 3 - LangChain & LangGraph Multi-Agent System  
**Estimated Video Duration:** 4 - 6 minutes  

---

## Pre-Recording Checklist & Setup

1. **Terminal Ready:** Open your terminal in the repository root directory (`gensec-code/`).
2. **Virtual Environment Active:**
   ```bash
   source .venv/bin/activate
   ```
3. **VS Code / IDE Ready:** Have the following files open in tabs so you can quickly switch between them:
   - `HW3/tools.py`
   - `HW3/graph.py`
   - `HW3/agent.py`
   - `HW3/agent_graph.png`
   - `HW3/test_agent.py`
   - `HW3/README.md`
4. **Clean Terminal Screen:** Run `clear`.

---

## Video Timeline & Script

---

### Segment 1: Introduction & Assignment Goals (0:00 - 0:45)

**[Visual: Show `HW3/README.md` or repository structure in VS Code]**

**Spoken Script:**
> *"Hello everyone and welcome! My name is **Liav Dahari** (FAU ID: Z23815316), and this is my video presentation for **Homework 3** in **COT4930: Generative AI Security** at Florida Atlantic University.*
>
> *For this assignment, based on our lab exercises, we were tasked with building a custom LangChain agent by augmenting the starter code with additional tools or architectures.*
>
> *Rather than stopping at the minimum requirements, I designed **SecurAgent**—a comprehensive system that satisfies all three difficulty tiers in the prompt:*
> 1. *It retains both the **PythonREPL** and a secured **Terminal tool**;*
> 2. *It adds **Level 1 built-in tools** like live DuckDuckGo web search, Wikipedia, and SQLite database querying;*
> 3. *It implements **Level 2 custom tools with Pydantic validation**, specifically integrating my **Homework 2 SmartNotebook RAG application** with strict in-line citations, as well as an Azure Active Directory security audit tool;*
> 4. *And for **Level 3**, it implements a stateful **Multi-Agent LangGraph architecture** featuring supervisor routing, memory checkpointing, and human-in-the-loop review.*
>
> *All original starter lab scripts (01 through 08 and presidents.py) were kept completely untouched as pristine baselines, with project dependencies isolated using the `uv` virtual environment manager.*
>
> *Let’s dive into the code!"*

---

### Segment 2: Code Walkthrough - Tool Suite & Retained Tools (0:45 - 2:00)

**[Visual: Switch to `HW3/tools.py` and scroll down as you discuss]**

#### 1. Retained Tools (`tools.py`, lines 75 - 135)
**[Highlight: `python_repl_tool` and `execute_command`]**

**Spoken Script:**
> *"Starting in `HW3/tools.py`, the assignment requires retaining either the PythonREPL or the Terminal tool. SecurAgent retains **both**:*
> - *Here on line 78 is `python_repl_tool` from `langchain_experimental`, allowing the agent to evaluate Python expressions and perform numerical analysis.*
> - *Directly below it, starting on line 81, is our retained `terminal_tool` (`execute_command`). Notice that we added safety engineering: a Pydantic `TerminalCommandInput` validator that enforces an execution timeout and uses regex guards to block dangerous patterns like `rm -rf /` or fork bombs before they can run."*

#### 2. Level 1 - Additional Built-in Tools (`tools.py`, lines 137 - 220)
**[Highlight: `web_search_tool`, `wikipedia_tool`, and `query_sqlite_database`]**

**Spoken Script:**
> *"Next, for **Level 1**, we added support for built-in tools not found in the lab exercises:*
> - *On line 139 is `duckduckgo_search` (`DuckDuckGoSearchRun`), providing real-time web search capabilities without needing any third-party API keys.*
> - *On line 151 is `wikipedia_search`, allowing the agent to pull factual and academic summaries.*
> - *And on line 165 is `sql_db_query` (`query_sqlite_database`), which uses Pydantic validation to execute read-only SELECT and PRAGMA statements strictly against SQLite databases in our `db_data` directory."*

#### 3. Level 2 - Custom Tools with Pydantic Validation (`tools.py`, lines 222 - 540)
**[Highlight: `smartnotebook_rag_search` and `database_security_audit`]**

**Spoken Script:**
> *"For **Level 2**, we implemented custom tools:*
> - *First, on line 242 is `smartnotebook_rag_search`. As suggested in the assignment, this directly imports and utilizes my **Homework 2 RAG application**. It dynamically imports `ResearchNoteLoader` from `HW2/notebook_loader.py` to ingest markdown research notes and JSON datasets from `HW2/rag_data/notes/`, performing keyword and semantic token relevance retrieval and strictly appending verified bracketed citations—`[Source: filename]`—to every retrieved context passage.*
> - *Second, on line 363 is `database_security_audit`. This is a custom Pydantic-validated security tool designed for this course. It audits our two SQLite datasets: scanning `metactf_users.db` for password hash algorithms like PBKDF2-SHA256, and analyzing `roadrecon.db`—an Azure Active Directory tenant reconstruction database—to detect critical privilege tiers like Global Administrators and Application Administrators.*
> - *Third, on line 498 is `presidents_analyzer`, which parses the presidential dataset from `presidents.py` to compute longevity metrics, terms, and average ages."*

---

### Segment 3: Code Walkthrough - LangGraph Architecture (2:00 - 3:00)

**[Visual: Switch to `HW3/graph.py` and show `agent_graph.png`]**

**Spoken Script:**
> *"Now let's examine **Level 3: the custom LangGraph architecture** in `HW3/graph.py`.*
>
> *Here on screen is `HW3/agent_graph.png`, generated directly by our code.*
>
> *Our state graph is defined around `MultiAgentState`, which extends LangGraph's `MessagesState`. It features:*
> 1. *A **Supervisor Node** (line 144): acting as the orchestrator. It inspects incoming user queries and delegates work to the tool node or synthesizes the final response.*
> 2. *A **Prebuilt ToolNode** (line 197): registered with all 8 of our domain tools.*
> 3. *A **Human Review Node** (`human_review`, line 192): inspired by lab exercise 07. Through conditional routing in `route_supervisor` (line 204), when Human-in-the-Loop mode is active, any sensitive terminal or Python REPL command triggers an execution pause before execution, requiring human verification `[y/N]` or feedback before continuing.*
> 4. *A `MemorySaver` checkpointer (line 280), ensuring conversations maintain persistent state across turns.*
>
> *Notice also that in `get_llm()` (line 65), credentials are never hardcoded. It dynamically checks for Google Gemini, Vertex AI, OpenAI, or Anthropic, and provides a deterministic simulation fallback so the system can run offline smoothly."*

---

### Segment 4: Live Demonstration (3:00 - 4:45)

**[Visual: Switch to Terminal]**

#### Test 1: Run the Automated Test Suite
**Command:**
```bash
python -m unittest HW3/test_agent.py
```
**Spoken Script:**
> *"Now let's see SecurAgent in action! First, let's run our automated test suite in `HW3/test_agent.py`.*
> *[Run command]*
> *Notice that all 14 tests pass in approximately 0.2 seconds! This verifies our Python REPL, terminal safety filters, SQLite queries, HW2 RAG citation generation, Pydantic validations, and LangGraph workflow compilation."*

#### Test 2: Architecture Graph Export
**Command:**
```bash
python HW3/agent.py --draw
```
**Spoken Script:**
> *"Next, let's run `python HW3/agent.py --draw`.*
> *[Run command]*
> *This exports `agent_graph.png` and prints the ASCII topology directly to the terminal, showing the entry point, supervisor orchestrator, conditional human review edge, and tool node."*

#### Test 3: Demo Custom HW2 SmartNotebook RAG Tool
**Command:**
```bash
python HW3/agent.py -q "Summarize the key security principles in RAG from my notes"
```
**Spoken Script:**
> *"Now let's test our Level 2 custom RAG tool utilizing Homework 2.*
> *[Run command]*
> *Notice the rich formatted output! The agent routes the query through the graph to `smartnotebook_rag_search`. It reads from `ai_security_brief.md` in my HW2 notes and retrieves key security principles: Context Grounding, Access Control, Throttled Ingestion, and Hybrid Retrieval—complete with verified `[Source: ai_security_brief.md]` citations."*

#### Test 4: Demo Database Security Audit Tool
**Command:**
```bash
python HW3/agent.py -q "Perform a security audit on roadrecon.db"
```
**Spoken Script:**
> *"Next, let's test our custom security audit tool on the Azure Active Directory reconnaissance database `roadrecon.db`.*
> *[Run command]*
> *Here, SecurAgent audits the database, discovers 2 users assigned to the CRITICAL 'Global Administrator' directory role, and flags an 'Application Administrator' role, returning a structured JSON security report."*

#### Test 5: Demo Presidential Longevity Analyzer
**Command:**
```bash
python HW3/agent.py -q "Analyze the age of US presidents when leaving office"
```
**Spoken Script:**
> *"Let's test our custom presidential analyzer:*
> *[Run command]*
> *SecurAgent analyzes all 45 presidents from `presidents.py`, calculating an average age of 60.78 years, with Joe Biden as the oldest at term end (age 82) and John F. Kennedy as the youngest (age 46)."*

#### Test 6: Demo Interactive Human-in-the-Loop (HITL) Mode
**Command:**
```bash
python HW3/agent.py --hitl
```
*(When prompt appears: type `exit`)*
**Spoken Script:**
> *"Finally, when running in interactive mode with `--hitl`, SecurAgent launches our rich terminal REPL. In this mode, any time a terminal or shell tool is scheduled, execution interrupts and prompts the user: 'Approve execution? [y/N] or type feedback', giving full control to the human reviewer before code execution."*

---

### Segment 5: Conclusion & Wrap-Up (4:45 - 5:15)

**[Visual: Switch back to VS Code showing Git log / commit history or `HW3/README.md`]**

**Spoken Script:**
> *"To wrap up:*
> - *We developed our code incrementally with frequent, well-structured git commits;*
> - *Documented every function with complete Python docstrings;*
> - *Isolated dependencies using `uv`;*
> - *Enforced zero hardcoded API keys;*
> - *And created full documentation in `HW3/README.md` and `hw3-Z23815316.docx`.*
>
> *Thank you very much for watching! All code and commit history are pushed and available in my GitHub repository."*

---

## Quick Reference: Commands Used in Video

```bash
# 1. Run test suite
python -m unittest HW3/test_agent.py

# 2. Export & display graph topology
python HW3/agent.py --draw

# 3. HW2 Custom RAG Demo
python HW3/agent.py -q "Summarize the key security principles in RAG from my notes"

# 4. Azure AD Database Security Audit Demo
python HW3/agent.py -q "Perform a security audit on roadrecon.db"

# 5. Presidential Longevity Analysis Demo
python HW3/agent.py -q "Analyze the age of US presidents when leaving office"

# 6. Launch Human-in-the-Loop Interactive REPL
python HW3/agent.py --hitl
```
