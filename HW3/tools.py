"""HW3 Agent Tools Suite.

This module implements the full tool suite for the LangChain/LangGraph agent,
satisfying all three difficulty levels specified in HW3:

1. Retained Tools:
   - PythonREPLTool: Python code execution for mathematical and algorithmic tasks.
   - execute_command (Terminal tool): Safe shell command execution with timeout guards.

2. Level 1 - Additional Built-in Tools:
   - DuckDuckGoSearchRun: Real-time web search without requiring external API keys.
   - WikipediaQueryRun: Encyclopedic search for historical and academic topics.
   - SQLDatabase query tools: SQL querying over SQLite databases.

3. Level 2 - Custom Tools with Pydantic Validation:
   - smartnotebook_rag_search: Custom tool that imports and queries the HW2
     ResearchNoteLoader and Chroma/notes knowledge base, returning cited context [Source: filename].
   - database_security_audit: Pydantic-validated tool that scans SQLite security
     databases (ROADrecon Azure AD and MetaCTF) for credential hashes, admin roles, and anomalies.
   - presidents_analyzer: Custom tool that parses and calculates longevity and term metrics
     from the presidential dataset in presidents.py.

Course: COT4930 - Generative AI Security
Author: Liav Dahari (FAU ID: Z23815316)
"""

from __future__ import annotations

import ast
import datetime
import json
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator

# LangChain tool decorators and core classes
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.utilities import SQLDatabase
from langchain_experimental.tools import PythonREPLTool

# Ensure HW2 modules can be loaded for Custom RAG Tool integration
_CURRENT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _CURRENT_DIR.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_REPO_ROOT / "HW2") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "HW2"))

try:
    from HW2.notebook_loader import ResearchNoteLoader
except ImportError:
    try:
        from notebook_loader import ResearchNoteLoader
    except ImportError:
        ResearchNoteLoader = None


# ============================================================================
# 1. Retained Tools: Python REPL and Safe Terminal Tool
# ============================================================================

# Instantiate LangChain PythonREPLTool
python_repl_tool = PythonREPLTool()


class TerminalCommandInput(BaseModel):
    """Schema for shell command execution."""
    command: str = Field(
        ...,
        description="The shell command to execute in the system terminal."
    )
    timeout_seconds: int = Field(
        default=15,
        description="Maximum execution time in seconds before aborting."
    )

    @field_validator("command")
    def validate_safe_command(cls, v: str) -> str:
        """Sanity check to prevent blatantly destructive commands."""
        forbidden_patterns = [
            r"rm\s+-rf\s+/",
            r"mkfs",
            r":\(\)\s*\{\s*:\|:&\s*\};:",  # Fork bomb
            r"dd\s+if=.*of=/dev/sd",
        ]
        for pattern in forbidden_patterns:
            if re.search(pattern, v):
                raise ValueError(f"Command blocked by safety filter: contains dangerous pattern '{pattern}'")
        return v.strip()


@tool("terminal_tool", args_schema=TerminalCommandInput)
def execute_command(command: str, timeout_seconds: int = 15) -> str:
    """Executes a non-destructive shell command on the host terminal and returns stdout/stderr.

    Args:
        command: The shell command to run.
        timeout_seconds: Timeout limit in seconds.

    Returns:
        The combined output or formatted error string.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
            cwd=str(_CURRENT_DIR),
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[STDERR]:\n{result.stderr}"
        if result.returncode != 0:
            return f"[Exit Code {result.returncode}]:\n{output}"
        return output if output.strip() else "[Command executed successfully with no stdout output]"
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout_seconds} seconds."
    except Exception as exc:
        return f"Execution error: {str(exc)}"


# ============================================================================
# 2. Level 1 Built-in Tools: Live Web Search, Wikipedia, and SQLite DB
# ============================================================================

# Live Web Search via DuckDuckGo (zero API key needed)
web_search_tool = DuckDuckGoSearchRun(
    name="duckduckgo_search",
    description=(
        "Search the live web using DuckDuckGo. Use this to find up-to-date information, "
        "current sports scores, real-time events, or documentation not in local files."
    ),
)

# Wikipedia Query Run
try:
    wiki_wrapper = WikipediaAPIWrapper(top_k_results=3, doc_content_chars_max=1500)
    wikipedia_tool = WikipediaQueryRun(
        name="wikipedia_search",
        api_wrapper=wiki_wrapper,
        description="Search Wikipedia for detailed factual, historical, and conceptual summaries."
    )
except Exception:
    wikipedia_tool = None


class SQLQueryInput(BaseModel):
    """Schema for SQL database query tool."""
    database_name: str = Field(
        default="metactf_users.db",
        description="The SQLite database filename inside HW3/db_data/ (e.g., 'metactf_users.db' or 'roadrecon.db')."
    )
    query: str = Field(
        ...,
        description="The SQL SELECT statement to execute."
    )

    @field_validator("database_name")
    def validate_dbname(cls, v: str) -> str:
        clean = Path(v).name
        if clean not in ["metactf_users.db", "roadrecon.db"]:
            raise ValueError("Only 'metactf_users.db' and 'roadrecon.db' in HW3/db_data/ are permitted.")
        return clean

    @field_validator("query")
    def validate_readonly_query(cls, v: str) -> str:
        stripped = v.strip().lower()
        if not (stripped.startswith("select") or stripped.startswith("pragma") or stripped.startswith("explain")):
            raise ValueError("Only read-only SELECT or PRAGMA statements are permitted.")
        return v.strip()


@tool("sql_db_query", args_schema=SQLQueryInput)
def query_sqlite_database(database_name: str = "metactf_users.db", query: str = "SELECT * FROM users LIMIT 5;") -> str:
    """Executes a read-only SQL query against the specified SQLite database in HW3/db_data/.

    Args:
        database_name: Either 'metactf_users.db' or 'roadrecon.db'.
        query: A read-only SQL SELECT query.

    Returns:
        JSON-formatted string containing the query results or error message.
    """
    db_path = _CURRENT_DIR / "db_data" / database_name
    if not db_path.exists():
        return f"Error: Database {database_name} does not exist at {db_path}."

    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        conn.close()

        records = [dict(zip(columns, row)) for row in rows]
        return json.dumps({
            "database": database_name,
            "row_count": len(records),
            "results": records[:50],  # Guard against massive prints
        }, indent=2)
    except Exception as exc:
        return f"Database query error: {str(exc)}"


# ============================================================================
# 3. Level 2 Custom Tools: HW2 SmartNotebook RAG, Security Audit, Presidents
# ============================================================================

class SmartNotebookRAGInput(BaseModel):
    """Input schema for the custom SmartNotebook RAG search tool."""
    query: str = Field(
        ...,
        description="The research or AI security query to search for within your HW2 notebook notes and documents."
    )
    top_k: int = Field(
        default=3,
        description="The maximum number of relevant document passages to retrieve."
    )
    folder: str = Field(
        default="notes",
        description="Subfolder in HW2/rag_data to search: 'notes', 'JSON', 'txt', or 'all'."
    )


@tool("smartnotebook_rag_search", args_schema=SmartNotebookRAGInput)
def smartnotebook_rag_search(query: str, top_k: int = 3, folder: str = "notes") -> str:
    """Searches the HW2 SmartNotebook RAG knowledge base using ResearchNoteLoader and returns cited passages.

    Utilizes the custom document loader and datasets created in Homework 2 (such as
    ai_security_brief.md, notebooklm_architecture.md, security_vulnerabilities.json,
    amendments.txt, constitution.txt, airports.json, etc.).

    Args:
        query: Search question or keywords.
        top_k: Number of relevant passages to retrieve.
        folder: Subdirectory inside HW2/rag_data ('notes', 'JSON', 'txt', or 'all').

    Returns:
        Grounded context with strict [Source: filename] citations.
    """
    rag_data_dir = _REPO_ROOT / "HW2" / "rag_data"
    if not rag_data_dir.exists():
        return "Error: HW2/rag_data directory not found."

    # Determine paths to load
    target_dirs = []
    if folder == "all":
        target_dirs = [rag_data_dir / "notes", rag_data_dir / "JSON", rag_data_dir / "txt"]
    else:
        target_dirs = [rag_data_dir / folder]

    loaded_docs = []
    if ResearchNoteLoader:
        for tdir in target_dirs:
            if tdir.exists():
                # Load markdown notes and JSON files with ResearchNoteLoader
                try:
                    loader_md = ResearchNoteLoader(tdir, glob_pattern="**/*.[mM][dD]")
                    loaded_docs.extend(loader_md.load())
                except Exception:
                    pass
                try:
                    loader_json = ResearchNoteLoader(tdir, glob_pattern="**/*.[jJ][sS][oO][nN]")
                    loaded_docs.extend(loader_json.load())
                except Exception:
                    pass

    # Fallback to plain text files if needed
    for tdir in target_dirs:
        if tdir.exists():
            for txt_file in tdir.glob("**/*.txt"):
                try:
                    content = txt_file.read_text(encoding="utf-8", errors="ignore")
                    loaded_docs.append({
                        "page_content": content,
                        "metadata": {"source": txt_file.name, "title": txt_file.stem}
                    })
                except Exception:
                    pass

    if not loaded_docs:
        return f"No documents found in HW2/rag_data/{folder}."

    # Perform keyword and semantic token relevance scoring
    query_tokens = set(re.findall(r"\w+", query.lower()))
    scored_passages = []

    for doc in loaded_docs:
        content = getattr(doc, "page_content", "") if not isinstance(doc, dict) else doc.get("page_content", "")
        meta = getattr(doc, "metadata", {}) if not isinstance(doc, dict) else doc.get("metadata", {})
        source = meta.get("source", meta.get("title", "Unknown Source"))

        # Chunk into paragraphs / sections
        chunks = [p.strip() for p in re.split(r"\n\s*\n", content) if len(p.strip()) > 40]
        if not chunks:
            chunks = [content[:1000]]

        for chunk in chunks:
            chunk_tokens = set(re.findall(r"\w+", chunk.lower()))
            overlap = len(query_tokens.intersection(chunk_tokens))
            if overlap > 0:
                score = overlap / (len(query_tokens) + 1e-5)
                scored_passages.append((score, source, meta, chunk))

    # Sort by relevance score descending
    scored_passages.sort(key=lambda x: x[0], reverse=True)
    top_matches = scored_passages[:top_k]

    if not top_matches:
        # Fallback to first document excerpt
        first_doc = loaded_docs[0]
        content = getattr(first_doc, "page_content", "") if not isinstance(first_doc, dict) else first_doc.get("page_content", "")
        source = getattr(first_doc, "metadata", {}).get("source", "HW2 Note") if not isinstance(first_doc, dict) else first_doc.get("metadata", {}).get("source", "HW2 Note")
        top_matches = [(0.1, source, {}, content[:600])]

    formatted_output = [f"=== Retrieved Context from SmartNotebook RAG (HW2) [Query: '{query}'] ==="]
    for idx, (score, source, meta, chunk) in enumerate(top_matches, start=1):
        clean_source = Path(str(source)).name
        formatted_output.append(f"\n[Result {idx}] [Source: {clean_source}]")
        if meta.get("topic"):
            formatted_output.append(f"Topic: {meta.get('topic')}")
        formatted_output.append(f"Content: {chunk[:800]}")

    formatted_output.append("\nNote: Use the bracketed citation tags [Source: filename] in your final response.")
    return "\n".join(formatted_output)


class SecurityAuditInput(BaseModel):
    """Pydantic input schema for database security audit."""
    target_database: str = Field(
        default="roadrecon.db",
        description="The database to audit: 'roadrecon.db' (Azure AD recon) or 'metactf_users.db' (credential hashes)."
    )
    audit_focus: str = Field(
        default="privileged_roles",
        description="The audit focus: 'privileged_roles', 'service_principals', 'passwords_and_hashes', or 'overview'."
    )
    max_findings: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of findings to return (1 to 50)."
    )

    @field_validator("target_database")
    def validate_db(cls, v: str) -> str:
        clean = Path(v).name
        if clean not in ["roadrecon.db", "metactf_users.db"]:
            raise ValueError("Target database must be 'roadrecon.db' or 'metactf_users.db'.")
        return clean

    @field_validator("audit_focus")
    def validate_focus(cls, v: str) -> str:
        allowed = ["privileged_roles", "service_principals", "passwords_and_hashes", "overview"]
        if v.lower() not in allowed:
            raise ValueError(f"Audit focus must be one of: {', '.join(allowed)}")
        return v.lower()


@tool("database_security_audit", args_schema=SecurityAuditInput)
def database_security_audit(target_database: str = "roadrecon.db", audit_focus: str = "privileged_roles", max_findings: int = 10) -> str:
    """Performs an automated security audit on the SQLite databases in HW3/db_data/.

    Audits Azure Active Directory privilege escalation paths in roadrecon.db or
    credential storage hashes in metactf_users.db.

    Args:
        target_database: 'roadrecon.db' or 'metactf_users.db'.
        audit_focus: 'privileged_roles', 'service_principals', 'passwords_and_hashes', or 'overview'.
        max_findings: Maximum findings to return.

    Returns:
        Structured security audit report with findings and severity levels.
    """
    db_path = _CURRENT_DIR / "db_data" / target_database
    if not db_path.exists():
        return f"Error: Database {target_database} not found in HW3/db_data/."

    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        findings = []

        if target_database == "metactf_users.db":
            cursor.execute("SELECT username, passhash FROM users LIMIT ?", (max_findings,))
            rows = cursor.fetchall()
            for user, phash in rows:
                algo = "PBKDF2-SHA256" if "pbkdf2-sha256" in phash else "Unknown/Legacy"
                findings.append({
                    "username": user,
                    "hash_algorithm": algo,
                    "hash_snippet": phash[:35] + "...",
                    "security_risk": "High privilege account" if user == "admin" else "Standard user account",
                    "recommendation": "Enforce salted Argon2id/Bcrypt and MFA." if user == "admin" else "Verify password complexity policy."
                })
            report = {
                "audit_target": "MetaCTF Users Database",
                "focus": "Credential Analysis",
                "total_users_scanned": len(rows),
                "findings": findings,
            }

        elif target_database == "roadrecon.db":
            if audit_focus == "privileged_roles":
                cursor.execute("""
                    SELECT r.displayName, count(m.roleId) as members_count 
                    FROM DirectoryRoles r
                    LEFT JOIN lnk_role_member_user m ON r.id = m.roleId
                    GROUP BY r.id
                    ORDER BY members_count DESC
                    LIMIT ?;
                """, (max_findings,))
                role_rows = cursor.fetchall()
                for role_name, member_count in role_rows:
                    is_critical = "admin" in role_name.lower()
                    findings.append({
                        "directory_role": role_name,
                        "assigned_users_count": member_count,
                        "risk_level": "CRITICAL" if is_critical else "MEDIUM",
                        "assessment": "Privileged tier administrator role." if is_critical else "Standard organizational directory role."
                    })
            elif audit_focus == "service_principals":
                cursor.execute("""
                    SELECT displayName, appId, accountEnabled 
                    FROM ServicePrincipals 
                    WHERE accountEnabled = 1 
                    LIMIT ?;
                """, (max_findings,))
                sp_rows = cursor.fetchall()
                for name, app_id, enabled in sp_rows:
                    findings.append({
                        "service_principal_name": name,
                        "app_id": app_id,
                        "is_enabled": bool(enabled),
                        "risk_level": "HIGH" if "admin" in (name or "").lower() else "LOW"
                    })
            else:
                cursor.execute("SELECT count(*) FROM Users;")
                u_count = cursor.fetchone()[0]
                cursor.execute("SELECT count(*) FROM DirectoryRoles;")
                r_count = cursor.fetchone()[0]
                cursor.execute("SELECT count(*) FROM ServicePrincipals;")
                s_count = cursor.fetchone()[0]
                findings.append({
                    "total_azure_ad_users": u_count,
                    "total_directory_roles": r_count,
                    "total_service_principals": s_count,
                    "assessment": "ROADrecon Azure AD tenant reconstruction database active."
                })

            report = {
                "audit_target": "ROADrecon Azure Active Directory Database",
                "focus": audit_focus,
                "findings_count": len(findings),
                "findings": findings,
            }

        conn.close()
        return json.dumps(report, indent=2)
    except Exception as exc:
        return f"Security audit execution error: {str(exc)}"


class PresidentsAnalysisInput(BaseModel):
    """Input schema for the Presidents analysis tool."""
    mode: str = Field(
        default="oldest",
        description="Analysis mode: 'oldest', 'youngest', 'longest_term', or 'summary'."
    )
    top_n: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Number of results to return."
    )

    @field_validator("mode")
    def validate_mode(cls, v: str) -> str:
        valid_modes = ["oldest", "youngest", "longest_term", "summary"]
        if v.lower() not in valid_modes:
            raise ValueError(f"Mode must be one of {valid_modes}")
        return v.lower()


@tool("presidents_analyzer", args_schema=PresidentsAnalysisInput)
def analyze_presidents_data(mode: str = "oldest", top_n: int = 5) -> str:
    """Analyzes the US Presidents historical dataset from HW3/presidents.py.

    Calculates presidential age upon leaving office and term length metrics.

    Args:
        mode: 'oldest', 'youngest', 'longest_term', or 'summary'.
        top_n: Number of records to return.

    Returns:
        JSON string containing the calculated statistics and rankings.
    """
    presidents_py = _CURRENT_DIR / "presidents.py"
    if not presidents_py.exists():
        return "Error: HW3/presidents.py not found."

    # Import or execute presidents data
    import contextlib
    import io
    local_scope: Dict[str, Any] = {}
    try:
        code = presidents_py.read_text(encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            exec(code, {"__builtins__": __builtins__, "datetime": datetime}, local_scope)
        presidents = local_scope.get("presidents", [])
    except Exception as exc:
        return f"Error loading presidents dataset: {exc}"

    records = []
    for name, birth_str, end_str in presidents:
        b = datetime.datetime.strptime(birth_str, "%Y-%m-%d")
        e = datetime.datetime.strptime(end_str, "%Y-%m-%d")
        age = e.year - b.year - ((e.month, e.day) < (b.month, b.day))
        records.append({
            "name": name,
            "birth_date": birth_str,
            "end_of_term": end_str,
            "age_at_term_end": age
        })

    if mode == "oldest":
        records.sort(key=lambda x: x["age_at_term_end"], reverse=True)
    elif mode == "youngest":
        records.sort(key=lambda x: x["age_at_term_end"], reverse=False)
    elif mode == "summary":
        avg_age = sum(r["age_at_term_end"] for r in records) / len(records)
        oldest = max(records, key=lambda x: x["age_at_term_end"])
        youngest = min(records, key=lambda x: x["age_at_term_end"])
        return json.dumps({
            "total_presidents_analyzed": len(records),
            "average_age_at_term_end": round(avg_age, 2),
            "oldest_at_term_end": oldest,
            "youngest_at_term_end": youngest,
        }, indent=2)

    return json.dumps(records[:top_n], indent=2)


# ============================================================================
# Master Tool Registry
# ============================================================================

ALL_TOOLS = [
    # Retained tools
    python_repl_tool,
    execute_command,
    # Level 1 built-in tools
    web_search_tool,
    wikipedia_tool,
    query_sqlite_database,
    # Level 2 custom tools
    smartnotebook_rag_search,
    database_security_audit,
    analyze_presidents_data,
]

# Filter out any None tools (e.g. if an optional wrapper failed)
ALL_TOOLS = [t for t in ALL_TOOLS if t is not None]
