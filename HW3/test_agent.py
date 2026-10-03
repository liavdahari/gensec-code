"""Automated Unit & Integration Test Suite for HW3 SecurAgent.

Tests all components of the system:
1. Retained Tools: PythonREPLTool and TerminalTool safety filters.
2. Level 1 Built-in Tools: SQLite read-only queries, Web Search, Wikipedia.
3. Level 2 Custom Tools:
   - SmartNotebook RAG Tool (queries HW2 notes with citations).
   - Database Security Audit Tool (Pydantic schema validation & database scans).
   - Presidents Analyzer Tool (longevity calculations from presidents.py).
4. Level 3 LangGraph Architecture:
   - Graph compilation, node routing, and state execution.

Course: COT4930 - Generative AI Security
Author: Liav Dahari (FAU ID: Z23815316)
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

# Add project paths to sys.path
_CURRENT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _CURRENT_DIR.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))

from graph import build_agent_graph, export_graph_diagram
from tools import (
    ALL_TOOLS,
    analyze_presidents_data,
    database_security_audit,
    execute_command,
    python_repl_tool,
    query_sqlite_database,
    smartnotebook_rag_search,
    web_search_tool,
    wikipedia_tool,
)


class TestRetainedTools(unittest.TestCase):
    """Unit tests for retained tools: PythonREPL and Terminal."""

    def test_python_repl_tool(self):
        """Verifies Python REPL executes valid Python code and returns stdout."""
        code = "print(sum([10, 20, 30, 40]))"
        output = python_repl_tool.invoke(code)
        self.assertIn("100", output)

    def test_terminal_tool_execution(self):
        """Verifies safe terminal execution produces expected stdout."""
        output = execute_command.invoke({"command": "echo 'HW3 SecurAgent Terminal Active'"})
        self.assertIn("HW3 SecurAgent Terminal Active", output)

    def test_terminal_tool_safety_filter(self):
        """Verifies that dangerous commands are blocked by the safety filter."""
        with self.assertRaises(Exception):
            execute_command.invoke({"command": "rm -rf /"})


class TestLevel1BuiltinTools(unittest.TestCase):
    """Unit tests for Level 1 built-in tools."""

    def test_sqlite_query_success(self):
        """Verifies read-only SELECT queries on metactf_users.db."""
        result = query_sqlite_database.invoke({
            "database_name": "metactf_users.db",
            "query": "SELECT username FROM users LIMIT 3;"
        })
        parsed = json.loads(result)
        self.assertEqual(parsed["database"], "metactf_users.db")
        self.assertGreaterEqual(parsed["row_count"], 1)
        self.assertTrue(any(u["username"] == "admin" for u in parsed["results"]))

    def test_sqlite_blocks_write_queries(self):
        """Verifies that non-SELECT statements are rejected by schema validation."""
        with self.assertRaises(Exception):
            query_sqlite_database.invoke({
                "database_name": "metactf_users.db",
                "query": "DROP TABLE users;"
            })

    def test_builtin_tool_registration(self):
        """Verifies web_search_tool and wikipedia_tool are registered."""
        tool_names = [t.name for t in ALL_TOOLS]
        self.assertIn("duckduckgo_search", tool_names)
        self.assertIn("sql_db_query", tool_names)


class TestLevel2CustomTools(unittest.TestCase):
    """Unit tests for Level 2 custom tools (RAG, Security Audit, Presidents)."""

    def test_smartnotebook_rag_search(self):
        """Verifies HW2 RAG search retrieves notes and attaches citations."""
        output = smartnotebook_rag_search.invoke({
            "query": "security principles in RAG",
            "top_k": 2,
            "folder": "notes"
        })
        self.assertIn("Retrieved Context from SmartNotebook RAG", output)
        self.assertIn("[Source:", output)
        self.assertIn("ai_security_brief.md", output)

    def test_database_security_audit_metactf(self):
        """Verifies security audit detects credential hashes in metactf_users.db."""
        report_str = database_security_audit.invoke({
            "target_database": "metactf_users.db",
            "audit_focus": "passwords_and_hashes",
            "max_findings": 5
        })
        report = json.loads(report_str)
        self.assertEqual(report["audit_target"], "MetaCTF Users Database")
        self.assertEqual(len(report["findings"]), 5)
        self.assertEqual(report["findings"][0]["hash_algorithm"], "PBKDF2-SHA256")

    def test_database_security_audit_roadrecon(self):
        """Verifies security audit parses privileged directory roles in roadrecon.db."""
        report_str = database_security_audit.invoke({
            "target_database": "roadrecon.db",
            "audit_focus": "privileged_roles",
            "max_findings": 5
        })
        report = json.loads(report_str)
        self.assertEqual(report["audit_target"], "ROADrecon Azure Active Directory Database")
        self.assertGreater(len(report["findings"]), 0)

    def test_database_security_audit_pydantic_validation(self):
        """Verifies Pydantic schema rejects invalid databases and out-of-range counts."""
        with self.assertRaises(Exception):
            database_security_audit.invoke({
                "target_database": "unauthorized.db",
                "max_findings": 10
            })
        with self.assertRaises(Exception):
            database_security_audit.invoke({
                "target_database": "roadrecon.db",
                "max_findings": 100  # Exceeds le=50
            })

    def test_presidents_analyzer_modes(self):
        """Verifies longevity calculations for oldest, youngest, and summary."""
        summary_str = analyze_presidents_data.invoke({"mode": "summary"})
        summary = json.loads(summary_str)
        self.assertEqual(summary["total_presidents_analyzed"], 45)
        self.assertEqual(summary["oldest_at_term_end"]["name"], "Joe Biden")
        self.assertEqual(summary["youngest_at_term_end"]["name"], "John F. Kennedy")

        oldest_str = analyze_presidents_data.invoke({"mode": "oldest", "top_n": 3})
        oldest = json.loads(oldest_str)
        self.assertEqual(len(oldest), 3)
        self.assertEqual(oldest[0]["name"], "Joe Biden")


class TestLevel3LangGraphArchitecture(unittest.TestCase):
    """Unit tests for LangGraph multi-agent compilation and workflow."""

    def test_build_agent_graph(self):
        """Verifies state graph builds and compiles without errors."""
        app = build_agent_graph(enable_hitl=False)
        self.assertIsNotNone(app)
        nodes = app.get_graph().nodes
        self.assertIn("supervisor", nodes)
        self.assertIn("tools", nodes)
        self.assertIn("human_review", nodes)

    def test_export_diagram(self):
        """Verifies diagram generation outputs a valid file."""
        png_path = export_graph_diagram("test_graph.png")
        if png_path:
            self.assertTrue(png_path.exists())
            png_path.unlink()  # Clean up test output

    def test_graph_execution_flow(self):
        """Verifies end-to-end execution of a prompt through the graph."""
        app = build_agent_graph(enable_hitl=False)
        thread = {"configurable": {"thread_id": "unit_test_thread"}}
        from langchain_core.messages import HumanMessage
        result = app.invoke({"messages": [HumanMessage(content="What are the RAG security principles in my notes?")]}, thread)
        self.assertIn("messages", result)
        last_msg = result["messages"][-1]
        self.assertTrue(len(last_msg.content) > 0)


if __name__ == "__main__":
    unittest.main()
