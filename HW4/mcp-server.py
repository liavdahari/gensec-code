"""SecOps MCP Server - Security Operations Tools Server.

HW4: Custom FastMCP Server
Course: COT4930 - Generative AI Security
Author: Liav Dahari (FAU ID: Z23815316)
Institution: Florida Atlantic University
Pattern Adopted: 04_MCP/01_sqlite/vulnerable_sqlite_mcp_server.py

This server exposes custom security audit tools using FastMCP over stdio.
"""

from fastmcp import FastMCP

# Initialize FastMCP Server instance
mcp = FastMCP("Simple-SecOps-Tools")

if __name__ == "__main__":
    mcp.run()
