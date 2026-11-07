# CyberRAG: Enterprise Security Knowledge & Threat Intelligence Retrieval Engine
### COT4930 — Security Engineering with Generative AI (GenSec) | Homework 06.3
**Student:** Liav Dahari | **FAU ID:** Z23815316  
**Coding Agent:** AntiGravity (Google DeepMind Advanced Agentic Coding Assistant)  
**Repository:** [https://github.com/liavdahari/gensec-code](https://github.com/liavdahari/gensec-code)  
**Live Application:** `http://localhost:8501`

---

## 🎯 Executive Overview

**CyberRAG** is an enterprise-grade cybersecurity Retrieval-Augmented Generation (RAG) system engineered entirely via prompt-driven development with the **AntiGravity** coding agent. CyberRAG empowers security analysts, incident responders, and compliance engineers to query an authoritative knowledge base of industry-standard security frameworks to rapidly triage active threats and generate mathematically grounded, citation-backed security advisories.

### Key Capabilities
- **Authoritative Security Knowledge Base:** 13 pre-indexed documents covering **OWASP Top 10 (2021)**, **MITRE ATT&CK (v14)**, and **NIST Cybersecurity Framework (CSF 2.0)**.
- **Dual-Layer Vector Storage:**
  - *ChromaDB Persistent Store:* Disk-serialized vector database saving to `./hw6/.chroma_db`.
  - *Lightweight Vector Store:* Autonomous TF-IDF term vector engine with $L_2$-normalized cosine similarity and security keyword anchor boosts (zero external network dependencies, 100% offline availability).
- **Grounded Multi-Engine RAG Inference:**
  - *Offline Heuristic Engine:* Deterministic threat synthesis with sub-millisecond latency (0.15 ms) and dynamic risk scoring.
  - *Google Gemini API Engine:* Live cloud LLM synthesis supporting `gemini-2.5-flash` and `gemini-1.5-pro` with anti-hallucination prompt guardrails and automatic offline fallback.
- **Interactive Cyber-Themed Web Application:** Streamlit dark mode interface with one-click threat scenario presets, real-time telemetry metrics, collapsible citation cards, and export to Markdown/JSON.
- **Dynamic Ingestion & Telemetry Audit:** Real-time ingestion supporting dynamic word chunking and session telemetry export.

---

## 🏗️ System Architecture

```
                                  [ User / Security Analyst ]
                                               │
                                               ▼
                              ┌──────────────────────────────────┐
                              │  Streamlit Dark Operations UI    │
                              │  (http://localhost:8501)         │
                              └────────────────┬─────────────────┘
                                               │
                                               ▼
                              ┌──────────────────────────────────┐
                              │    Hybrid Security Retriever     │
                              └────────┬────────────────┬────────┘
                                       │                │
                    ┌──────────────────▼──┐          ┌──▼──────────────────┐
                    │ ChromaDB Persistent │          │ Lightweight Store   │
                    │ Vector Store        │          │ (TF-IDF + Cosine    │
                    │ (./hw6/.chroma_db)  │          │  + Anchor Boosts)   │
                    └─────────────────────┘          └─────────────────────┘
                                       │                │
                                       └────────┬───────┘
                                                │ Ranked Top-K Chunks
                                                ▼
                              ┌──────────────────────────────────┐
                              │    Grounded RAG Inference        │
                              │  ┌─────────────────────────────┐ │
                              │  │ Offline Heuristic Reasoner  │ │
                              │  ├─────────────────────────────┤ │
                              │  │ Google Gemini GenAI API     │ │
                              │  └─────────────────────────────┘ │
                              └────────────────┬─────────────────┘
                                               │
                                               ▼
                              ┌──────────────────────────────────┐
                              │ Synthesized Threat Advisory      │
                              │ • Executive Threat Briefing      │
                              │ • Technical Attack Analysis      │
                              │ • Hardening Checklist [Source:ID]│
                              │ • Markdown & JSON Export         │
                              └──────────────────────────────────┘
```

---

## ⚡ Quickstart & Installation

### 1. Environment Activation
Activate the existing course virtual environment:
```bash
cd "/Users/liavdahari/Documents/FAU FALL 2026/COT4930- GENSEC/gensec-code"
source .venv/bin/activate
```

### 2. Verify Package Dependencies
Verify availability of core libraries:
```bash
python -c "import streamlit, chromadb, google.genai; print('All core libraries verified!')"
```

### 3. Launch Streamlit Web Application
Launch CyberRAG in your local browser:
```bash
streamlit run hw6/app.py
```
*Application opens automatically at `http://localhost:8501`.*

### 4. Run CLI Diagnostic & Verification Test
To run the automated retrieval and RAG synthesis diagnostic test suite in the terminal:
```bash
python hw6/app.py
```

---

## 📚 Indexed Security Knowledge Base

| Framework | Identifier | Title / Attack Vector | Standard Mapping |
| :--- | :--- | :--- | :--- |
| **OWASP Top 10** | `OWASP-A01-BAC` | Broken Access Control & IDOR | CWE-200, CWE-284, CWE-639 |
| **OWASP Top 10** | `OWASP-A02-CRYPTO`| Cryptographic Failures & Broken Ciphers | CWE-310, CWE-327, CWE-328 |
| **OWASP Top 10** | `OWASP-A03-INJECT`| Injection (SQLi, Command Injection, XSS) | CWE-89, CWE-78, CWE-79, CWE-94 |
| **OWASP Top 10** | `OWASP-A07-AUTH`  | Authentication & Session Failures | CWE-287, CWE-384, CWE-798 |
| **OWASP Top 10** | `OWASP-A10-SSRF`  | Server-Side Request Forgery & Cloud IMDS | CWE-918 |
| **MITRE ATT&CK** | `MITRE-T1003-LSASS` | OS Credential Dumping: LSASS Memory | TA0006 (Credential Access) |
| **MITRE ATT&CK** | `MITRE-T1059-INTERP`| Command and Scripting Interpreter (PowerShell) | TA0002 (Execution) |
| **MITRE ATT&CK** | `MITRE-T1078-ACCTS` | Valid Accounts & Cloud Identity Abuse | TA0001, TA0003, TA0005 |
| **MITRE ATT&CK** | `MITRE-T1486-RANSOM`| Data Encrypted for Impact (Ransomware) | TA0040 (Impact) |
| **NIST CSF 2.0** | `NIST-GV-GOVERN`  | GOVERN (GV) - Strategy & Supply Chain | GV.OC, GV.RM, GV.SC |
| **NIST CSF 2.0** | `NIST-PR-PROTECT` | PROTECT (PR) - Safeguards & Zero Trust | PR.AA, PR.DS, PR.PS |
| **NIST CSF 2.0** | `NIST-DE-DETECT`  | DETECT (DE) - Continuous Monitoring & SIEM | DE.CM, DE.AE |
| **NIST CSF 2.0** | `NIST-RS-RESPOND` | RESPOND (RS) - Incident Management & CSIRT | RS.MA, RS.AN, RS.MI |

---

## 📝 Prompt History Log
Every prompt used throughout development is documented in [`hw6/prompts.txt`](prompts.txt):
- **PROMPT 1:** Repository Scaffolding & Initial Remote Push (`initial commit`)
- **PROMPT 2:** Authoritative Security Knowledge Base Corpus (OWASP, MITRE, NIST)
- **PROMPT 3:** Dual-Layer Vector Storage (ChromaDB + Lightweight TF-IDF Store)
- **PROMPT 4:** Grounded RAG Inference Pipeline (Gemini & Autonomous Offline Mode)
- **PROMPT 5:** Streamlit Dark Cybersecurity Operations Web Interface
- **PROMPT 6:** Knowledge Base Explorer, Custom Dynamic Ingestion & Audit Telemetry
