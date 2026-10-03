"""SecurAgent: Multi-Agent LangGraph System with Human-in-the-Loop & RAG.

Main application entry point for Homework 3.

Key Capabilities:
1. Level 1: Integrates built-in tools (DuckDuckGo search, Wikipedia, SQLite DB).
2. Level 2: Integrates custom tools (HW2 SmartNotebook RAG with citations,
   Pydantic-validated security auditing for Azure AD ROADrecon and MetaCTF databases,
   and presidential statistics analysis).
3. Level 3: Stateful cooperative Multi-Agent LangGraph architecture with
   Supervisor orchestration, ToolNode execution, and optional Human-in-the-Loop review.
4. Retains both PythonREPLTool and safe Terminal tool.

Course: COT4930 - Generative AI Security
Author: Liav Dahari (FAU ID: Z23815316)
Institution: Florida Atlantic University
"""

from __future__ import annotations

import argparse
import os
import readline
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

# Ensure HW3 package can be found
_CURRENT_DIR = Path(__file__).resolve().parent
if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(_CURRENT_DIR.parent / ".env")
    load_dotenv(_CURRENT_DIR / ".env")
except ImportError:
    pass

from graph import build_agent_graph, export_graph_diagram, get_llm
from tools import ALL_TOOLS

console = Console()


def print_banner(hitl_enabled: bool) -> None:
    """Displays a rich styled application banner and configuration overview."""
    banner_text = (
        "[bold cyan]SecurAgent: Multi-Agent LangGraph System[/bold cyan]\n"
        "[italic]COT4930 Generative AI Security - Homework 3[/italic]\n"
        "Student: Liav Dahari (FAU ID: Z23815316)"
    )
    console.print(Panel(banner_text, border_style="bright_blue", expand=False))

    # Tool status table
    table = Table(title="Configured Tool Suite", border_style="cyan", show_lines=True)
    table.add_column("Tier / Category", style="bold magenta", width=22)
    table.add_column("Tool Name", style="bold green", width=24)
    table.add_column("Description", style="white")

    table.add_row("Retained Tool", "Python_REPL", "Python code execution & numerical analysis")
    table.add_row("Retained Tool", "terminal_tool", "Safe shell command execution with timeout guard")
    table.add_row("Level 1 (Built-in)", "duckduckgo_search", "Live web search (no API key required)")
    table.add_row("Level 1 (Built-in)", "wikipedia_search", "Encyclopedic conceptual search")
    table.add_row("Level 1 (Built-in)", "sql_db_query", "Read-only SQL queries on SQLite databases")
    table.add_row("Level 2 (Custom RAG)", "smartnotebook_rag_search", "Queries HW2 research notes & datasets with [Source] tags")
    table.add_row("Level 2 (Custom Security)", "database_security_audit", "Pydantic-validated audit of ROADrecon Azure AD & MetaCTF")
    table.add_row("Level 2 (Custom Data)", "presidents_analyzer", "Analyzes presidential longevity & term statistics")

    console.print(table)

    mode_status = "[bold yellow]ENABLED[/bold yellow] (Human approval required for terminal & REPL)" if hitl_enabled else "[bold green]AUTONOMOUS[/bold green] (Direct tool execution)"
    console.print(f"[bold]Execution Mode:[/bold] {mode_status}")
    console.print("[dim]Type your prompt below. Type 'exit', 'quit', or press Enter on an empty line to exit.[/dim]\n")


def handle_human_feedback(app: Any, thread: Dict[str, Any]) -> None:
    """Prompts the user for approval or modification of pending sensitive tool calls."""
    state = app.get_state(thread)
    if not state.values.get("messages"):
        return

    last_msg = state.values["messages"][-1]
    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
        for tool_call in last_msg.tool_calls:
            t_name = tool_call.get("name", "tool")
            t_args = tool_call.get("args", {})
            console.print(
                Panel(
                    f"[bold yellow]Tool Call Pending Approval:[/bold yellow] [bold cyan]{t_name}[/bold cyan]\n"
                    f"[bold]Arguments:[/bold] {t_args}",
                    title="⚠️  Human Review Required",
                    border_style="yellow"
                )
            )

            user_choice = input("\nApprove execution? [y/N] or type feedback to revise: ").strip()
            if user_choice.lower() in ["y", "yes"]:
                console.print("[green]✓ Tool execution approved by user.[/green]")
                app.update_state(thread, {"human_approved": True}, as_node="human_review")
                return

            # User provided modification or rejection feedback
            feedback_msg = user_choice if user_choice else "User declined execution of this action."
            console.print(f"[red]✗ Tool call rejected. Sending feedback to supervisor: '{feedback_msg}'[/red]")
            
            rejection_message = ToolMessage(
                content=f"Human reviewer rejected tool '{t_name}'. Feedback: {feedback_msg}",
                tool_call_id=tool_call.get("id", "human_review_id"),
                name=t_name,
            )
            app.update_state(
                thread,
                {"messages": [rejection_message], "human_approved": False},
                as_node="human_review",
            )


def process_query(app: Any, query: str, thread_id: str = "default_session", hitl_enabled: bool = False) -> None:
    """Executes a single user query through the compiled LangGraph workflow.

    Args:
        app: Compiled LangGraph application.
        query: Human prompt to answer.
        thread_id: Memory session thread identifier.
        hitl_enabled: Whether human-in-the-loop validation is active.
    """
    thread = {"configurable": {"thread_id": thread_id}}
    inputs = {"messages": [HumanMessage(content=query)], "human_approved": not hitl_enabled}

    console.print(f"\n[bold green]User Query:[/bold green] {query}")

    try:
        # Stream graph execution events
        for event in app.stream(inputs, thread, stream_mode="updates"):
            for node_name, node_update in event.items():
                if node_name == "supervisor":
                    msgs = node_update.get("messages", [])
                    for m in msgs:
                        if isinstance(m, AIMessage):
                            if m.tool_calls:
                                for tc in m.tool_calls:
                                    console.print(f"  [bold cyan]🛠️  Supervisor Scheduled Tool:[/bold cyan] [bold]{tc['name']}[/bold] (Args: {tc['args']})")
                            elif m.content:
                                console.print(Panel(Markdown(m.content), title="🤖 SecurAgent Final Response", border_style="green"))

                elif node_name == "tools":
                    msgs = node_update.get("messages", [])
                    for m in msgs:
                        preview = str(m.content)[:300] + ("..." if len(str(m.content)) > 300 else "")
                        console.print(f"  [bold purple]✅ Tool Execution Output ({m.name}):[/bold purple]\n    [dim]{preview}[/dim]")

        # Handle pending human review interrupts
        while hitl_enabled and app.get_state(thread).next:
            handle_human_feedback(app, thread)
            for event in app.stream(None, thread, stream_mode="updates"):
                for node_name, node_update in event.items():
                    if node_name == "supervisor":
                        msgs = node_update.get("messages", [])
                        for m in msgs:
                            if isinstance(m, AIMessage) and m.content:
                                console.print(Panel(Markdown(m.content), title="🤖 SecurAgent Final Response", border_style="green"))
                    elif node_name == "tools":
                        msgs = node_update.get("messages", [])
                        for m in msgs:
                            preview = str(m.content)[:300] + ("..." if len(str(m.content)) > 300 else "")
                            console.print(f"  [bold purple]✅ Tool Output ({m.name}):[/bold purple]\n    [dim]{preview}[/dim]")

    except Exception as exc:
        console.print(f"[bold red]Execution error:[/bold red] {exc}")


def main() -> None:
    """CLI entrypoint with argument parsing."""
    parser = argparse.ArgumentParser(
        description="SecurAgent: Multi-Agent LangGraph System (HW3)"
    )
    parser.add_argument(
        "-q", "--query",
        type=str,
        default=None,
        help="Run a single prompt directly and exit."
    )
    parser.add_argument(
        "--hitl",
        action="store_true",
        help="Enable Human-in-the-Loop approval for terminal and python tool calls."
    )
    parser.add_argument(
        "--draw",
        action="store_true",
        help="Export the graph diagram to agent_graph.png and print ASCII structure."
    )

    args = parser.parse_args()

    # Build compiled LangGraph workflow
    app = build_agent_graph(enable_hitl=args.hitl)

    if args.draw:
        console.print("[bold cyan]Exporting LangGraph Architecture Diagram...[/bold cyan]")
        png_path = export_graph_diagram("agent_graph.png")
        if png_path:
            console.print(f"[green]✓ Diagram saved to:[/green] {png_path}")
        console.print("\n[bold]Graph ASCII Topology:[/bold]")
        console.print(app.get_graph().draw_ascii())
        if not args.query:
            return

    # Banner display
    print_banner(hitl_enabled=args.hitl)

    # Single-shot execution mode
    if args.query:
        process_query(app, args.query, thread_id="cli_single_shot", hitl_enabled=args.hitl)
        return

    # Interactive REPL mode
    session_id = f"session_{os.getpid()}"
    while True:
        try:
            prompt = input("SecurAgent>> ").strip()
            if not prompt or prompt.lower() in ["exit", "quit"]:
                console.print("[bold yellow]Exiting SecurAgent. Goodbye![/bold yellow]")
                break
            process_query(app, prompt, thread_id=session_id, hitl_enabled=args.hitl)
        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold yellow]Session terminated by user.[/bold yellow]")
            break


if __name__ == "__main__":
    main()
