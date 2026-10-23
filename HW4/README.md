# Homework 4: Multi-Server MCP Agent Application

**Course:** COT4930 - Security (System) Engineering with Generative AI  
**Student:** Liav Dahari (FAU ID: Z23815316)  
**Institution:** Florida Atlantic University  

---

## 1. Project Overview

This homework implements a coordinated **Model Context Protocol (MCP)** multi-server agent application that combines:
1. **Published MCP Server (External):** Google Chrome DevTools MCP (`chrome-devtools-mcp`), sourced from MCP Market / GitHub, providing 32 browser automation and inspection tools over `stdio`.
2. **Custom MCP Server (Internal):** [`mcp-server.py`](file:///Users/liavdahari/Documents/FAU%20FALL%202026/COT4930-%20GENSEC/gensec-code/HW4/mcp-server.py) built with `FastMCP`, implementing specialized OWASP defensive security header audits, DOM secret/token leak scanning, and cryptographic hash vulnerability analysis.
3. **Coordinating Agent:** [`agent.py`](file:///Users/liavdahari/Documents/FAU%20FALL%202026/COT4930-%20GENSEC/gensec-code/HW4/agent.py) orchestrates both servers across an automated end-to-end security audit pipeline.

---

## 2. Architecture & Pipeline

```text
               ┌────────────────────────────────────────────────────────┐
               │         Target Webpage (e.g., https://example.com)     │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 HW4/agent.py (Coordinator)                                  │
│                                                                                              │
│   1. Spawns Chrome DevTools MCP via stdio_client()                                           │
│   2. Calls 'navigate_page' with target URL                                                   │
│   3. Calls 'take_snapshot' to extract live DOM accessibility tree                            │
│   4. Spawns Custom SecOps MCP via stdio_client()                                             │
│   5. Calls 'check_url_security' to evaluate HTTPS, HSTS, CSP, and X-Frame-Options            │
│   6. Calls 'scan_text_for_secrets' to detect exposed API keys, tokens, or credentials        │
│   7. Calls 'identify_hash_type' to classify cryptographic hashes & identify weaknesses       │
│   8. Prints structured Security Audit Assessment                                             │
└───────────────────────┬──────────────────────────────────────────────┬───────────────────────┘
                        │                                              │
                        ▼                                              ▼
┌────────────────────────────────────────────────┐   ┌─────────────────────────────────────────┐
│     Published Server: Chrome DevTools MCP      │   │     Custom FastMCP Server: SecOps       │
│                                                │   │                                         │
│ • Subprocess: npx -y chrome-devtools-mcp       │   │ • Subprocess: python mcp-server.py      │
│ • Flags: --headless --no-usage-statistics      │   │ • Framework: FastMCP 3.4.11             │
│ • Exposes 32 browser automation tools          │   │ • Transport: stdio                      │
└────────────────────────────────────────────────┘   └─────────────────────────────────────────┘
```

---

## 3. Custom FastMCP Server Tools (`mcp-server.py`)

- **`check_url_security(url: str) -> dict`**: Audits target URL for HTTPS enforcement and essential defensive HTTP headers (`Strict-Transport-Security`, `Content-Security-Policy`, `X-Frame-Options`).
- **`scan_text_for_secrets(text: str) -> dict`**: Uses regular expression patterns to scan live page text and DOM content for exposed Google API keys, OpenAI/Cloud keys (`sk-...`), GitHub PATs (`ghp_...`), and plaintext credentials.
- **`identify_hash_type(hash_string: str) -> dict`**: Analyzes cryptographic hash formats (MD5, SHA-1, SHA-256, bcrypt) and flags security weaknesses (e.g. deprecated collision-prone MD5/SHA-1 vs. modern salted bcrypt).

---

## 4. Setup and Installation

### Prerequisites
- Python 3.12+
- Node.js (`npx`) installed
- `uv` package manager

### Environment Initialization
```bash
cd HW4
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

---

## 5. Usage & Execution

### Run the Full Coordinated Security Audit
```bash
python agent.py https://example.com
```

### List Discovered Tools Across Both Servers
```bash
python agent.py --list-tools
```

---

## 6. Screencast Video Demonstration

The video demonstration link is documented in [`screencast_url.txt`](file:///Users/liavdahari/Documents/FAU%20FALL%202026/COT4930-%20GENSEC/gensec-code/HW4/screencast_url.txt).
