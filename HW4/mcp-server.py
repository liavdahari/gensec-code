"""SecOps MCP Server - Security Operations Tools Server.

HW4: Custom FastMCP Server
Course: COT4930 - Generative AI Security
Author: Liav Dahari (FAU ID: Z23815316)
Institution: Florida Atlantic University
Pattern Adopted: 04_MCP/01_sqlite/vulnerable_sqlite_mcp_server.py

This server exposes custom security audit tools using FastMCP over stdio.
"""

import re
import sys
from fastmcp import FastMCP
import requests

# Initialize FastMCP Server matching 04_MCP/01_sqlite pattern
mcp = FastMCP("Simple-SecOps-Tools")


@mcp.tool()
def check_url_security(url: str) -> dict:
    """Audit a target URL for HTTPS enforcement and essential defensive HTTP security headers.

    Checks for the presence of Strict-Transport-Security (HSTS), Content-Security-Policy (CSP),
    and X-Frame-Options to evaluate resistance to clickjacking, MITM, and injection attacks.
    """
    try:
        response = requests.get(url, timeout=5)
        headers = {k.lower(): v for k, v in response.headers.items()}
        return {
            "url": url,
            "status_code": response.status_code,
            "uses_https": url.startswith("https://"),
            "has_strict_transport_security": "strict-transport-security" in headers,
            "has_content_security_policy": "content-security-policy" in headers,
            "has_x_frame_options": "x-frame-options" in headers,
            "security_summary": (
                "PASS: Target employs HTTPS and defensive headers."
                if url.startswith("https://") and "strict-transport-security" in headers
                else "WARNING: Missing critical defensive headers or unencrypted transport."
            ),
        }
    except Exception as e:
        return {"error": str(e), "url": url}


@mcp.tool()
def scan_text_for_secrets(text: str) -> dict:
    """Scan raw text or extracted HTML/DOM content for exposed credentials and secrets.

    Detects Google API keys, OpenAI keys, GitHub personal access tokens, and plaintext
    password or secret assignments using regular expression signature matching.
    """
    findings = []
    if re.search(r"AIza[0-9A-Za-z-_]{35}", text):
        findings.append("Google API Key detected (AIza...)")
    if re.search(r"sk-[a-zA-Z0-9]{20,}", text):
        findings.append("OpenAI / Cloud API Key detected (sk-...)")
    if re.search(r"ghp_[a-zA-Z0-9]{36}", text):
        findings.append("GitHub Personal Access Token detected (ghp_...)")
    if re.search(r"(?i)(password|passwd|secret|api_key)\s*[:=]\s*['\"][^'\"]+['\"]", text):
        findings.append("Plaintext credential assignment detected")

    return {
        "text_length": len(text),
        "secrets_found_count": len(findings),
        "findings": findings if findings else ["No secrets detected"],
        "status": "VULNERABLE: Potential secrets found" if findings else "SECURE: No secrets found",
    }


@mcp.tool()
def identify_hash_type(hash_string: str) -> dict:
    """Identify cryptographic hash algorithms and assess their security posture.

    Analyzes hash string length and structure to identify MD5, SHA-1, SHA-256,
    or bcrypt, highlighting deprecated algorithms susceptible to collision attacks.
    """
    h = hash_string.strip()
    if len(h) == 32 and re.match(r"^[a-fA-F0-9]+$", h):
        return {
            "hash": h,
            "type": "MD5",
            "status": "INSECURE (Vulnerable to collision and instant lookup table crack)",
        }
    elif len(h) == 40 and re.match(r"^[a-fA-F0-9]+$", h):
        return {
            "hash": h,
            "type": "SHA-1",
            "status": "WEAK (Deprecated by NIST, collision attacks feasible)",
        }
    elif len(h) == 64 and re.match(r"^[a-fA-F0-9]+$", h):
        return {
            "hash": h,
            "type": "SHA-256",
            "status": "STANDARD (Secure for integrity, requires salt for passwords)",
        }
    elif re.match(r"^\$2[aby]?\$\d{2}\$[./A-Za-z0-9]{20,}", h):
        return {
            "hash": h,
            "type": "bcrypt",
            "status": "SECURE (Modern adaptive password hash with salt & work factor)",
        }
    else:
        return {"hash": h, "type": "Unknown", "status": "Unrecognized hash format"}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "http":
        mcp.run(transport="http", host="0.0.0.0", port=8080)
    else:
        mcp.run(transport="stdio")
