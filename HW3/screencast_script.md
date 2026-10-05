# Homework 3 Video Screencast Script

**Student:** Liav Dahari (FAU ID: Z23815316)  
**Course:** COT4930 - Generative AI Security (Florida Atlantic University)  
**Assignment:** Homework 3 - LangChain & LangGraph Multi-Agent System (SecurAgent)  

---

## Pre-Recording Checklist

1. Open your terminal in the project root: `/Users/liavdahari/Documents/FAU FALL 2026/COT4930- GENSEC/gensec-code`
2. Activate your virtual environment:
   ```bash
   source .venv/bin/activate
   ```
3. Have these tabs open in VS Code ready to click:
   - `HW3/tools.py`
   - `HW3/graph.py`
   - `HW3/agent_graph.png`
   - `HW3/agent.py`
4. Keep a terminal window open next to VS Code for the live demo.

---

## Presentation Script

### 1. Introduction

Hi everyone, my name is Liav Dahari, FAU ID Z23815316. This is my presentation for Homework 3 in Generative AI Security.

For this assignment, our goal was to build our own custom LangChain agent by taking what we learned in our lab exercises and augmenting it with additional tools and architectures.

In Homework 2, we built a standalone RAG application that could read documents. But a regular LLM or RAG pipeline can't run shell commands, can't write code, and can't make decisions on its own. An agent fixes that by giving the language model tools and a reasoning loop so it can decide which tools to call, inspect the results, and solve complex multi-step problems.

For this project, I created **SecurAgent**, which tackles all three levels of difficulty from the homework prompt:
1. First, it retains **both** the Python REPL and a safe Terminal shell tool.
2. Second, for **Level 1**, it adds built-in tools like live DuckDuckGo web search, Wikipedia, and SQLite database querying.
3. Third, for **Level 2**, it implements custom tools with Pydantic validation—specifically integrating our **Homework 2 SmartNotebook RAG system** with strict in-line citations, and an Azure Active Directory security audit tool.
4. And fourth, for **Level 3**, it uses a stateful **Multi-Agent LangGraph architecture** with a supervisor orchestrator, human-in-the-loop review, and memory checkpointing.

All of our original starter lab scripts (01 through 08 and presidents.py) were kept completely untouched as pristine references, and our dependencies are isolated using the `uv` virtual environment manager.

Now, let's walk through the code.

---

### 2. Code Walkthrough: Tool Suite (`tools.py`)

	1	Click on the tab for tools.py.
	2	Highlight Line 78: python_repl_tool = PythonREPLTool()
	3	Scroll to Line 81 (class TerminalCommandInput) and Line 93 (validate_safe_command).
	4	Highlight Line 109: @tool("terminal_tool", args_schema=TerminalCommandInput)

Starting in `tools.py`, the assignment requires retaining either the PythonREPL or the Terminal tool. SecurAgent retains both:
- Right here at line 78, we instantiate `python_repl_tool` from `langchain_experimental`, allowing our agent to run Python code for math and data processing.
- Then down at line 81 and 109 is our `terminal_tool`. Since running arbitrary shell commands is a major security risk, I added safety engineering using Pydantic: `TerminalCommandInput` sets an execution timeout, and at line 93, `validate_safe_command` uses regex patterns to block dangerous commands like `rm -rf /` or fork bombs before they can ever execute.

---

	1	Scroll down to Line 139: web_search_tool = DuckDuckGoSearchRun(...)
	2	Scroll to Line 152: wikipedia_tool = WikipediaQueryRun(...)
	3	Scroll to Line 165: class SQLQueryInput and Line 190: query_sqlite_database.

Next, for Level 1, we added built-in tools not contained in the lab exercises:
- At line 139 is `duckduckgo_search`, which gives our agent live internet search capabilities without needing any API keys.
- At line 152 is `wikipedia_search` for encyclopedic lookups.
- And down at line 165 and 190 is `sql_db_query`. It uses Pydantic validation to ensure the agent can only run read-only SELECT queries strictly against our local SQLite databases.

---

	1	Scroll down to Line 224: class SmartNotebookRAGInput(BaseModel):
	2	Highlight Line 242: def smartnotebook_rag_search(...)
	3	Scroll down to Line 333: class SecurityAuditInput(BaseModel):
	4	Highlight Line 363: def database_security_audit(...)
	5	Scroll to Line 486: def analyze_presidents_data(...)

Now let's look at Level 2, which are our custom tools:
- Here at line 242 is `smartnotebook_rag_search`. As suggested in the assignment, this directly connects to my **Homework 2 RAG project**. It imports our custom `ResearchNoteLoader` from Homework 2 to read through our AI security notes and datasets. It scores document relevance and forces the output to attach verified citations in brackets, like `[Source: filename]`, so we maintain strict grounding.
- Down at line 363 is `database_security_audit`. This is a security-focused tool tailored to our course. It scans `metactf_users.db` for password hashes like PBKDF2-SHA256, and inspects `roadrecon.db`—an Azure Active Directory reconnaissance database—to identify high-privilege roles like Global Administrators.
- And at line 486 is `presidents_analyzer`, which parses our presidential dataset from `presidents.py` to calculate longevity metrics and term lengths.

---

### 3. Code Walkthrough: LangGraph Architecture (`graph.py`)

	1	Click on the tab for graph.py.
	2	Highlight Line 134: class MultiAgentState(MessagesState):
	3	Scroll to Line 155: def supervisor_node(state: MultiAgentState):
	4	Scroll down to Line 208: def human_review_node and Line 220: def route_supervisor
	5	Scroll down to Line 261: def build_agent_graph and Line 297 (checkpointer=MemorySaver())
	6	Click on the tab for agent_graph.png to show the diagram.

Now let's examine Level 3, which is our custom LangGraph architecture in `graph.py`.

Here on screen is `agent_graph.png`, which was generated directly by our code:
- At line 134, we define `MultiAgentState`, which extends LangGraph's `MessagesState` so the conversation history and tool outputs are preserved.
- At line 155 is our **Supervisor Node**. This acts as the brain and orchestrator. It looks at the user's prompt, decides which tool needs to be called, and directs traffic.
- Down at line 208 and 220, we implemented a **Human-in-the-Loop review node** inspired by lab exercise 07. If human-review mode is turned on, whenever the agent wants to run a shell command or Python code, execution pauses at `human_review` so the user can approve it with 'y' or provide feedback to change it.
- Down at line 297, we compile the graph with `MemorySaver()`, giving our agent session memory across turns.
- Also, in `get_llm()` at line 65, API keys are never hardcoded—they are read from environment variables, with a deterministic simulation fallback so the system runs smoothly offline.

---

### 4. Live Demonstration (Terminal)

	1	Switch to your Terminal window.
	2	Make sure .venv is active.

Now let's jump into the terminal and see SecurAgent in action!

#### Step 1: Run the Test Suite
**Type and run:**
```bash
python -m unittest HW3/test_agent.py
```
> *"First, let's run our automated test suite in `HW3/test_agent.py`.*
> *As you can see, all 14 tests pass in around 0.2 seconds! This tests everything: the Python REPL, terminal safety filters, SQLite queries, HW2 RAG citations, Pydantic validation, and LangGraph graph compilation."*

---

#### Step 2: Show Architecture Graph
**Type and run:**
```bash
python HW3/agent.py --draw
```
> *"Next, let's run `python HW3/agent.py --draw`.*
> *This exports our graph image and prints the ASCII topology right in the terminal, showing our entry point, the supervisor node, the human-review conditional edge, and the tool node."*

---

#### Step 3: Query Custom HW2 RAG Knowledge Base
**Type and run:**
```bash
python HW3/agent.py -q "Summarize the key security principles in RAG from my notes"
```
> *"Now let's test our custom Level 2 RAG tool connected to Homework 2.*
> *Look at the formatted response! SecurAgent routed the query to `smartnotebook_rag_search`. It pulled the key principles from my notes in `ai_security_brief.md`—like context grounding, access control, and batch ingestion—and attached our verified source citations: `[Source: ai_security_brief.md]`."*

---

#### Step 4: Run Azure AD Security Audit
**Type and run:**
```bash
python HW3/agent.py -q "Perform a security audit on roadrecon.db"
```
> *"Next, let's test our security audit tool on the Azure AD database `roadrecon.db`.*
> *Here, SecurAgent audited the database, flagged 2 users assigned to the critical Global Administrator role, identified Application Administrators, and gave us a structured security report."*

---

#### Step 5: Run Presidential Longevity Analysis
**Type and run:**
```bash
python HW3/agent.py -q "Analyze the age of US presidents when leaving office"
```
> *"Next, we'll run our presidential data analyzer.*
> *It analyzed all 45 presidents from `presidents.py` and calculated that the average age upon leaving office is 60.78 years, with Joe Biden as the oldest at age 82 and John F. Kennedy as the youngest at age 46."*

---

#### Step 6: Interactive Human-in-the-Loop Mode
**Type and run:**
```bash
python HW3/agent.py --hitl
```
*(When the banner appears, type `exit` and press Enter)*
> *"Finally, if we launch SecurAgent with `--hitl`, it starts our interactive REPL. In this mode, whenever the agent attempts to run a terminal command or Python code, it halts and asks the user to approve execution with 'y' or provide feedback, giving the human reviewer full control."*

---

### 5. Conclusion

	1	Switch back to VS Code showing HW3/README.md or git log in terminal.

To wrap up:
- We developed SecurAgent incrementally with clean, frequent git commits;
- Added docstrings to all functions and classes;
- Used `uv` to isolate our environment;
- Ensured zero hardcoded secrets;
- And created full documentation in `README.md` and our submission document `hw3-Z23815316.docx`.

Thank you for watching! All of my code and commit history are pushed and available on my GitHub repository.
