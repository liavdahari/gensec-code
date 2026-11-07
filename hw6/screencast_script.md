# HW6 Screencast Narration Script

**Course:** COT4930 - Security Engineering with Generative AI (GenSec)  
**Student:** Liav Dahari | **FAU ID:** Z23815316  
**Assignment:** Homework 06.3 - Code Generation with an AI Coding Agent  
**Coding Agent:** AntiGravity (Google DeepMind Advanced Agentic Assistant)  
**Application:** CyberRAG — Enterprise Security Knowledge & Threat Intelligence Retrieval Engine  
**Target Duration:** ~3 to 3.5 minutes (Clear, confident, professional presentation)  

---

## 📋 Pre-Recording Checklist
1. Ensure your face camera is enabled for the introduction and conclusion.
2. Open your browser split-screen:
   - **Left:** MyFAU portal displaying your student credentials: `Hi there! Liav Dahari Z23815316`.
   - **Right:** CyberRAG web application running at `http://localhost:8501`.
3. In VS Code / Terminal, keep `hw6/prompts.txt` and `hw6/app.py` open to show prompt-driven development and git commits.

---

## 🎙️ Presentation Script

### [0:00 - 0:45] Introduction & Assignment Overview
**[Visual: Face camera on, showing MyFAU portal and CyberRAG dashboard]**

> "Hello everyone, my name is **Liav Dahari**, student ID **Z23815316**, and this is my video demonstration for **Homework 06.3** in Security Engineering with Generative AI.
> 
> The goal of this assignment is to build a production-grade cybersecurity Python application driven **strictly by prompts** using an AI coding agent.
> 
> For this project, I partnered with **AntiGravity**, Google DeepMind's advanced agentic coding assistant, to generate **CyberRAG**—an enterprise security knowledge and threat intelligence retrieval engine.
> 
> As you can see on my screen, my FAU credentials are fully visible in the MyFAU student portal, and the application is live and running on localhost port 8501."

---

### [0:45 - 1:30] Prompt-Driven Architecture & Coding Agent Workflow
**[Visual: Switch briefly to VS Code showing `hw6/prompts.txt` and git log in terminal]**

> "CyberRAG was engineered across a strict 6-step prompt sequence recorded in `hw6/prompts.txt`, with each milestone committed and pushed directly to GitHub.
> 
> Our architecture combines three core technical pillars:
> 1. **Authoritative Knowledge Base:** 13 pre-indexed security documents covering OWASP Top 10 vulnerabilities, MITRE ATT&CK techniques, and NIST Cybersecurity Framework 2.0 controls.
> 2. **Dual-Layer Vector Storage:** A persistent **ChromaDB** vector store serialized to `.chroma_db`, backed by a self-contained **Lightweight TF-IDF Vector Store** with cosine distance and security keyword anchor boosts. This guarantees 100% offline availability with zero external API dependencies.
> 3. **Grounded RAG Inference:** An anti-hallucination inference pipeline supporting both live **Google Gemini API** synthesis and an autonomous **Offline Heuristic Reasoner**."

---

### [1:30 - 2:30] Live Demonstration: Threat Incident Triage (Tab 1)
**[Visual: Focus on CyberRAG Tab 1 at `http://localhost:8501`]**

> "Now, let's see CyberRAG in action.
> 
> In **Tab 1: Threat Query & Incident Triage**, security analysts can enter incident symptoms or select one-click presets like SSRF Cloud Exfiltration, LSASS Dumping, or Ransomware response.
> 
> Let's click the **SSRF Cloud Exfil** preset and execute triage.
> 
> In real time, the engine computes:
> - **Retrieval Latency:** Under 5 milliseconds using our hybrid retriever.
> - **Generation Latency:** Sub-millisecond deterministic synthesis in offline mode.
> - **Top Match Relevance:** Over 60% match against OWASP A10 and MITRE T1078.
> 
> Below the telemetry metrics, CyberRAG provides expandable citation cards showing the exact source text, CWE mappings, and tags.
> 
> The synthesized **Threat Advisory** provides an Executive Threat Briefing, Technical Attack Mechanics, and a numbered Prescriptive Hardening Checklist—with every mitigation explicitly cited back to source IDs like `[Source: OWASP-A10-SSRF]`.
> 
> We can also export the full advisory to Markdown or structured JSON with a single click."

---

### [2:30 - 3:15] Knowledge Base Explorer, Custom Ingestion & Telemetry (Tabs 2, 3 & 4)
**[Visual: Click through Tab 2, Tab 3, and Tab 4]**

> "Moving to **Tab 2: Knowledge Base Explorer**, analysts can filter across OWASP, MITRE ATT&CK, and NIST CSF 2.0 to search specific CVEs or mitigation rules.
> 
> In **Tab 3: Custom Ingestion**, teams can ingest custom incident post-mortems or zero-day briefs via raw text or file uploads (.txt, .md, .json). It features **dynamic chunking** that automatically chunks large documents and re-indexes both ChromaDB and the offline store immediately.
> 
> Finally, in **Tab 4: RAG Performance & Audit Log**, every executed triage query is logged with timestamp, latency, grounding score, and top source ID, allowing one-click export for compliance auditing."

---

### [3:15 - 3:35] Conclusion & Submission Verification
**[Visual: Return to face camera with GitHub repository and submission documents visible]**

> "All application code, prompt logs, and configurations have been pushed to my GitHub repository at `github.com/liavdahari/gensec-code`.
> 
> This project demonstrates how pairing with an agentic coding assistant like AntiGravity enables rapid, secure, and rigorously tested software engineering in cybersecurity.
> 
> Thank you for watching!"
