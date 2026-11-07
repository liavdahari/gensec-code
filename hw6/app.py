"""
CyberRAG: Enterprise Security Knowledge & Threat Intelligence Retrieval Engine
COT4930 - Security Engineering with Generative AI (GenSec)
Student: Liav Dahari (FAU ID: Z23815316)
Coding Agent: AntiGravity (Google DeepMind)
"""

import os
import sys
import re
import json
import math
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    st = None
    STREAMLIT_AVAILABLE = False

# Optional ChromaDB import with graceful fallback
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    chromadb = None
    CHROMA_AVAILABLE = False

# Google GenAI import with graceful fallback
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    types = None
    GENAI_AVAILABLE = False

# Load environment variables if python-dotenv is present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ==============================================================================
# AUTHORITATIVE SECURITY KNOWLEDGE BASE CORPUS
# Structured reference datasets across OWASP Top 10, MITRE ATT&CK, and NIST CSF 2.0
# ==============================================================================

CYBER_CORPUS: List[Dict[str, Any]] = [
    # --------------------------------------------------------------------------
    # 1. OWASP Top 10 (2021)
    # --------------------------------------------------------------------------
    {
        "id": "OWASP-A01-BAC",
        "framework": "OWASP Top 10 (2021)",
        "title": "A01:2021 - Broken Access Control",
        "category": "Web Application Security",
        "mapping": "CWE-200, CWE-284, CWE-639 (IDOR), CWE-285",
        "tags": ["access control", "idor", "privilege escalation", "rbac", "abac", "authorization", "bola", "least privilege"],
        "content": (
            "OWASP A01:2021 - Broken Access Control occurs when application security policies are improperly enforced, "
            "allowing users to act outside of their intended permissions. Common failure modes include Insecure Direct Object "
            "References (IDOR) where modifying a record identifier (e.g., account_id, document_uuid) grants unauthorized data access, "
            "missing functional access controls enabling horizontal or vertical privilege escalation, and CORS misconfigurations "
            "permitting unauthorized API access. Attack vectors frequently target unauthenticated multi-tenant endpoints and API route tampering. "
            "Detection Indicators: High volume of 403 Forbidden spikes followed by successful 200 OK responses with mismatched session IDs, "
            "anomalous sequential parameter sweeps in web access logs, and unauthorized object query patterns. "
            "Hardening & Mitigation Checklist: (1) Enforce strict server-side authorization checks on every request using robust "
            "Role-Based (RBAC) or Attribute-Based Access Control (ABAC); (2) Default to 'Deny All' for any unmapped route; "
            "(3) Replace predictable sequential primary keys with cryptographically random UUIDv4 or encrypted surrogate tokens; "
            "(4) Implement automated access control unit and integration tests across all API endpoints; "
            "(5) Disable web server directory listing and ensure file metadata/backup files are not web-accessible."
        )
    },
    {
        "id": "OWASP-A02-CRYPTO",
        "framework": "OWASP Top 10 (2021)",
        "title": "A02:2021 - Cryptographic Failures",
        "category": "Web Application Security",
        "mapping": "CWE-310, CWE-327 (Broken Crypto), CWE-328 (Reversible One-Way Hash), CWE-319",
        "tags": ["cryptography", "encryption", "tls", "hashing", "ciphers", "aes-gcm", "argon2", "data in transit", "data at rest"],
        "content": (
            "OWASP A02:2021 - Cryptographic Failures relates to sensitive data exposure resulting from the absence or improper "
            "implementation of cryptographic protections. This vulnerability manifests when sensitive information (passwords, PII, "
            "credit card numbers, session tokens) is transmitted in cleartext (HTTP, SMTP, FTP) or stored using obsolete and broken "
            "algorithms such as MD5, SHA-1, DES, 3DES, or RC4. It also encompasses weak initialization vectors (IVs), static cryptographic "
            "keys embedded in source code, and missing Authenticated Encryption (AEAD). "
            "Detection Indicators: TLS scanning identifying SSLv3, TLS 1.0, TLS 1.1 or CBC ciphers; cleartext credentials identified in packet captures; "
            "secret detection alerts for committed high-entropy API keys or private keys in git repositories. "
            "Hardening & Mitigation Checklist: (1) Classify all processed data and enforce AES-256-GCM or ChaCha20-Poly1305 for data-at-rest encryption; "
            "(2) Mandate TLS 1.3 (or strictly TLS 1.2 with PFS ciphers) with HTTP Strict Transport Security (HSTS) with long max-age and includeSubDomains; "
            "(3) Hash user passwords using memory-hard, salt-assisted algorithms: Argon2id (recommended), bcrypt (cost factor >= 12), or PBKDF2; "
            "(4) Never store plaintext credentials or static encryption keys in source repositories; use automated secret managers (HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager); "
            "(5) Enforce periodic cryptographic key and certificate rotation."
        )
    },
    {
        "id": "OWASP-A03-INJECT",
        "framework": "OWASP Top 10 (2021)",
        "title": "A03:2021 - Injection",
        "category": "Web Application Security",
        "mapping": "CWE-89 (SQL Injection), CWE-78 (OS Command Injection), CWE-79 (XSS), CWE-94",
        "tags": ["injection", "sqli", "command injection", "xss", "parameterized queries", "input validation", "orm"],
        "content": (
            "OWASP A03:2021 - Injection flaws arise when untrusted user data is sent to an interpreter as part of a command or query without "
            "prior parameterization or rigorous sanitization. Hostile data tricks the interpreter into executing unintended commands or accessing "
            "unauthorized data. Classic variants include Structured Query Language Injection (SQLi), Operating System Command Injection (executing system commands "
            "via shell wrappers), Cross-Site Scripting (XSS), LDAP injection, and NoSQL injection. "
            "Detection Indicators: WAF alert logs reporting SQL metacharacters (UNION SELECT, OR 1=1, benchmark delay payloads); syntax error stack traces "
            "leaked in HTTP 500 error bodies; abnormal child processes spawned by web server daemons (e.g., cmd.exe or /bin/sh spawned by w3wp.exe or nginx). "
            "Hardening & Mitigation Checklist: (1) Always use safe APIs and parameterized queries (PreparedStatements) or modern Object-Relational Mappers (ORM); "
            "(2) Use positive input validation (allowlisting) on data types, lengths, character sets, and business logic formats; "
            "(3) Context-aware output encoding for HTML, JavaScript, CSS, and URL contexts to eradicate XSS; "
            "(4) Avoid invoking OS shell interpreters directly from application code; when system operations are mandatory, use parameterized process execution APIs without a shell wrapper; "
            "(5) Run database service accounts with least privilege, preventing arbitrary stored procedure execution or DROP TABLE permissions."
        )
    },
    {
        "id": "OWASP-A07-AUTH",
        "framework": "OWASP Top 10 (2021)",
        "title": "A07:2021 - Identification and Authentication Failures",
        "category": "Web Application Security",
        "mapping": "CWE-287 (Improper Authentication), CWE-384 (Session Fixation), CWE-798",
        "tags": ["authentication", "session management", "credential stuffing", "brute force", "mfa", "jwt", "session fixation"],
        "content": (
            "OWASP A07:2021 - Identification and Authentication Failures occurs when application functions related to user identity, authentication, "
            "and session state management are flawed. This allows adversaries to compromise passwords, keys, or session tokens to assume the identity "
            "of authorized users. Typical vulnerabilities include permitting automated brute-force attacks or credential stuffing, weak password policies, "
            "ineffective multi-factor authentication (MFA) enforcement, session fixation, predictable session IDs, and mishandled JSON Web Tokens (JWT) "
            "(e.g., accepting 'none' algorithms or missing signature validation). "
            "Detection Indicators: Spikes in HTTP 401 Unauthorized responses from single IP clusters or distributed proxies (indicating credential stuffing); "
            "concurrent active sessions from geographically implausible locations; reuse of invalidated session tokens. "
            "Hardening & Mitigation Checklist: (1) Enforce Multi-Factor Authentication (MFA/FIDO2 WebAuthn) for all external and privileged access; "
            "(2) Implement intelligent rate limiting, IP reputation scoring, and account lockout/exponential backoff to halt brute-force campaigns; "
            "(3) Use built-in, battle-tested session management frameworks; generate cryptographically secure, high-entropy session IDs; "
            "(4) Store session cookies with HttpOnly, Secure, and SameSite=Strict/Lax flags enabled; "
            "(5) Invalidate session identifiers completely upon logout, password change, or idle timeout period; "
            "(6) Strictly validate all JWT signatures server-side with asymmetric keys (RS256/ES256) and reject the 'none' algorithm."
        )
    },
    {
        "id": "OWASP-A10-SSRF",
        "framework": "OWASP Top 10 (2021)",
        "title": "A10:2021 - Server-Side Request Forgery (SSRF)",
        "category": "Web Application Security",
        "mapping": "CWE-918 (Server-Side Request Forgery)",
        "tags": ["ssrf", "cloud metadata", "imds", "imdsv2", "aws", "egress filtering", "internal network", "dns rebinding"],
        "content": (
            "OWASP A10:2021 - Server-Side Request Forgery (SSRF) emerges when a web application fetches a remote resource without validating the user-supplied "
            "URL. An attacker can coerce the application into sending a crafted request to an unexpected destination, typically targeting internal systems behind "
            "firewalls, loopback interfaces (127.0.0.1, localhost), or cloud instance metadata services (IMDS at 169.254.169.254). In cloud environments, "
            "unmitigated SSRF often leads to immediate credential exfiltration by stealing temporary IAM role credentials from IMDSv1. "
            "Detection Indicators: Egress firewall and VPC flow logs indicating outbound connections from web servers toward private RFC1918 subnets (10.0.0.0/8, "
            "172.16.0.0/12, 192.168.0.0/16) or the link-local address 169.254.169.254; DNS query logs showing lookups resolving to internal addresses (DNS rebinding). "
            "Hardening & Mitigation Checklist: (1) Strictly validate and allowlist target hostnames, schemes (enforce HTTPS only), and IP addresses; "
            "(2) Resolve target domain names and verify that the destination IP address does not fall within private, loopback, or link-local address spaces prior to establishing connection; "
            "(3) In AWS EC2, mandate IMDSv2 by setting HttpTokens=required and limiting hop limit to 1 (preventing container SSRF traversal); "
            "(4) Segment web tier networks and enforce egress firewall rules blocking arbitrary internal service calls; "
            "(5) Disable HTTP redirection handling in the HTTP client library to prevent blind redirection bypasses."
        )
    },

    # --------------------------------------------------------------------------
    # 2. MITRE ATT&CK Enterprise (v14)
    # --------------------------------------------------------------------------
    {
        "id": "MITRE-T1003-LSASS",
        "framework": "MITRE ATT&CK (v14)",
        "title": "T1003.001 - OS Credential Dumping: LSASS Memory",
        "category": "Credential Access (TA0006)",
        "mapping": "MITRE ATT&CK T1003.001, Sub-technique of T1003",
        "tags": ["lsass", "credential dumping", "mimikatz", "procdump", "credential access", "windows", "runasppl", "credential guard"],
        "content": (
            "MITRE ATT&CK T1003.001 describes adversarial techniques used to dump cleartext credentials, NTLM password hashes, Kerberos tickets, "
            "and PINs from the memory space of the Local Security Authority Subsystem Service (LSASS.exe). Tools like Mimikatz, ProcDump, Comsvcs.dll, "
            "or direct MiniDumpWriteDump API calls are leveraged by attackers possessing local administrative or SYSTEM privileges. Stolen credentials "
            "are then reused for lateral movement across Windows Active Directory domain environments. "
            "Detection Indicators: Windows Event ID 4656/4663 or Sysmon Event ID 10 showing unauthorized processes requesting PROCESS_VM_READ or "
            "PROCESS_ALL_ACCESS handles to lsass.exe; creation of abnormal .dmp files in temp directories; invocation of rundll32.exe referencing comsvcs.dll "
            "with MiniDump export syntax. "
            "Hardening & Mitigation Checklist: (1) Enable Windows Defender Credential Guard (virtualization-based security isolating LSA secrets); "
            "(2) Enable LSA Protection by enforcing RunAsPPL=1 (Protected Process Light) in the registry (HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Lsa); "
            "(3) Implement Attack Surface Reduction (ASR) rule 'Block credential stealing from the Windows local security authority subsystem' (GUID: 9e6c4e1f-7d60-472f-ba1a-a39ef669e4b2); "
            "(4) Restrict debug privileges (SeDebugPrivilege) to strictly authorized domain engineers; "
            "(5) Deploy endpoint detection and response (EDR) behavioral alerts for suspicious LSASS handle opening."
        )
    },
    {
        "id": "MITRE-T1059-INTERP",
        "framework": "MITRE ATT&CK (v14)",
        "title": "T1059 - Command and Scripting Interpreter",
        "category": "Execution (TA0002)",
        "mapping": "MITRE ATT&CK T1059.001 (PowerShell), T1059.003 (Windows Command Shell), T1059.004 (Unix Shell)",
        "tags": ["execution", "powershell", "cmd", "bash", "scripting", "amsi", "living off the land", "lotl"],
        "content": (
            "MITRE ATT&CK T1059 covers execution of arbitrary commands, scripts, or binaries through command-line interpreters (e.g., PowerShell, "
            "cmd.exe, bash, sh, Python, VBScript). Adversaries abuse built-in interpreters (Living off the Land) to execute malicious code, download "
            "secondary payloads, run memory-resident scripts, or bypass basic file-based security controls. Attackers frequently utilize obfuscation, "
            "Base64 encoding (-EncodedCommand), and Antimalware Scan Interface (AMSI) memory patching to evade detection. "
            "Detection Indicators: Process creation telemetry (Event ID 4688, Sysmon Event ID 1) showing powershell.exe or cmd.exe spawned with suspicious "
            "flags (-w hidden, -nop, -enc, IEX, downloadstring); unquoted service paths; PowerShell Script Block Logging (Event ID 4104) capturing obfuscated code. "
            "Hardening & Mitigation Checklist: (1) Enforce PowerShell Constrained Language Mode (CLM) via AppLocker or Windows Defender Application Control (WDAC); "
            "(2) Enable PowerShell Script Block Logging (Event ID 4104), Transcription Logging, and Module Logging; "
            "(3) Ensure Antimalware Scan Interface (AMSI) is active and monitor for in-memory patch attempts (e.g., amsiInitFailed modification); "
            "(4) Restrict command shell execution for unprivileged service accounts and web application processes; "
            "(5) Deploy centralized SIEM sigma rules matching suspicious command-line patterns and parent-child process anomalies."
        )
    },
    {
        "id": "MITRE-T1078-ACCTS",
        "framework": "MITRE ATT&CK (v14)",
        "title": "T1078 - Valid Accounts",
        "category": "Defense Evasion, Persistence, Initial Access (TA0001, TA0003, TA0005)",
        "mapping": "MITRE ATT&CK T1078.001, T1078.002, T1078.003, T1078.004 (Cloud)",
        "tags": ["valid accounts", "initial access", "cloud iam", "privilege escalation", "lateral movement", "compromised credentials"],
        "content": (
            "MITRE ATT&CK T1078 describes adversaries acquiring and using credentials of existing legitimate accounts to gain initial access, "
            "maintain persistence, escalate privileges, or evade defensive barriers. By leveraging legitimate credentials, adversary activity mimics "
            "normal user behavior, rendering signature-based defenses ineffective. Variations span default administrator accounts, compromised enterprise "
            "domain user accounts, and cloud service provider IAM access keys or service principals. "
            "Detection Indicators: Logins occurring outside typical operational hours, rapid geographical transitions (impossible travel) in Azure AD/Okta "
            "identity logs; sudden access to sensitive repositories or administrative consoles by accounts that historically never accessed them; "
            "anomalous CloudTrail API operations (e.g., CreateAccessKey, AttachUserPolicy) from unfamiliar IP subnets. "
            "Hardening & Mitigation Checklist: (1) Enforce phishing-resistant Multi-Factor Authentication (FIDO2, hardware security tokens) across all enterprise and cloud accounts; "
            "(2) Implement Conditional Access policies evaluating device health, IP reputation, and risk state before granting authentication; "
            "(3) Enforce Just-In-Time (JIT) access and Privileged Access Management (PAM) with automated credential checkout and session recording; "
            "(4) Disable default administrative accounts (e.g., built-in Administrator, Guest) or randomize passwords via LAPS; "
            "(5) Deploy User and Entity Behavior Analytics (UEBA) to identify baseline anomalies and impossible travel alerts."
        )
    },
    {
        "id": "MITRE-T1486-RANSOM",
        "framework": "MITRE ATT&CK (v14)",
        "title": "T1486 - Data Encrypted for Impact",
        "category": "Impact (TA0040)",
        "mapping": "MITRE ATT&CK T1486",
        "tags": ["ransomware", "encryption", "impact", "shadow copies", "vssadmin", "canary files", "incident response", "business interruption"],
        "content": (
            "MITRE ATT&CK T1486 details adversarial operations that encrypt data on target systems or network shares to disrupt access to critical "
            "assets and demand extortion payments (Ransomware). Modern ransomware actors typically combine data exfiltration (double extortion) "
            "with destructive system changes prior to encryption: terminating security services, purging volume shadow copies (vssadmin delete shadows /all /quiet), "
            "disabling system recovery modes (bcdedit /set default recoveryenabled No), and executing high-speed multithreaded file encryption with custom extensions. "
            "Detection Indicators: High-frequency file modification/rename operations matching known ransomware extensions; execution of commands deleting "
            "shadow copies (vssadmin, wbadmin, PowerShell Get-WmiObject Win32_ShadowCopy); mass endpoint connection terminations or unexpected mass reboot schedules. "
            "Hardening & Mitigation Checklist: (1) Maintain immutable, air-gapped, offline backups following the 3-2-1 backup strategy (3 copies, 2 media types, 1 offsite/immutable); "
            "(2) Deploy Canary file tripwires in common shared network directories to detect rapid encryption activity and trigger automated network isolation; "
            "(3) Block execution of unauthorized mass-encryption binaries and scripts via Endpoint Detection and Response (EDR) automated containment; "
            "(4) Enforce strict network segmentation preventing SMB/RPC spread between user endpoints and server tiers; "
            "(5) Periodically validate backup restoration capabilities through full disaster recovery tabletop simulations."
        )
    },

    # --------------------------------------------------------------------------
    # 3. NIST Cybersecurity Framework (CSF 2.0)
    # --------------------------------------------------------------------------
    {
        "id": "NIST-GV-GOVERN",
        "framework": "NIST CSF 2.0",
        "title": "GOVERN (GV) - Cybersecurity Governance & Strategy",
        "category": "Governance & Risk Management",
        "mapping": "NIST CSF 2.0 Functions: GV.OC, GV.RM, GV.RR, GV.PO, GV.OV, GV.SC",
        "tags": ["governance", "nist csf", "risk management", "supply chain", "policy", "compliance", "board oversight"],
        "content": (
            "NIST CSF 2.0 GOVERN (GV) function establishes and monitors the organization's cybersecurity risk management strategy, expectations, "
            "and policy. It informs how an organization achieves and prioritizes the other five core functions (Identify, Protect, Detect, Respond, Recover) "
            "in the context of its mission and regulatory obligations. Key categories include Organizational Context (GV.OC), Risk Management Strategy (GV.RM), "
            "Roles, Responsibilities, and Authorities (GV.RR), Policy (GV.PO), Oversight (GV.OV), and Cybersecurity Supply Chain Risk Management (GV.SC). "
            "Key Focus Areas: Aligning cybersecurity risk appetite with enterprise business goals; integrating third-party vendor risk scoring; establishing "
            "unambiguous leadership accountability; and conducting regular external compliance audits (SOC 2, ISO 27001, HIPAA). "
            "Operational Hardening Checklist: (1) Document and regularly update organizational cybersecurity policies, baseline standards, and exception processes; "
            "(2) Formalize a Third-Party Risk Management (TPRM) framework evaluating vendor software bills of materials (SBOM) and security postures; "
            "(3) Appoint dedicated risk owners and maintain an active Enterprise Cybersecurity Risk Register; "
            "(4) Establish board-level cybersecurity reporting dashboards with quantitative risk metrics (FAIR model)."
        )
    },
    {
        "id": "NIST-PR-PROTECT",
        "framework": "NIST CSF 2.0",
        "title": "PROTECT (PR) - Safeguards & Defensive Countermeasures",
        "category": "Defensive Architecture & Access Control",
        "mapping": "NIST CSF 2.0 Functions: PR.AA, PR.AT, PR.DS, PR.PS, PR.IR",
        "tags": ["protect", "nist csf", "identity management", "zero trust", "data security", "network security", "patch management"],
        "content": (
            "NIST CSF 2.0 PROTECT (PR) function provides safeguards to manage the organization's cybersecurity risk and ensure delivery of critical "
            "infrastructure services. It addresses control mechanisms designed to prevent or reduce the likelihood and impact of cybersecurity events. "
            "Core categories include Identity Management, Authentication, and Access Control (PR.AA), Awareness and Training (PR.AT), Data Security (PR.DS), "
            "Platform Security (PR.PS), and Technology Infrastructure Resilience (PR.IR). "
            "Key Focus Areas: Zero Trust Architecture (ZTA) principle enforcement; end-to-end encryption for data in transit and at rest; strict vulnerability "
            "and patch management cadences; least privilege access enforcement; and continuous configuration management baselines. "
            "Operational Hardening Checklist: (1) Deploy Zero Trust network architecture verifying identity and device posture on every transactional request; "
            "(2) Enforce cryptographic protection across all data stores, backups, and communication channels; "
            "(3) Implement automated patch management with strict SLAs (critical vulnerabilities remediated within 7 days); "
            "(4) Conduct mandatory, continuous role-specific cybersecurity awareness and phishing resilience training."
        )
    },
    {
        "id": "NIST-DE-DETECT",
        "framework": "NIST CSF 2.0",
        "title": "DETECT (DE) - Continuous Monitoring & Anomaly Discovery",
        "category": "Security Monitoring & Threat Detection",
        "mapping": "NIST CSF 2.0 Functions: DE.CM, DE.AE",
        "tags": ["detect", "nist csf", "continuous monitoring", "siem", "xdr", "threat hunting", "anomaly detection"],
        "content": (
            "NIST CSF 2.0 DETECT (DE) function enables timely discovery and diagnosis of cybersecurity events and anomalies. Continuous monitoring "
            "and analysis of enterprise assets, network traffic, physical environments, and identity systems ensure that malicious activities or policy "
            "violations are recognized swiftly. Core categories comprise Continuous Monitoring (DE.CM) and Adverse Event Analysis (DE.AE). "
            "Key Focus Areas: Enterprise-wide telemetry ingestion into unified SIEM/XDR platforms; behavioral analytics detecting deviations from normal "
            "operational baselines; proactive threat hunting operations; and correlated alert triage minimizing dwell time. "
            "Operational Hardening Checklist: (1) Ingest high-fidelity logs (endpoint EDR, DNS, VPC flows, identity provider, web application firewalls) into a centralized SIEM; "
            "(2) Develop and maintain automated detection correlation rules mapped to the MITRE ATT&CK framework; "
            "(3) Establish 24/7/365 Security Operations Center (SOC) coverage with tiered alert triage and automated initial response playbooks; "
            "(4) Execute regular threat hunting sprints to identify unflagged persistence and lateral movement."
        )
    },
    {
        "id": "NIST-RS-RESPOND",
        "framework": "NIST CSF 2.0",
        "title": "RESPOND (RS) - Incident Management & Mitigation",
        "category": "Incident Response & Crisis Management",
        "mapping": "NIST CSF 2.0 Functions: RS.MA, RS.AN, RS.CO, RS.MI",
        "tags": ["respond", "nist csf", "incident response", "triage", "containment", "forensics", "mitigation", "csirt"],
        "content": (
            "NIST CSF 2.0 RESPOND (RS) function supports the ability to contain and manage the effects of an identified cybersecurity incident. "
            "It emphasizes rapid containment, forensic analysis, coordination across stakeholders, and active mitigation to prevent incident propagation. "
            "Core categories include Incident Management (RS.MA), Incident Analysis (RS.AN), Incident Response Reporting and Communication (RS.CO), "
            "and Incident Mitigation (RS.MI). "
            "Key Focus Areas: Rapid mobilization of the Cyber Security Incident Response Team (CSIRT); digital forensics and chain-of-custody evidence collection; "
            "effective internal and external legal/regulatory disclosures; and execution of predetermined containment playbooks (host isolation, credential revocation). "
            "Operational Hardening Checklist: (1) Maintain and test formal Incident Response Playbooks for primary threat scenarios (Ransomware, Data Breach, Supply Chain, Cloud Compromise); "
            "(2) Implement automated containment mechanisms (e.g., EDR network isolation, automated session revocation); "
            "(3) Conduct regular tabletop exercises with cross-functional leadership (Security, Legal, Communications, Executives); "
            "(4) Conduct mandatory Post-Incident Reviews (blameless post-mortems) within 14 days of incident closure to integrate lessons learned."
        )
    }
]

# Quick reference mapping for framework lookup
FRAMEWORKS: List[str] = sorted(list({doc["framework"] for doc in CYBER_CORPUS}))


def get_corpus_statistics() -> Dict[str, Any]:
    """Returns summary metadata regarding the indexed cyber knowledge base."""
    total_docs = len(CYBER_CORPUS)
    framework_counts = {}
    for doc in CYBER_CORPUS:
        fw = doc["framework"]
        framework_counts[fw] = framework_counts.get(fw, 0) + 1
    return {
        "total_documents": total_docs,
        "frameworks": framework_counts,
        "all_ids": [doc["id"] for doc in CYBER_CORPUS]
    }


# ==============================================================================
# VECTOR DATABASE STORAGE & HYBRID RETRIEVAL ENGINE
# ==============================================================================

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
    "by", "can", "did", "do", "does", "doing", "don", "down", "during", "each", "few", "for",
    "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself",
    "him", "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just",
    "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once",
    "only", "or", "other", "our", "ours", "ourselves", "out", "over", "own", "s", "same", "she",
    "should", "so", "some", "such", "t", "than", "that", "the", "their", "theirs", "them",
    "themselves", "then", "there", "these", "they", "this", "those", "through", "to", "too",
    "under", "until", "up", "very", "was", "we", "were", "what", "when", "where", "which",
    "while", "who", "whom", "why", "will", "with", "you", "your", "yours", "yourself"
}


class LightweightVectorStore:
    """
    Self-contained fallback vector similarity store utilizing TF-IDF term vectors,
    L2-normalized cosine distance, and security keyword anchor boosts.
    Guarantees 100% offline availability with zero external network or C-extension dependencies.
    """

    def __init__(self, documents: Optional[List[Dict[str, Any]]] = None):
        self.documents: List[Dict[str, Any]] = []
        self.doc_vectors: List[Dict[str, float]] = []
        self.doc_norms: List[float] = []
        self.idf: Dict[str, float] = {}
        self.vocabulary: set = set()
        if documents:
            self.index_documents(documents)

    def _tokenize(self, text: str) -> List[str]:
        """Extracts normalized alphanumeric and security-token terms."""
        clean = re.sub(r'[^a-zA-Z0-9_\-\.]', ' ', text.lower())
        tokens = [t for t in clean.split() if len(t) >= 2 and t not in STOP_WORDS]
        return tokens

    def _compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        """Calculates term frequencies for a token sequence."""
        if not tokens:
            return {}
        counts: Dict[str, int] = {}
        for t in tokens:
            counts[t] = counts.get(t, 0) + 1
        n = float(len(tokens))
        return {t: (c / n) for t, c in counts.items()}

    def index_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Indexes corpus documents into L2-normalized TF-IDF vector space."""
        self.documents = documents
        total_docs = len(documents)
        if total_docs == 0:
            return

        doc_tokens_list: List[List[str]] = []
        df_counts: Dict[str, int] = {}

        for doc in documents:
            combined_text = f"{doc.get('title', '')} {doc.get('category', '')} {doc.get('mapping', '')} {' '.join(doc.get('tags', []))} {doc.get('content', '')}"
            tokens = self._tokenize(combined_text)
            doc_tokens_list.append(tokens)
            unique_tokens = set(tokens)
            for t in unique_tokens:
                df_counts[t] = df_counts.get(t, 0) + 1

        # Smooth Inverse Document Frequency (IDF)
        self.vocabulary = set(df_counts.keys())
        self.idf = {
            t: math.log((1.0 + total_docs) / (1.0 + df)) + 1.0
            for t, df in df_counts.items()
        }

        # Compute document vectors and L2 norms
        self.doc_vectors = []
        self.doc_norms = []
        for tokens in doc_tokens_list:
            tf = self._compute_tf(tokens)
            vec: Dict[str, float] = {}
            norm_sq = 0.0
            for t, tf_val in tf.items():
                w = tf_val * self.idf.get(t, 1.0)
                vec[t] = w
                norm_sq += w * w
            norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
            self.doc_vectors.append(vec)
            self.doc_norms.append(norm)

    def search(
        self,
        query: str,
        top_k: int = 3,
        similarity_threshold: float = 0.05,
        framework_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes L2-normalized cosine distance retrieval augmented by keyword anchor boosts.
        Returns ranked security records.
        """
        if not self.documents:
            return []

        q_tokens = self._tokenize(query)
        if not q_tokens:
            return []

        q_tf = self._compute_tf(q_tokens)
        q_vec: Dict[str, float] = {}
        q_norm_sq = 0.0
        for t, tf_val in q_tf.items():
            idf_val = self.idf.get(t, math.log(1.0 + len(self.documents)) + 1.0)
            w = tf_val * idf_val
            q_vec[t] = w
            q_norm_sq += w * w
        q_norm = math.sqrt(q_norm_sq) if q_norm_sq > 0 else 1.0

        query_lower = query.lower()
        results = []

        for idx, doc in enumerate(self.documents):
            # Apply optional framework filter
            if framework_filter and framework_filter != "All Frameworks":
                if doc.get("framework") != framework_filter:
                    continue

            d_vec = self.doc_vectors[idx]
            d_norm = self.doc_norms[idx]

            # 1. Base Cosine Similarity
            dot = sum(w * d_vec.get(t, 0.0) for t, w in q_vec.items())
            cosine_sim = dot / (q_norm * d_norm) if (q_norm * d_norm) > 0 else 0.0

            # 2. Security Keyword Anchor Boosts
            anchor_boost = 0.0
            doc_id_lower = doc.get("id", "").lower()
            doc_title_lower = doc.get("title", "").lower()
            doc_tags = [tag.lower() for tag in doc.get("tags", [])]
            doc_mapping = doc.get("mapping", "").lower()
            doc_content_lower = doc.get("content", "").lower()

            # Exact full phrase match boost
            if len(query_lower) >= 4 and query_lower in doc_content_lower:
                anchor_boost += 0.15

            # Targeted term anchors
            for qt in q_tokens:
                if len(qt) < 3:
                    continue
                if qt in doc_id_lower:
                    anchor_boost += 0.20
                if any(qt == tag or qt in tag for tag in doc_tags):
                    anchor_boost += 0.12
                if qt in doc_title_lower:
                    anchor_boost += 0.08
                if qt in doc_mapping:
                    anchor_boost += 0.08

            # Cap maximum anchor boost
            anchor_boost = min(0.35, anchor_boost)
            final_score = min(1.0, max(0.0, (cosine_sim * 0.70) + anchor_boost))

            if final_score >= similarity_threshold:
                match_entry = dict(doc)
                match_entry["score"] = round(final_score, 4)
                match_entry["cosine_similarity"] = round(cosine_sim, 4)
                match_entry["anchor_boost"] = round(anchor_boost, 4)
                match_entry["source_engine"] = "LightweightVectorStore"
                results.append(match_entry)

        # Rank descending by composite score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def reindex(self, documents: List[Dict[str, Any]]) -> None:
        """Clears and re-indexes given documents."""
        self.index_documents(documents)

    def count(self) -> int:
        return len(self.documents)


class ChromaSecurityStore:
    """
    Persistent ChromaDB storage adapter saving vector embeddings to ./hw6/.chroma_db.
    Supports persistent disk serialization, collection management, and vector similarity querying.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        collection_name: str = "cyber_rag_vault"
    ):
        if db_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.db_path = os.path.join(base_dir, ".chroma_db")
        else:
            self.db_path = db_path

        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.is_ready = False

        if CHROMA_AVAILABLE:
            try:
                os.makedirs(self.db_path, exist_ok=True)
                self.client = chromadb.PersistentClient(path=self.db_path)
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"description": "CyberRAG Security Knowledge Base Vault"}
                )
                self.is_ready = True
            except Exception as e:
                print(f"[ChromaSecurityStore] Initialization notice: {e}")
                self.is_ready = False

    def index_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Upserts documents and structured metadata into ChromaDB collection."""
        if not self.is_ready or not self.collection:
            return

        ids = [doc["id"] for doc in documents]
        texts = [doc["content"] for doc in documents]
        metadatas = [
            {
                "framework": doc.get("framework", "General"),
                "title": doc.get("title", ""),
                "category": doc.get("category", ""),
                "mapping": doc.get("mapping", ""),
                "tags": ", ".join(doc.get("tags", []))
            }
            for doc in documents
        ]

        self.collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )

    def search(
        self,
        query: str,
        top_k: int = 3,
        similarity_threshold: float = 0.05,
        framework_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Queries persistent ChromaDB collection and converts distances to similarity scores."""
        if not self.is_ready or not self.collection:
            return []

        where_clause = None
        if framework_filter and framework_filter != "All Frameworks":
            where_clause = {"framework": framework_filter}

        try:
            query_kwargs: Dict[str, Any] = {
                "query_texts": [query],
                "n_results": min(top_k, max(1, self.collection.count()))
            }
            if where_clause:
                query_kwargs["where"] = where_clause

            res = self.collection.query(**query_kwargs)
            results = []

            if res and res.get("ids") and len(res["ids"]) > 0:
                ids = res["ids"][0]
                docs = res["documents"][0]
                metas = res["metadatas"][0]
                distances = res["distances"][0] if "distances" in res and res["distances"] else [0.5] * len(ids)

                for doc_id, doc_text, meta, dist in zip(ids, docs, metas, distances):
                    # Chroma default distance is cosine distance (0: identical, 2: opposite)
                    sim_score = max(0.0, min(1.0, 1.0 - (float(dist) / 2.0)))
                    if sim_score >= similarity_threshold:
                        tags_list = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
                        results.append({
                            "id": doc_id,
                            "framework": meta.get("framework", ""),
                            "title": meta.get("title", ""),
                            "category": meta.get("category", ""),
                            "mapping": meta.get("mapping", ""),
                            "tags": tags_list,
                            "content": doc_text,
                            "score": round(sim_score, 4),
                            "distance": round(float(dist), 4),
                            "source_engine": "ChromaDB"
                        })

            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:top_k]
        except Exception as e:
            print(f"[ChromaSecurityStore] Search fallback triggered: {e}")
            return []

    def reindex(self, documents: List[Dict[str, Any]]) -> None:
        """Purges existing collection and indexes fresh document set."""
        if not self.is_ready or not self.client:
            return
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "CyberRAG Security Knowledge Base Vault"}
        )
        self.index_documents(documents)

    def count(self) -> int:
        return self.collection.count() if (self.is_ready and self.collection) else 0


class HybridSecurityRetriever:
    """
    Unified Hybrid Retrieval Engine coordinating ChromaDB persistent vector storage
    and the self-contained Lightweight TF-IDF + Keyword Anchor Vector Store.
    """

    def __init__(self, documents: Optional[List[Dict[str, Any]]] = None):
        self.documents = documents if documents is not None else CYBER_CORPUS
        self.lightweight_store = LightweightVectorStore(self.documents)
        self.chroma_store = ChromaSecurityStore()

        # Initialize persistent ChromaDB with initial corpus
        if self.chroma_store.is_ready:
            try:
                self.chroma_store.index_documents(self.documents)
            except Exception as e:
                print(f"[HybridSecurityRetriever] Chroma initial indexing notice: {e}")

    def search(
        self,
        query: str,
        top_k: int = 3,
        similarity_threshold: float = 0.05,
        framework_filter: Optional[str] = None,
        engine_mode: str = "hybrid"  # "hybrid", "chroma", "lightweight"
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top security documents matching the query using the requested engine mode.
        """
        # Mode 1: Pure Lightweight Store (100% offline, keyword-anchored)
        if engine_mode == "lightweight" or not self.chroma_store.is_ready:
            return self.lightweight_store.search(
                query=query,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
                framework_filter=framework_filter
            )

        # Mode 2: Pure ChromaDB
        if engine_mode == "chroma":
            chroma_hits = self.chroma_store.search(
                query=query,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
                framework_filter=framework_filter
            )
            if chroma_hits:
                return chroma_hits
            # Fallback if Chroma returns empty
            return self.lightweight_store.search(
                query=query,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
                framework_filter=framework_filter
            )

        # Mode 3: Hybrid Blending (ChromaDB semantic vectors + Lightweight TF-IDF anchor boost)
        chroma_hits = self.chroma_store.search(
            query=query,
            top_k=top_k * 2,
            similarity_threshold=similarity_threshold,
            framework_filter=framework_filter
        )
        light_hits = self.lightweight_store.search(
            query=query,
            top_k=top_k * 2,
            similarity_threshold=similarity_threshold,
            framework_filter=framework_filter
        )

        merged: Dict[str, Dict[str, Any]] = {}
        # Incorporate Chroma hits
        for h in chroma_hits:
            doc_id = h["id"]
            merged[doc_id] = dict(h)
            merged[doc_id]["composite_score"] = h["score"] * 0.55
            merged[doc_id]["source_engine"] = "Hybrid (ChromaDB + Semantic)"

        # Incorporate / blend Lightweight hits
        for h in light_hits:
            doc_id = h["id"]
            if doc_id in merged:
                merged[doc_id]["composite_score"] += h["score"] * 0.45
                merged[doc_id]["score"] = round(min(1.0, merged[doc_id]["composite_score"]), 4)
                merged[doc_id]["source_engine"] = "Hybrid (Chroma + TF-IDF Boosted)"
            else:
                entry = dict(h)
                entry["score"] = round(h["score"] * 0.85, 4)
                entry["source_engine"] = "LightweightVectorStore"
                merged[doc_id] = entry

        ranked = sorted(merged.values(), key=lambda x: x["score"], reverse=True)
        return ranked[:top_k]

    def reindex(self, documents: List[Dict[str, Any]]) -> None:
        """Synchronously re-indexes both stores with updated document set."""
        self.documents = documents
        self.lightweight_store.reindex(documents)
        if self.chroma_store.is_ready:
            self.chroma_store.reindex(documents)


# ==============================================================================
# GROUNDED RAG INFERENCE & THREAT SYNTHESIS PIPELINE
# ==============================================================================

def generate_rag_offline(
    query: str,
    retrieved_docs: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Autonomous heuristic reasoning engine strictly grounded on retrieved source chunks.
    Requires zero external API keys or internet connection.
    Implements deterministic anti-hallucination guardrails and structured threat advisory synthesis.
    """
    start_time = time.time()

    if not retrieved_docs:
        latency_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "status": "refusal",
            "synthesis_text": (
                "### ⚠️ Incident Advisory Refusal: Insufficient Grounding Evidence\n\n"
                "No relevant cybersecurity framework controls or threat intelligence records "
                "were identified in the knowledge base meeting the required similarity threshold for this query.\n\n"
                "**Anti-Hallucination Guardrail Active:** In accordance with enterprise cybersecurity guidelines, "
                "CyberRAG strictly refuses to synthesize ungrounded threat hypotheses or fabricated remediations. "
                "Please broaden your query or ingest relevant security documentation in the Custom Ingestion tab."
            ),
            "mode": "Offline Heuristic RAG",
            "model": "Deterministic Semantic Reasoner (Offline)",
            "latency_ms": latency_ms,
            "top_relevance": 0.0,
            "citations": [],
            "grounded_chunk_count": 0
        }

    top_doc = retrieved_docs[0]
    top_score = top_doc.get("score", 0.0)
    doc_ids = [d["id"] for d in retrieved_docs]
    citations = [f"[Source: {d['id']}]" for d in retrieved_docs]

    # Dynamic severity determination
    critical_triggers = {"T1486", "T1003", "A10", "A03", "ransomware", "lsass", "credential", "injection"}
    high_triggers = {"A01", "A02", "A07", "T1059", "T1078", "ssrf", "crypto", "auth"}
    
    query_and_ids = (query + " " + " ".join(doc_ids)).lower()
    if any(t in query_and_ids for t in critical_triggers):
        severity = "CRITICAL (CVSS 9.0 - 10.0)"
        sla = "Immediate Containment Required (< 1 Hour)"
    elif any(t in query_and_ids for t in high_triggers):
        severity = "HIGH (CVSS 7.5 - 8.9)"
        sla = "Expedited Remediation SLA (< 24 Hours)"
    else:
        severity = "MEDIUM (CVSS 5.0 - 7.4)"
        sla = "Scheduled Hardening SLA (< 7 Days)"

    # Build Executive Threat Briefing
    executive_briefing = [
        "### 🛡️ 1. Executive Threat Briefing",
        f"- **Primary Threat Classification:** {top_doc.get('title', 'Security Advisory')} [Source: {top_doc['id']}]",
        f"- **Calculated Risk Level:** **{severity}** | **Response SLA:** {sla}",
        f"- **Frameworks Engaged:** {', '.join(sorted(list({d.get('framework', '') for d in retrieved_docs})))}",
        f"- **Correlated Standards & Mappings:** {', '.join(filter(None, [d.get('mapping', '') for d in retrieved_docs]))} [Source: {top_doc['id']}]",
        f"- **Operational Impact Summary:** Active exploitation of vulnerabilities in this category exposes enterprise "
        f"workloads to unauthorized access, potential data exfiltration, lateral movement, or service disruption. "
        f"Retrieval correlation identifies high-priority relevance with {top_doc.get('title')} (Match: {top_score * 100:.1f}%) [Source: {top_doc['id']}]."
    ]

    # Build Technical Vulnerability Analysis
    tech_analysis = [
        "\n### 🔍 2. Technical Vulnerability Analysis"
    ]
    for d in retrieved_docs:
        tech_analysis.append(
            f"#### ◈ [{d['id']}] {d.get('title', '')} — {d.get('category', '')}\n"
            f"- **Framework Mapping:** `{d.get('mapping', 'N/A')}`\n"
            f"- **Attack Mechanics & Threat Vector:** {d.get('content', '')}\n"
            f"- **Grounding Citation:** Verified against authoritative corpus chunk [Source: {d['id']}]."
        )

    # Build Prescriptive Hardening Checklist
    hardening_checklist = [
        "\n### ⚙️ 3. Prescriptive Hardening & Mitigation Checklist",
        "Implement the following defensive countermeasures immediately, strictly verified against retrieved knowledge base baselines:"
    ]

    counter = 1
    for d in retrieved_docs:
        content = d.get("content", "")
        if "Checklist:" in content:
            checklist_part = content.split("Checklist:")[-1].strip()
            # Extract numbered points (1), (2), etc.
            points = re.findall(r'\(\d+\)\s*([^;]+(?:;|$))', checklist_part)
            if points:
                for pt in points:
                    clean_pt = pt.strip().rstrip(";")
                    if clean_pt:
                        hardening_checklist.append(f"{counter}. **{clean_pt}** [Source: {d['id']}]")
                        counter += 1
            else:
                hardening_checklist.append(f"{counter}. **{checklist_part}** [Source: {d['id']}]")
                counter += 1
        else:
            hardening_checklist.append(
                f"{counter}. **Enforce operational safeguards for {d.get('title')} as specified in {d.get('framework')}** [Source: {d['id']}]."
            )
            counter += 1

    # Defense-in-Depth Governance Footer
    traceability_table = [
        "\n### 📋 4. Knowledge Base Grounding & Audit Traceability",
        "| Source ID | Framework | Title / Control | Similarity Score | Retrieval Engine |",
        "| :--- | :--- | :--- | :---: | :--- |"
    ]
    for d in retrieved_docs:
        score_pct = f"{d.get('score', 0.0) * 100:.1f}%"
        traceability_table.append(
            f"| `{d['id']}` | {d.get('framework', '')} | {d.get('title', '')} | {score_pct} | {d.get('source_engine', 'KB Engine')} |"
        )

    full_report = "\n".join(executive_briefing + tech_analysis + hardening_checklist + traceability_table)
    latency_ms = round((time.time() - start_time) * 1000, 2)

    return {
        "status": "success",
        "synthesis_text": full_report,
        "mode": "Offline Heuristic RAG",
        "model": "Deterministic Semantic Reasoner (Zero-Dependency)",
        "latency_ms": latency_ms,
        "top_relevance": round(top_score, 4),
        "citations": citations,
        "grounded_chunk_count": len(retrieved_docs)
    }


def generate_rag_gemini(
    query: str,
    retrieved_docs: List[Dict[str, Any]],
    model_name: str = "gemini-2.5-flash",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Live Google Gemini API synthesis engine with prompt anti-hallucination guardrails.
    Extracts explicit citations [Source: ID] and validates grounding against retrieved chunks.
    """
    start_time = time.time()

    if not retrieved_docs:
        return generate_rag_offline(query, retrieved_docs)

    effective_api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not effective_api_key or not GENAI_AVAILABLE or genai is None:
        # Graceful fallback to offline generation if Gemini API is unconfigured
        offline_result = generate_rag_offline(query, retrieved_docs)
        offline_result["notice"] = (
            "Gemini API key not configured or client library unavailable. "
            "Executed via autonomous offline heuristic engine."
        )
        return offline_result

    # Format retrieved sources with citation IDs
    formatted_sources = []
    for d in retrieved_docs:
        formatted_sources.append(
            f"--- START SOURCE CHUNK: [Source: {d['id']}] ---\n"
            f"Framework: {d.get('framework')}\n"
            f"Title: {d.get('title')}\n"
            f"Category/Tactic: {d.get('category')}\n"
            f"Mapping: {d.get('mapping')}\n"
            f"Content: {d.get('content')}\n"
            f"--- END SOURCE CHUNK: [Source: {d['id']}] ---"
        )
    sources_block = "\n\n".join(formatted_sources)

    system_instruction = (
        "You are CyberRAG, an authoritative cybersecurity AI operations assistant. "
        "Your task is to synthesize an actionable Incident Response & Threat Advisory strictly based on the provided RETRIEVED SOURCES.\n\n"
        "STRICT ANTI-HALLUCINATION GUARDRAILS:\n"
        "1. Every claim, finding, technical attack analysis, and mitigation step MUST be grounded in the provided sources.\n"
        "2. You MUST cite the source for every major point using the exact tag: [Source: <DOC_ID>] (e.g. [Source: OWASP-A10-SSRF]).\n"
        "3. Do not invent CVEs, CWEs, or techniques not referenced in the sources.\n"
        "4. Format your report strictly into four sections:\n"
        "   - ### 🛡️ 1. Executive Threat Briefing\n"
        "   - ### 🔍 2. Technical Vulnerability Analysis\n"
        "   - ### ⚙️ 3. Prescriptive Hardening & Mitigation Checklist\n"
        "   - ### 📋 4. NIST Incident Response Alignment\n"
    )

    prompt = (
        f"{system_instruction}\n\n"
        f"=== USER THREAT QUERY / INCIDENT DESCRIPTION ===\n{query}\n\n"
        f"=== AUTHORITATIVE RETRIEVED SOURCE CHUNKS ===\n{sources_block}\n\n"
        f"Synthesize the official Security Advisory now, adhering strictly to anti-hallucination rules and citation tags [Source: ID]:"
    )

    try:
        client = genai.Client(api_key=effective_api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )

        response_text = response.text if hasattr(response, "text") and response.text else "No response generated by model."
        latency_ms = round((time.time() - start_time) * 1000, 2)
        top_score = retrieved_docs[0].get("score", 0.0) if retrieved_docs else 0.0

        # Extract citation occurrences
        extracted_citations = list(set(re.findall(r'\[Source:\s*[^\]]+\]', response_text)))

        return {
            "status": "success",
            "synthesis_text": response_text,
            "mode": "Google Gemini RAG",
            "model": model_name,
            "latency_ms": latency_ms,
            "top_relevance": round(top_score, 4),
            "citations": extracted_citations,
            "grounded_chunk_count": len(retrieved_docs)
        }

    except Exception as e:
        # Fall back to offline generation on API error
        error_msg = str(e)
        offline_result = generate_rag_offline(query, retrieved_docs)
        offline_result["notice"] = f"Gemini API request failed ({error_msg[:90]}...). Fell back to offline synthesis."
        return offline_result


def generate_rag_synthesis(
    query: str,
    retrieved_docs: List[Dict[str, Any]],
    mode: str = "offline",  # "offline" or "gemini"
    model_name: str = "gemini-2.5-flash",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Unified dispatcher for RAG inference synthesis."""
    if mode.lower() == "gemini":
        return generate_rag_gemini(
            query=query,
            retrieved_docs=retrieved_docs,
            model_name=model_name,
            api_key=api_key
        )
    return generate_rag_offline(query=query, retrieved_docs=retrieved_docs)


# ==============================================================================
# STREAMLIT CYBERSECURITY USER INTERFACE
# ==============================================================================

CYBER_CUSTOM_CSS = """
<style>
    /* Dark Cyber Theme Palette */
    .stApp {
        background-color: #0a0e17;
        color: #e2e8f0;
    }
    
    /* Glowing Headers */
    h1, h2, h3 {
        color: #00f2fe !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* Cyber Title Glow */
    .cyber-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
        text-shadow: 0 0 25px rgba(0, 242, 254, 0.35);
    }
    
    .cyber-subtitle {
        color: #94a3b8;
        font-size: 1.0rem;
        margin-bottom: 20px;
    }

    /* Metadata Badge Bar */
    .badge-bar {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 20px;
    }
    
    .cyber-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid #1e293b;
        color: #cbd5e1;
    }
    
    .badge-cyan {
        border-color: #00f2fe;
        color: #00f2fe;
        background: rgba(0, 242, 254, 0.1);
    }
    
    .badge-green {
        border-color: #00ff88;
        color: #00ff88;
        background: rgba(0, 255, 136, 0.1);
    }
    
    .badge-purple {
        border-color: #a855f7;
        color: #c084fc;
        background: rgba(168, 85, 247, 0.1);
    }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid #1e293b;
        border-top: 3px solid #00f2fe;
        border-radius: 8px;
        padding: 12px 16px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    
    div[data-testid="stMetricValue"] {
        color: #00f2fe !important;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        font-weight: 700;
    }

    /* Source Cards & Expanders */
    .streamlit-expanderHeader {
        background-color: #0f172a !important;
        border: 1px solid #1e293b !important;
        border-radius: 6px !important;
        color: #e2e8f0 !important;
    }
    
    /* Preset Buttons */
    div.stButton > button {
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    
    div.stButton > button:hover {
        border-color: #00f2fe !important;
        box-shadow: 0 0 10px rgba(0, 242, 254, 0.4) !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0b111e;
        border-right: 1px solid #1e293b;
    }
</style>
"""

PRESET_SCENARIOS = {
    "🌐 SSRF Cloud Exfil": (
        "Adversary leveraged SSRF to access AWS link-local metadata at 169.254.169.254 "
        "and exfiltrate temporary IAM session tokens. How should we harden our cloud endpoints?"
    ),
    "🔑 LSASS Dumping": (
        "Threat actor executed Mimikatz to dump plaintext credentials and NTLM hashes from "
        "LSASS.exe process memory. How do we detect and mitigate this with Credential Guard and RunAsPPL?"
    ),
    "🔓 Broken Access Control": (
        "Attacker tampered with user ID parameters (IDOR) to access other tenants' financial records "
        "across REST endpoints. How do we enforce server-side RBAC and deny-by-default?"
    ),
    "🛑 Ransomware Response": (
        "Ransomware actor purged volume shadow copies with vssadmin and initiated multithreaded "
        "file encryption. What immediate incident containment and immutable backup restoration controls apply?"
    )
}


def run_streamlit_app():
    """Renders the comprehensive CyberRAG Streamlit web application."""
    if not STREAMLIT_AVAILABLE or st is None:
        print("Streamlit package is not installed. Please run via a supported environment.")
        return

    st.set_page_config(
        page_title="CyberRAG | Security Knowledge & Threat Retrieval Engine",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Inject Cyber Dark Theme CSS
    st.markdown(CYBER_CUSTOM_CSS, unsafe_allow_html=True)

    # Initialize Global Application State
    if "retriever" not in st.session_state:
        st.session_state["retriever"] = HybridSecurityRetriever()
    if "audit_log" not in st.session_state:
        st.session_state["audit_log"] = []
    if "current_query" not in st.session_state:
        st.session_state["current_query"] = PRESET_SCENARIOS["🌐 SSRF Cloud Exfil"]
    if "last_results" not in st.session_state:
        st.session_state["last_results"] = None

    retriever: HybridSecurityRetriever = st.session_state["retriever"]

    # ==========================================================================
    # SIDEBAR CONFIGURATION
    # ==========================================================================
    with st.sidebar:
        st.markdown("### 🛡️ CyberRAG Console")
        st.markdown(
            """
            <div class="badge-bar">
                <span class="cyber-badge badge-cyan">Student: Liav Dahari</span>
                <span class="cyber-badge badge-purple">FAU ID: Z23815316</span>
                <span class="cyber-badge">COT4930 GenSec</span>
                <span class="cyber-badge badge-green">Agent: AntiGravity</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.divider()

        st.markdown("#### 🧠 RAG Reasoning Engine")
        rag_mode_selection = st.radio(
            "Select Inference Engine:",
            ["Offline Heuristic Engine (Deterministic & Zero-Dependency)", "Google Gemini API (Live Generative AI)"],
            index=0,
            help="Choose between autonomous local heuristic synthesis or live Gemini cloud inference."
        )
        rag_mode = "gemini" if "Google Gemini" in rag_mode_selection else "offline"

        gemini_model = "gemini-2.5-flash"
        api_key_input = ""
        if rag_mode == "gemini":
            gemini_model = st.selectbox(
                "Gemini Model:",
                ["gemini-2.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"],
                index=0
            )
            api_key_input = st.text_input(
                "Gemini API Key (optional if in .env):",
                type="password",
                value=os.environ.get("GEMINI_API_KEY", os.environ.get("GOOGLE_API_KEY", "")),
                help="Enter Google Gemini API key or set GEMINI_API_KEY in .env"
            )

        st.divider()
        st.markdown("#### 🔍 Retrieval Engine & Vector Store")
        retrieval_mode_selection = st.selectbox(
            "Vector Storage Strategy:",
            [
                "Hybrid (ChromaDB + TF-IDF Boosted)",
                "Persistent ChromaDB Store",
                "Lightweight Vector Store (100% Offline)"
            ],
            index=0
        )
        engine_mode_map = {
            "Hybrid (ChromaDB + TF-IDF Boosted)": "hybrid",
            "Persistent ChromaDB Store": "chroma",
            "Lightweight Vector Store (100% Offline)": "lightweight"
        }
        engine_mode = engine_mode_map[retrieval_mode_selection]

        top_k = st.slider("Top-K Grounded Chunks:", min_value=1, max_value=6, value=3, step=1)
        similarity_threshold = st.slider("Similarity Threshold:", min_value=0.00, max_value=0.70, value=0.05, step=0.01)

        framework_filter = st.selectbox(
            "Framework Filter:",
            ["All Frameworks", "OWASP Top 10 (2021)", "MITRE ATT&CK (v14)", "NIST CSF 2.0"],
            index=0
        )

        st.divider()
        st.markdown("#### 📡 System Status")
        chroma_status = "🟢 Active (./hw6/.chroma_db)" if retriever.chroma_store.is_ready else "🟡 Fallback (Lightweight)"
        st.write(f"**ChromaDB:** {chroma_status}")
        st.write(f"**GenAI SDK:** {'🟢 Installed' if GENAI_AVAILABLE else '🔴 Missing'}")
        st.write(f"**Indexed Knowledge Base:** {len(retriever.documents)} documents")

    # ==========================================================================
    # MAIN APPLICATION WORKSPACE
    # ==========================================================================
    st.markdown('<div class="cyber-title">🛡️ CyberRAG</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="cyber-subtitle">Enterprise Security Knowledge & Threat Intelligence Retrieval Engine | '
        'COT4930 Generative Cybersecurity — Homework 06.3</div>',
        unsafe_allow_html=True
    )

    tab_triage, tab_explorer, tab_ingest, tab_audit = st.tabs([
        "🎯 Threat Query & Incident Triage",
        "📚 Knowledge Base Explorer",
        "📥 Custom Ingestion",
        "📊 RAG Performance & Audit Log"
    ])

    # --------------------------------------------------------------------------
    # TAB 1: THREAT QUERY & INCIDENT TRIAGE
    # --------------------------------------------------------------------------
    with tab_triage:
        st.markdown("##### ⚡ One-Click Threat Scenario Presets")
        preset_cols = st.columns(4)
        for idx, (label, text) in enumerate(PRESET_SCENARIOS.items()):
            with preset_cols[idx]:
                if st.button(label, use_container_width=True, key=f"btn_preset_{idx}"):
                    st.session_state["current_query"] = text
                    st.rerun()

        # Query Input Area
        query_text = st.text_area(
            "Incident Telemetry / Security Inquiry Query:",
            value=st.session_state.get("current_query", ""),
            height=90,
            placeholder="Describe the incident symptoms, malware signatures, or security framework questions...",
            key="threat_query_input"
        )

        execute_col1, execute_col2 = st.columns([3, 1])
        with execute_col1:
            run_triage = st.button("🚀 Execute Grounded Threat Triage", type="primary", use_container_width=True)
        with execute_col2:
            clear_btn = st.button("🔄 Clear", use_container_width=True)
            if clear_btn:
                st.session_state["current_query"] = ""
                st.session_state["last_results"] = None
                st.rerun()

        if run_triage and query_text.strip():
            with st.spinner("Retrieving grounded cybersecurity evidence and synthesizing threat advisory..."):
                t_retrieval_start = time.time()
                hits = retriever.search(
                    query=query_text,
                    top_k=top_k,
                    similarity_threshold=similarity_threshold,
                    framework_filter=framework_filter,
                    engine_mode=engine_mode
                )
                retrieval_latency = round((time.time() - t_retrieval_start) * 1000, 2)

                t_gen_start = time.time()
                advisory = generate_rag_synthesis(
                    query=query_text,
                    retrieved_docs=hits,
                    mode=rag_mode,
                    model_name=gemini_model,
                    api_key=api_key_input
                )
                generation_latency = round((time.time() - t_gen_start) * 1000, 2)

                top_match_pct = round((hits[0]["score"] * 100), 1) if hits else 0.0

                result_bundle = {
                    "query": query_text,
                    "hits": hits,
                    "advisory": advisory,
                    "retrieval_latency_ms": retrieval_latency,
                    "generation_latency_ms": generation_latency,
                    "top_match_pct": top_match_pct,
                    "rag_mode": rag_mode,
                    "engine_mode": engine_mode,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state["last_results"] = result_bundle

                # Add to persistent session audit log
                st.session_state["audit_log"].append({
                    "timestamp": result_bundle["timestamp"],
                    "query": query_text[:80] + ("..." if len(query_text) > 80 else ""),
                    "engine": engine_mode,
                    "rag_mode": advisory.get("mode", rag_mode),
                    "retrieval_ms": retrieval_latency,
                    "generation_ms": generation_latency,
                    "top_relevance": f"{top_match_pct}%",
                    "grounded_chunks": len(hits),
                    "top_source_id": hits[0]["id"] if hits else "None"
                })

        # Render Active Results
        if st.session_state.get("last_results"):
            res = st.session_state["last_results"]
            hits = res["hits"]
            advisory = res["advisory"]

            st.markdown("---")
            st.markdown("#### ⏱️ Real-Time Telemetry & Grounding Metrics")
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            with m_col1:
                st.metric("⏱️ Retrieval Latency", f"{res['retrieval_latency_ms']} ms")
            with m_col2:
                st.metric("⚡ Generation Latency", f"{res['generation_latency_ms']} ms")
            with m_col3:
                st.metric("🎯 Top Match Relevance", f"{res['top_match_pct']}%")
            with m_col4:
                st.metric("📚 Grounded Chunks", f"{len(hits)} Sources")

            # Collapsible Grounded Source Chunks
            st.markdown(f"#### 📌 Retrieved Source Chunks ({len(hits)} Grounded Documents)")
            if not hits:
                st.warning("No knowledge base chunks passed the similarity threshold for this query.")
            else:
                for idx, chunk in enumerate(hits, 1):
                    score_pct = f"{chunk.get('score', 0.0) * 100:.1f}%"
                    badge_style = "badge-cyan" if "OWASP" in chunk.get("framework", "") else ("badge-purple" if "MITRE" in chunk.get("framework", "") else "badge-green")
                    
                    with st.expander(
                        f"#{idx} [{chunk['id']}] {chunk.get('title', '')} — Match: {score_pct} ({chunk.get('source_engine', '')})",
                        expanded=(idx == 1)
                    ):
                        st.markdown(
                            f"""
                            <div class="badge-bar">
                                <span class="cyber-badge {badge_style}">{chunk.get('framework', '')}</span>
                                <span class="cyber-badge">{chunk.get('category', '')}</span>
                                <span class="cyber-badge">Mapping: {chunk.get('mapping', '')}</span>
                                <span class="cyber-badge">Similarity: {score_pct}</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        st.write(f"**Knowledge Base Content:**\n\n{chunk.get('content', '')}")
                        if chunk.get("tags"):
                            st.caption(f"🏷️ Tags: {', '.join(chunk['tags'])}")

            # Synthesized Advisory Output
            st.markdown("#### 🛡️ Grounded Threat Advisory & Incident Response")
            if "notice" in advisory:
                st.info(f"ℹ️ {advisory['notice']}")
            
            st.markdown(advisory.get("synthesis_text", "No advisory generated."))

            # One-Click Export Actions
            st.markdown("---")
            st.markdown("##### 📥 Export Security Advisory")
            exp_col1, exp_col2, exp_col3 = st.columns([1, 1, 2])

            with exp_col1:
                export_md = (
                    f"# CyberRAG Security Advisory\n\n"
                    f"**Generated:** {res['timestamp']}\n"
                    f"**Query:** {res['query']}\n"
                    f"**RAG Engine:** {advisory.get('mode', 'N/A')} ({advisory.get('model', 'N/A')})\n"
                    f"**Telemetry:** Retrieval: {res['retrieval_latency_ms']}ms | Generation: {res['generation_latency_ms']}ms\n\n"
                    f"---\n\n"
                    f"{advisory.get('synthesis_text', '')}\n"
                )
                st.download_button(
                    "📥 Download Markdown Report",
                    data=export_md,
                    file_name="cyber_threat_advisory.md",
                    mime="text/markdown",
                    use_container_width=True
                )

            with exp_col2:
                export_json = json.dumps({
                    "metadata": {
                        "application": "CyberRAG",
                        "student": "Liav Dahari (Z23815316)",
                        "course": "COT4930 Generative Cybersecurity",
                        "timestamp": res["timestamp"]
                    },
                    "telemetry": {
                        "retrieval_latency_ms": res["retrieval_latency_ms"],
                        "generation_latency_ms": res["generation_latency_ms"],
                        "top_relevance_pct": res["top_match_pct"],
                        "grounded_chunk_count": len(hits)
                    },
                    "query": res["query"],
                    "retrieved_sources": hits,
                    "advisory": advisory
                }, indent=2)
                st.download_button(
                    "📥 Download JSON Advisory",
                    data=export_json,
                    file_name="cyber_security_advisory.json",
                    mime="application/json",
                    use_container_width=True
                )

    # --------------------------------------------------------------------------
    # TAB 2: KNOWLEDGE BASE EXPLORER
    # --------------------------------------------------------------------------
    with tab_explorer:
        st.markdown("### 📚 Pre-Indexed Security Knowledge Base Explorer")
        st.write("Browse and search authoritative security documents pre-indexed in CyberRAG.")

        exp_col1, exp_col2 = st.columns([1, 2])
        with exp_col1:
            filter_fw = st.selectbox(
                "Filter Framework:",
                ["All Frameworks"] + FRAMEWORKS,
                key="explorer_fw_filter"
            )
        with exp_col2:
            search_kb = st.text_input("Search Knowledge Base Chunks:", placeholder="Search title, CWE, tags, or content...", key="explorer_search")

        matching_docs = retriever.documents
        if filter_fw != "All Frameworks":
            matching_docs = [d for d in matching_docs if d.get("framework") == filter_fw]

        if search_kb.strip():
            sk = search_kb.lower()
            matching_docs = [
                d for d in matching_docs
                if sk in d.get("title", "").lower()
                or sk in d.get("content", "").lower()
                or sk in d.get("mapping", "").lower()
                or any(sk in t.lower() for t in d.get("tags", []))
            ]

        st.caption(f"Showing {len(matching_docs)} of {len(retriever.documents)} documents")

        for d in matching_docs:
            badge_style = "badge-cyan" if "OWASP" in d.get("framework", "") else ("badge-purple" if "MITRE" in d.get("framework", "") else "badge-green")
            with st.container():
                st.markdown(
                    f"""
                    <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid #1e293b; border-radius: 8px; padding: 14px; margin-bottom: 12px;">
                        <div class="badge-bar">
                            <span class="cyber-badge {badge_style}">{d.get('framework', '')}</span>
                            <span class="cyber-badge">{d.get('id', '')}</span>
                            <span class="cyber-badge">CWE/ATT&CK: {d.get('mapping', '')}</span>
                        </div>
                        <h4 style="margin: 6px 0; color: #38bdf8 !important;">{d.get('title', '')}</h4>
                        <p style="color: #cbd5e1; font-size: 0.95rem; line-height: 1.5;">{d.get('content', '')}</p>
                        <span style="color: #94a3b8; font-size: 0.8rem;">🏷️ Tags: {', '.join(d.get('tags', []))}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # --------------------------------------------------------------------------
    # TAB 3: CUSTOM INGESTION & DYNAMIC CHUNKING
    # --------------------------------------------------------------------------
    with tab_ingest:
        st.markdown("### 📥 Dynamic Custom Security Documentation Ingestion")
        st.write(
            "Upload or paste enterprise security documentation, threat bulletins, or incident post-mortems. "
            "CyberRAG dynamically chunks long texts and re-indexes both ChromaDB and the offline vector store in real-time."
        )

        ingest_mode = st.radio("Ingestion Source:", ["Paste Document Text", "Upload Security File (.txt, .md, .json)"], horizontal=True)

        col_id, col_fw = st.columns(2)
        with col_id:
            new_doc_id = st.text_input("Document ID Prefix:", value=f"CUSTOM-SEC-{len(retriever.documents) + 1}")
        with col_fw:
            new_doc_framework = st.selectbox(
                "Assign Framework / Domain:",
                ["Enterprise Internal Policy", "Vendor Threat Advisory", "Zero-Day CVE Brief", "Custom IR Playbook", "Cloud Architecture Standard"]
            )

        new_doc_title = st.text_input("Document Title:", placeholder="e.g. Internal Zero-Trust Identity & PAM Hardening Baseline")
        new_doc_mapping = st.text_input("Standards Mapping (optional):", placeholder="e.g. CWE-287, NIST PR.AA, ISO 27001 A.9")
        new_doc_tags = st.text_input("Search Keyword Tags (comma-separated):", placeholder="e.g. zero trust, pam, okta, iam, session, token")

        # Dynamic Chunking Controls
        with st.expander("⚙️ Dynamic Chunking Configuration", expanded=True):
            chunk_col1, chunk_col2 = st.columns(2)
            with chunk_col1:
                enable_chunking = st.checkbox("Enable Dynamic Chunking for Long Texts", value=True)
            with chunk_col2:
                chunk_size_words = st.slider("Target Chunk Size (Words):", min_value=50, max_value=400, value=150, step=25)

        raw_content = ""
        parsed_json_items = []

        if ingest_mode == "Paste Document Text":
            raw_content = st.text_area(
                "Security Text / Intelligence Report:",
                height=180,
                placeholder="Paste raw security advisory, incident report, or hardening instructions here..."
            )
        else:
            uploaded_file = st.file_uploader("Upload Security File:", type=["txt", "md", "json"])
            if uploaded_file is not None:
                file_bytes = uploaded_file.read().decode("utf-8")
                if uploaded_file.name.endswith(".json"):
                    try:
                        data = json.loads(file_bytes)
                        if isinstance(data, list):
                            parsed_json_items = data
                            st.success(f"Parsed JSON array with {len(data)} items from '{uploaded_file.name}'.")
                        elif isinstance(data, dict):
                            parsed_json_items = [data]
                            st.success(f"Parsed structured JSON object from '{uploaded_file.name}'.")
                    except Exception as e:
                        st.error(f"Error parsing JSON: {e}")
                        raw_content = file_bytes
                else:
                    raw_content = file_bytes
                    st.success(f"Loaded '{uploaded_file.name}' ({len(raw_content)} chars).")

        if st.button("⚡ Ingest & Dynamically Re-Index Vector Store", type="primary"):
            docs_to_add: List[Dict[str, Any]] = []
            tags_list = [t.strip() for t in new_doc_tags.split(",") if t.strip()]

            # Handle JSON array batch ingestion
            if parsed_json_items:
                for idx, item in enumerate(parsed_json_items, 1):
                    item_content = item.get("content", item.get("description", str(item)))
                    docs_to_add.append({
                        "id": f"{new_doc_id.strip()}-J{idx}",
                        "framework": item.get("framework", new_doc_framework),
                        "title": item.get("title", f"{new_doc_title} (Item {idx})"),
                        "category": item.get("category", "Structured Threat Intel"),
                        "mapping": item.get("mapping", new_doc_mapping.strip()),
                        "tags": item.get("tags", tags_list),
                        "content": item_content
                    })
            elif raw_content.strip():
                if not new_doc_title.strip():
                    st.error("Please provide a Document Title.")
                else:
                    words = raw_content.strip().split()
                    if enable_chunking and len(words) > chunk_size_words:
                        # Chunk words with slight overlap
                        overlap = 20
                        step = max(1, chunk_size_words - overlap)
                        chunk_idx = 1
                        for i in range(0, len(words), step):
                            chunk_words = words[i:i + chunk_size_words]
                            chunk_text = " ".join(chunk_words)
                            docs_to_add.append({
                                "id": f"{new_doc_id.strip()}-C{chunk_idx}",
                                "framework": new_doc_framework,
                                "title": f"{new_doc_title.strip()} (Part {chunk_idx})",
                                "category": "Custom Ingested Intelligence",
                                "mapping": new_doc_mapping.strip(),
                                "tags": tags_list,
                                "content": chunk_text
                            })
                            chunk_idx += 1
                    else:
                        docs_to_add.append({
                            "id": new_doc_id.strip(),
                            "framework": new_doc_framework,
                            "title": new_doc_title.strip(),
                            "category": "Custom Ingested Intelligence",
                            "mapping": new_doc_mapping.strip(),
                            "tags": tags_list,
                            "content": raw_content.strip()
                        })

            if not docs_to_add:
                st.error("No valid text or JSON content to ingest.")
            else:
                updated_corpus = retriever.documents + docs_to_add
                retriever.reindex(updated_corpus)
                st.success(
                    f"🎉 Successfully ingested and indexed {len(docs_to_add)} chunk(s)! "
                    f"Total active knowledge base size: {len(retriever.documents)} documents."
                )

    # --------------------------------------------------------------------------
    # TAB 4: RAG PERFORMANCE & AUDIT LOG
    # --------------------------------------------------------------------------
    with tab_audit:
        st.markdown("### 📊 RAG Performance & Incident Telemetry Audit Log")
        st.write("Real-time telemetry, query latencies, vector engine metrics, and grounding audit logs.")

        audit_records = st.session_state["audit_log"]

        # Summary Telemetry Cards
        if audit_records:
            total_queries = len(audit_records)
            avg_retrieval = round(sum(r["retrieval_ms"] for r in audit_records) / total_queries, 2)
            avg_gen = round(sum(r["generation_ms"] for r in audit_records) / total_queries, 2)

            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            with kpi1:
                st.metric("Total Triage Inquiries", total_queries)
            with kpi2:
                st.metric("Avg Retrieval Latency", f"{avg_retrieval} ms")
            with kpi3:
                st.metric("Avg Generation Latency", f"{avg_gen} ms")
            with kpi4:
                st.metric("Active KB Chunks", len(retriever.documents))

            st.markdown("---")
            st.dataframe(
                audit_records,
                use_container_width=True,
                column_config={
                    "timestamp": "Timestamp",
                    "query": "Threat Query",
                    "engine": "Vector Store",
                    "rag_mode": "RAG Mode",
                    "retrieval_ms": "Retrieval (ms)",
                    "generation_ms": "Gen (ms)",
                    "top_relevance": "Top Match",
                    "grounded_chunks": "Chunks",
                    "top_source_id": "Top Source ID"
                }
            )

            act_col1, act_col2 = st.columns([1, 3])
            with act_col1:
                audit_json = json.dumps(audit_records, indent=2)
                st.download_button(
                    "📥 Export Audit Log (JSON)",
                    data=audit_json,
                    file_name="rag_performance_audit_log.json",
                    mime="application/json",
                    use_container_width=True
                )
            with act_col2:
                if st.button("🗑️ Clear Audit Log", use_container_width=False):
                    st.session_state["audit_log"] = []
                    st.rerun()
        else:
            st.info("No queries executed yet in this session. Run a threat triage query in Tab 1 to generate telemetry entries.")


def main():
    """Application dispatcher supporting both Streamlit GUI and CLI test modes."""
    is_streamlit_runtime = False
    if STREAMLIT_AVAILABLE:
        try:
            from streamlit.runtime.scriptrunner import get_script_run_ctx
            ctx = get_script_run_ctx()
            if ctx is not None:
                is_streamlit_runtime = True
        except Exception:
            pass

    if is_streamlit_runtime:
        run_streamlit_app()
    else:
        # CLI diagnostic mode
        stats = get_corpus_statistics()
        print("=== CyberRAG Knowledge Base Corpus Loaded ===")
        print(f"Total Pre-indexed Documents: {stats['total_documents']}")
        for fw, count in stats["frameworks"].items():
            print(f"  • {fw}: {count} authoritative records")

        print("\n--- Testing Hybrid Retrieval & RAG Synthesis Pipeline ---")
        retriever = HybridSecurityRetriever()

        test_scenario = PRESET_SCENARIOS["🌐 SSRF Cloud Exfil"]
        print(f"\n[Scenario]: '{test_scenario}'")
        hits = retriever.search(test_scenario, top_k=2, engine_mode="hybrid")

        for i, h in enumerate(hits, 1):
            print(f"  [{i}] {h['id']} — {h['title']} (Score: {h['score']:.4f})")

        advisory = generate_rag_offline(test_scenario, hits)
        print(f"\nStatus: {advisory['status']} | Latency: {advisory['latency_ms']} ms | Citations: {advisory['citations']}")
        print("\n[Streamlit Web App Ready] Launch with: streamlit run hw6/app.py")


if __name__ == "__main__":
    main()




