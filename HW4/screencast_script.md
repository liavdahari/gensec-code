# Homework 4 Video Screencast Script (Under 5 Minutes)

**Student:** Liav Dahari (FAU ID: Z23815316)  
**Course:** COT4930 - Security Engineering with Generative AI  
**Assignment:** Homework 4 - Multi-Server Model Context Protocol (MCP) Agent Application  
**Target Duration:** ~4 Minutes (Hard limit: 5 minutes)  

---

## Pre-Recording Checklist (Set this up before hitting Record)

1. **Terminal Setup:**
   - Open a terminal split beside VS Code.
   - Change directory into `HW4` and activate your environment:
     ```bash
     cd HW4
     source .venv/bin/activate
     ```
2. **VS Code Editor Tabs:** Open these tabs in order:
   - Tab 1: `HW4/mcp-server.py`
   - Tab 2: `HW4/agent.py`
   - Tab 3: `HW4/README.md`
3. **Audio/Screen:** Ensure your microphone is clear and your full screen (showing editor, terminal, and code headers with FAU ID **Z23815316**) is in view.

---

## Timed Presentation Script

```
TIMING BREAKDOWN:
0:00 - 0:45  Part 1: Introduction, Student Info & Architecture
0:45 - 1:45  Part 2: Custom FastMCP Security Server (mcp-server.py)
1:45 - 2:30  Part 3: Published Server Integration (Chrome DevTools MCP)
2:30 - 3:45  Part 4: Live Terminal Demonstration & Coordination
3:45 - 4:15  Part 5: Conclusion & Git Tracking Summary
```

---

### Part 1: Introduction & Project Overview (0:00 - 0:45)

**[ON SCREEN: Show `HW4/README.md` or the top of `HW4/agent.py` displaying your student header]**

> "Hi everyone, my name is **Liav Dahari**, FAU ID **Z23815316**. This is my presentation and demonstration for **Homework 4** in **COT4930: Generative AI Security**.
>
> In this assignment, our objective was to build a coordinated **Model Context Protocol (MCP)** agent application by taking what we learned in the `04_MCP` lab exercises and combining two different servers:
> 1. A **published MCP server** integrated from an external repository—specifically Google's official **Chrome DevTools MCP**.
> 2. A **custom MCP server** written in Python using `FastMCP` that provides specialized security audit tools.
> 3. And a **coordinating agent** in `agent.py` that orchestrates both servers across an automated web security pipeline over standard I/O (`stdio`).
>
> All dependencies are managed in an isolated virtual environment using `uv` with `fastmcp`, the official `mcp` SDK, and `requests`."

---

### Part 2: Custom FastMCP Server (`mcp-server.py`) (0:45 - 1:45)

**[ON SCREEN: Switch to `HW4/mcp-server.py` tab. Scroll to the header and tools]**

> "First, let's look at [`mcp-server.py`](file:///Users/liavdahari/Documents/FAU%20FALL%202026/COT4930-%20GENSEC/gensec-code/HW4/mcp-server.py).
>
> **[Highlight Lines 17–19]:**  
> We adopt the FastMCP server foundation demonstrated in `04_MCP/01_sqlite/vulnerable_sqlite_mcp_server.py`. Here at line 18, we initialize:  
> `mcp = FastMCP("Simple-SecOps-Tools")`.
>
> Using the `@mcp.tool()` decorator, we implement three custom security tools:
>
> **[Highlight Lines 21–48]: `check_url_security`**  
> This tool audits a given URL for defensive posture. It checks HTTP status, validates HTTPS enforcement, and evaluates critical headers like `Strict-Transport-Security` (HSTS), `Content-Security-Policy` (CSP), and `X-Frame-Options` to guard against clickjacking and MITM attacks.
>
> **[Highlight Lines 51–75]: `scan_text_for_secrets`**  
> This tool scans extracted page text or DOM content using regex signatures to detect leaked API keys—including Google API keys, OpenAI secret keys, GitHub Personal Access Tokens, and plaintext credential assignments.
>
> **[Highlight Lines 78–109]: `identify_hash_type`**  
> This tool classifies cryptographic password hashes like MD5, SHA-1, SHA-256, and bcrypt, explicitly highlighting deprecated algorithms that are vulnerable to collision attacks.
>
> **[Highlight Line 115]:**  
> Finally, at line 115, the server executes with `mcp.run(transport="stdio")` so our agent can interact with it over standard streams."

---

### Part 3: Published Server Integration & Agent Architecture (`agent.py`) (1:45 - 2:30)

**[ON SCREEN: Switch to `HW4/agent.py` tab]**

> "Next, let's open [`agent.py`](file:///Users/liavdahari/Documents/FAU%20FALL%202026/COT4930-%20GENSEC/gensec-code/HW4/agent.py), which implements the client architecture from `04_MCP/01_sqlite/01_stdio_mcp_client.py`.
>
> **[Highlight Lines 23–44]: `get_server_configs`**  
> Notice how both servers are configured using `StdioServerParameters`:
> - For our published server, we use Google's official `chrome-devtools-mcp` via `npx`, running in headless mode with usage statistics disabled. This gives our agent 32 browser automation tools.
> - For our custom server, we point `sys.executable` directly at our `mcp-server.py`.
>
> **[Highlight Lines 78–125]: `run_security_audit` (Phase 1)**  
> In Phase 1, our agent uses the `stdio_client` and `ClientSession` context managers to connect to Chrome DevTools MCP. It calls `navigate_page` to browse to our target URL (`https://example.com`), and then calls `take_snapshot` to extract a live DOM accessibility text tree.
>
> **[Highlight Lines 127–185]: `run_security_audit` (Phase 2)**  
> In Phase 2, the agent connects to our custom SecOps server and pipes the live data into our defensive tools: auditing the target headers, scanning the extracted DOM text for exposed secrets, and evaluating candidate password hashes."

---

### Part 4: Live Demonstration in Terminal (2:30 - 3:45)

**[ON SCREEN: Focus on the Terminal window]**

> "Now let's see both servers run live.
>
> First, I will run our agent with the `--list-tools` flag to verify both connections:
>
> **[Type and run in terminal]:**
> ```bash
> python agent.py --list-tools
> ```
>
> *(Wait 2 seconds as output prints)*  
> As you can see, our custom SecOps server instantly registers its 3 defensive tools, and the published Chrome DevTools MCP server initializes and exposes all 32 browser automation tools.
>
> Now, let's run the complete coordinated multi-server security audit on `https://example.com`:
>
> **[Type and run in terminal]:**
> ```bash
> python agent.py https://example.com
> ```
>
> *(Narrate as it executes)*:
> - In **Phase 1**, Chrome DevTools MCP starts headless Chrome, navigates to `https://example.com`, and captures an 1,133-byte DOM snapshot.
> - In **Phase 2**, our custom FastMCP server receives the URL and snapshot. 
>   - Tool 1 reports that `https://example.com` returns HTTP 200 with HTTPS, but warns that HSTS and CSP headers are missing.
>   - Tool 2 scans the 1,133 characters of live DOM text and confirms no API keys or credentials were leaked.
>   - Tool 3 tests our candidate hashes, identifying the MD5 hash as insecure and the bcrypt hash as secure.
>
> Both external and custom servers executed and coordinated seamlessly."

---

### Part 5: Conclusion & Submission (3:45 - 4:15)

**[ON SCREEN: Show git log or GitHub repository in browser]**

> "To wrap up:
> - Our development followed an organized, incremental git workflow with distinct commits for environment setup, custom server creation, published server verification, coordinating agent execution, and documentation.
> - All code is documented with PEP 257 docstrings, and no API keys or secrets are stored in the repo.
> - Everything has been committed and pushed to my student GitHub repository at `https://github.com/liavdahari/gensec-code`.
>
> Thank you for watching!"

---

## Quick Teleprompter Sheet (Printable Cue Cards)

| Time | Action | What to Say (Summary) |
| :--- | :--- | :--- |
| **0:00** | Show `README.md` | Introduce self (Liav Dahari, Z23815316), COT4930 HW4 overview, 2 MCP servers coordinated over stdio. |
| **0:45** | Show `mcp-server.py` lines 18–109 | FastMCP pattern from `04_MCP/01_sqlite`. 3 tools: `check_url_security`, `scan_text_for_secrets`, `identify_hash_type`. |
| **1:45** | Show `agent.py` lines 23–185 | Architecture from `01_stdio_mcp_client.py`. `StdioServerParameters` for Chrome DevTools and SecOps. Phase 1 + Phase 2. |
| **2:30** | Run `python agent.py --list-tools` | Point out 3 custom tools + 32 Chrome DevTools automation tools discovered over stdio. |
| **3:00** | Run `python agent.py https://example.com` | Watch live audit: navigate, DOM snapshot, header analysis, secret scanning, hash auditing. |
| **3:45** | Wrap up | Incremental commits, uv isolation, code on GitHub. Thanks. |
