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
import os
import sys
from pathlib import Path
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession

# Chrome DevTools MCP Configuration (Pattern from 04_MCP/03_git stdio servers)
CHROME_DEVTOOLS_PARAMS = StdioServerParameters(
    command="npx",
    args=["-y", "chrome-devtools-mcp@latest", "--headless", "--no-usage-statistics"],
    env=os.environ.copy(),
)


async def verify_published_server() -> None:
    """Connect to published Chrome DevTools MCP and list available tools."""
    print("=" * 65)
    print("[*] Connecting to Chrome DevTools MCP Server over stdio...")
    print("=" * 65)

    async with stdio_client(CHROME_DEVTOOLS_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("[+] Successfully initialized session with Chrome DevTools MCP!")
            tools = await session.list_tools()
            print(f"[+] Discovered {len(tools.tools)} browser automation tools:\n")
            for idx, tool in enumerate(tools.tools, 1):
                desc = tool.description.replace("\n", " ") if tool.description else ""
                print(f" {idx:2d}. {tool.name:28s} - {desc[:58]}...")
    print("\n" + "=" * 65)
    print("[+] Published MCP Server verification complete!")
    print("=" * 65)


async def main() -> None:
    """Main CLI entry point."""
    await verify_published_server()


if __name__ == "__main__":
    asyncio.run(main())
