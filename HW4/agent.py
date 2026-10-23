"""SecOps MCP Agent - Model Context Protocol Client Orchestrator.

HW4: MCP-based Multi-Server Security Coordinating Agent
Course: COT4930 - Generative AI Security
Author: Liav Dahari (FAU ID: Z23815316)
Institution: Florida Atlantic University
Pattern Adopted: 04_MCP/01_sqlite/01_stdio_mcp_client.py & 04_MCP/03_git

This module coordinates tools between a custom FastMCP SecOps server
and an external published MCP server (Chrome DevTools MCP).
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession


def get_server_configs() -> tuple[StdioServerParameters, StdioServerParameters]:
    """Configure StdioServerParameters for published and custom MCP servers."""
    base_dir = Path(__file__).resolve().parent

    # Server 1: Published Google Chrome DevTools MCP (Pattern from 04_MCP/03_git)
    chrome_params = StdioServerParameters(
        command="npx",
        args=["-y", "chrome-devtools-mcp@latest", "--headless", "--no-usage-statistics"],
        env=os.environ.copy(),
    )

    # Server 2: Custom SecOps FastMCP Server (Pattern from 04_MCP/01_sqlite)
    custom_params = StdioServerParameters(
        command=sys.executable,
        args=[str(base_dir / "mcp-server.py"), "stdio"],
        env=os.environ.copy(),
    )

    return chrome_params, custom_params


async def list_all_tools() -> None:
    """Connect to both MCP servers and display their complete tool catalogs."""
    chrome_params, custom_params = get_server_configs()

    print("=" * 70)
    print("      DISCOVERING TOOLS ACROSS MULTI-SERVER MCP ARCHITECTURE")
    print("=" * 70)

    # 1. Custom SecOps Tools
    print("\n[*] Server 1: Custom FastMCP Server (HW4/mcp-server.py)")
    async with stdio_client(custom_params) as (read_s, write_s):
        async with ClientSession(read_s, write_s) as sec_session:
            await sec_session.initialize()
            sec_tools = await sec_session.list_tools()
            for idx, tool in enumerate(sec_tools.tools, 1):
                desc = tool.description.replace("\n", " ") if tool.description else ""
                print(f"  {idx}. {tool.name:26s} - {desc[:55]}...")

    # 2. Chrome DevTools
    print("\n[*] Server 2: Published Chrome DevTools MCP Server (Google)")
    async with stdio_client(chrome_params) as (read_c, write_c):
        async with ClientSession(read_c, write_c) as chrome_session:
            await chrome_session.initialize()
            c_tools = await chrome_session.list_tools()
            print(f"  Total tools available: {len(c_tools.tools)}")
            for idx, tool in enumerate(c_tools.tools, 1):
                desc = tool.description.replace("\n", " ") if tool.description else ""
                print(f"  {idx:2d}. {tool.name:26s} - {desc[:55]}...")

    print("\n" + "=" * 70)


async def run_security_audit(target_url: str = "https://example.com") -> None:
    """Coordinate Chrome DevTools MCP and SecOps MCP to perform an automated security audit.

    Adopts the StdioServerParameters, stdio_client, and ClientSession patterns
    from 04_MCP/01_sqlite/01_stdio_mcp_client.py.
    """
    chrome_params, custom_params = get_server_configs()

    print("=" * 70)
    print("   COORDINATING MULTI-SERVER MCP SECURITY AUDIT PIPELINE")
    print(f"   Target URL: {target_url}")
    print("   Student:    Liav Dahari (FAU ID: Z23815316)")
    print("   Course:     COT4930 - Generative AI Security")
    print("=" * 70)

    # -------------------------------------------------------------
    # PHASE 1: Browser Navigation & DOM Extraction (Chrome DevTools MCP)
    # -------------------------------------------------------------
    print("\n[Phase 1] Published Server: Chrome DevTools MCP")
    print("  -> Initializing stdio client session...")
    page_text = ""

    async with stdio_client(chrome_params) as (read_c, write_c):
        async with ClientSession(read_c, write_c) as chrome_session:
            await chrome_session.initialize()
            print("  -> Connected to Chrome DevTools MCP successfully.")

            # 1. Determine active page
            page_id = 1

            # 2. Navigate to target URL
            print(f"  -> Calling tool 'navigate_page' with url='{target_url}' (pageId={page_id})...")
            try:
                await chrome_session.call_tool("navigate_page", arguments={"pageId": page_id, "url": target_url})
            except Exception:
                await chrome_session.call_tool("navigate_page", arguments={"url": target_url})
            print(f"  [+] Page navigated successfully.")

            # 3. Extract DOM accessibility text snapshot
            print(f"  -> Calling tool 'take_snapshot' (pageId={page_id}) to extract live DOM content...")
            try:
                snapshot_result = await chrome_session.call_tool("take_snapshot", arguments={"pageId": page_id})
            except Exception:
                snapshot_result = await chrome_session.call_tool("take_snapshot", arguments={})

            if snapshot_result and snapshot_result.content:
                first_item = snapshot_result.content[0]
                page_text = first_item.text if hasattr(first_item, "text") else str(first_item)
                print(f"  [+] Captured DOM text snapshot ({len(page_text)} bytes).")
                clean_preview = " ".join(line.strip() for line in page_text.splitlines() if line.strip())[:110]
                print(f"      Snapshot content: \"{clean_preview}...\"")

    # -------------------------------------------------------------
    # PHASE 2: Security Analysis & Audit (Custom FastMCP SecOps Server)
    # -------------------------------------------------------------
    print("\n[Phase 2] Custom Server: SecOps FastMCP Tools")
    print("  -> Initializing stdio client session...")

    async with stdio_client(custom_params) as (read_s, write_s):
        async with ClientSession(read_s, write_s) as sec_session:
            await sec_session.initialize()
            print("  -> Connected to SecOps FastMCP Server successfully.")

            # Tool 1: Audit HTTP Defensive Headers
            print("\n  [Audit 1/3] Calling 'check_url_security'...")
            headers_call = await sec_session.call_tool("check_url_security", arguments={"url": target_url})
            headers_text = headers_call.content[0].text if hasattr(headers_call.content[0], "text") else str(headers_call.content[0])
            headers_data = json.loads(headers_text) if isinstance(headers_text, str) and headers_text.startswith("{") else headers_text

            print("  [+] Defensive Headers Assessment:")
            if isinstance(headers_data, dict):
                print(f"      • Target URL:       {headers_data.get('url')}")
                print(f"      • HTTP Status:      {headers_data.get('status_code')}")
                print(f"      • HTTPS Enforced:   {headers_data.get('uses_https')}")
                print(f"      • HSTS Header:      {headers_data.get('has_strict_transport_security')}")
                print(f"      • CSP Header:       {headers_data.get('has_content_security_policy')}")
                print(f"      • X-Frame-Options:  {headers_data.get('has_x_frame_options')}")
                print(f"      • Verdict:          {headers_data.get('security_summary')}")
            else:
                print(f"      {headers_data}")

            # Tool 2: Scan Extracted DOM Content for Leaked Secrets
            print("\n  [Audit 2/3] Calling 'scan_text_for_secrets' on captured DOM snapshot...")
            secrets_call = await sec_session.call_tool("scan_text_for_secrets", arguments={"text": page_text})
            secrets_text = secrets_call.content[0].text if hasattr(secrets_call.content[0], "text") else str(secrets_call.content[0])
            secrets_data = json.loads(secrets_text) if isinstance(secrets_text, str) and secrets_text.startswith("{") else secrets_text

            print("  [+] DOM Secret Scanning Assessment:")
            if isinstance(secrets_data, dict):
                print(f"      • Characters Scanned: {secrets_data.get('text_length')}")
                print(f"      • Secrets Found:      {secrets_data.get('secrets_found_count')}")
                print(f"      • Findings:           {secrets_data.get('findings')}")
                print(f"      • Verdict:            {secrets_data.get('status')}")
            else:
                print(f"      {secrets_data}")

            # Tool 3: Cryptographic Hash Analysis
            sample_hashes = [
                ("5f4dcc3b5aa765d61d8327deb882cf99", "Admin hash sample"),
                ("$2b$12$e8OfO.h7K9oQ9YxYqX4kEu8L6aB6Jz3j4j2r9v7u5w4abc1234567890", "DB shadow sample"),
            ]
            print("\n  [Audit 3/3] Calling 'identify_hash_type' on candidate password hashes...")
            for h_val, label in sample_hashes:
                hash_call = await sec_session.call_tool("identify_hash_type", arguments={"hash_string": h_val})
                hash_text = hash_call.content[0].text if hasattr(hash_call.content[0], "text") else str(hash_call.content[0])
                hash_data = json.loads(hash_text) if isinstance(hash_text, str) and hash_text.startswith("{") else hash_text
                if isinstance(hash_data, dict):
                    print(f"      • {label} ({hash_data.get('hash')[:18]}...): Algorithm={hash_data.get('type')}, Status={hash_data.get('status')}")

    # -------------------------------------------------------------
    # SUMMARY & COMPLETION
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print("   AUDIT COMPLETE: MULTI-SERVER MCP COORDINATION SUCCESSFUL")
    print("=" * 70)


async def main() -> None:
    """CLI routing for the coordinating agent."""
    if len(sys.argv) > 1 and sys.argv[1] == "--list-tools":
        await list_all_tools()
    else:
        target = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
        await run_security_audit(target)


if __name__ == "__main__":
    asyncio.run(main())
