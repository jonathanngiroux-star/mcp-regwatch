#!/usr/bin/env python3
"""
MCP RegWatch Server - Regulatory Research Subscription via MCP
"""

import json
import asyncio
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List
from pathlib import Path

from mcp.server import Server
from mcp.types import Tool, TextContent, ListToolsResult, CallToolResult

DB_PATH = Path(__file__).parent / "regwatch.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS regulations (
                id TEXT PRIMARY KEY,
                jurisdiction TEXT NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                source_url TEXT NOT NULL,
                published_at TEXT NOT NULL,
                effective_at TEXT,
                summary TEXT,
                tags TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS watchlists (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                jurisdictions TEXT NOT NULL,
                keywords TEXT,
                created_at TEXT NOT NULL
            )
        """)

init_db()

TOOLS = [
    Tool(
        name="search_regulations",
        description="Search regulations by keyword and jurisdiction",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "jurisdiction": {"type": "string", "description": "Jurisdiction (eu, us, uk, sg, ca, au, jp, ch)"}
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="get_recent_changes",
        description="Get recent regulatory changes for a jurisdiction",
        inputSchema={
            "type": "object",
            "properties": {
                "jurisdiction": {"type": "string", "description": "Jurisdiction code"},
                "days": {"type": "integer", "default": 7}
            },
            "required": ["jurisdiction"]
        }
    ),
    Tool(
        name="get_compliance_deadlines",
        description="Get upcoming compliance deadlines for a jurisdiction",
        inputSchema={
            "type": "object",
            "properties": {
                "jurisdiction": {"type": "string", "description": "Jurisdiction code"}
            },
            "required": ["jurisdiction"]
        }
    ),
    Tool(
        name="create_watchlist",
        description="Create a regulatory watchlist",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Watchlist name"},
                "jurisdictions": {"type": "array", "items": {"type": "string"}, "description": "Jurisdiction codes"},
                "keywords": {"type": "array", "items": {"type": "string"}, "description": "Keywords to watch"}
            },
            "required": ["name", "jurisdictions"]
        }
    ),
    Tool(
        name="list_watchlists",
        description="List all watchlists",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    )
]

async def list_tools_handler():
    from mcp.types import ListToolsResult
    return ListToolsResult(tools=TOOLS)

async def call_tool_handler(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    try:
        if name == "search_regulations":
            result = await search_regulations(arguments)
        elif name == "get_recent_changes":
            result = await get_recent_changes(arguments)
        elif name == "get_compliance_deadlines":
            result = await get_compliance_deadlines(arguments)
        elif name == "create_watchlist":
            result = await create_watchlist(arguments)
        elif name == "list_watchlists":
            result = await list_watchlists(arguments)
        else:
            return CallToolResult(content=[TextContent(type="text", text=f"Unknown tool: {name}")], isError=True)
        return CallToolResult(content=result)
    except Exception as e:
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {str(e)}")], isError=True)

async def search_regulations(args: Dict[str, Any]) -> List[TextContent]:
    query = args["query"].lower()
    jurisdiction = args.get("jurisdiction", "")
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        q = "SELECT * FROM regulations WHERE (title LIKE ? OR summary LIKE ? OR tags LIKE ?)"
        params = [f"%{query}%", f"%{query}%", f"%{query}%"]
        if jurisdiction:
            q += " AND jurisdiction = ?"
            params.append(jurisdiction)
        q += " ORDER BY published_at DESC LIMIT 20"
        rows = conn.execute(q, params).fetchall()
        results = [dict(r) for r in rows]
    
    return [TextContent(type="text", text=json.dumps({"query": query, "jurisdiction": jurisdiction, "results": results}, indent=2))]

async def get_recent_changes(args: Dict[str, Any]) -> List[TextContent]:
    jurisdiction = args["jurisdiction"]
    days = args.get("days", 7)
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        since = (datetime.now() - timedelta(days=days)).isoformat()
        rows = conn.execute("SELECT * FROM regulations WHERE jurisdiction = ? AND published_at >= ? ORDER BY published_at DESC", (jurisdiction, since)).fetchall()
        results = [dict(r) for r in rows]
    
    return [TextContent(type="text", text=json.dumps({"jurisdiction": jurisdiction, "days": days, "changes": results}, indent=2))]

async def get_compliance_deadlines(args: Dict[str, Any]) -> List[TextContent]:
    jurisdiction = args["jurisdiction"]
    
    # Simulated deadlines based on jurisdiction
    deadline_map = {
        "eu": [
            {"id": "eu-1", "regulation": "MiCA Article 30", "due": "2024-12-30", "type": "compliance"},
            {"id": "eu-2", "regulation": "Travel Rule Reporting", "due": "2024-12-30", "type": "reporting"},
            {"id": "eu-3", "regulation": "AML Directive 6", "due": "2025-01-15", "type": "compliance"},
        ],
        "us": [
            {"id": "us-1", "regulation": "SEC Crypto Custody Rule", "due": "2024-12-31", "type": "compliance"},
            {"id": "us-2", "regulation": "FinCEN Travel Rule", "due": "2025-01-01", "type": "reporting"},
        ],
        "uk": [
            {"id": "uk-1", "regulation": "FCA Crypto Registration", "due": "2024-12-31", "type": "compliance"},
        ],
        "sg": [
            {"id": "sg-1", "regulation": "MAS Stablecoin Framework", "due": "2025-03-31", "type": "compliance"},
        ],
    }
    
    deadlines = deadline_map.get(jurisdiction.lower(), [])
    
    return [TextContent(type="text", text=json.dumps({"jurisdiction": jurisdiction, "deadlines": deadlines}, indent=2))]

async def create_watchlist(args: Dict[str, Any]) -> List[TextContent]:
    name = args["name"]
    jurisdictions = args["jurisdictions"]
    keywords = args.get("keywords", [])
    
    watchlist_id = f"watchlist-{name.lower().replace(' ', '-')}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    now = datetime.now().isoformat()
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO watchlists (id, name, jurisdictions, keywords, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (watchlist_id, name, json.dumps(jurisdictions), json.dumps(keywords), now))
    
    return [TextContent(type="text", text=json.dumps({
        "watchlist_id": watchlist_id,
        "name": name,
        "jurisdictions": jurisdictions,
        "keywords": keywords
    }, indent=2))]

async def list_watchlists(args: Dict[str, Any]) -> List[TextContent]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM watchlists ORDER BY created_at DESC").fetchall()
        watchlists = [dict(r) for r in rows]
    
    return [TextContent(type="text", text=json.dumps({"watchlists": watchlists}, indent=2))]

from mcp.types import Tool, TextContent, ListToolsResult, CallToolResult

init_db()

TOOLS = [
    Tool(
        name="search_regulations",
        description="Search regulations by keyword and jurisdiction",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "jurisdiction": {"type": "string", "description": "Jurisdiction (eu, us, uk, sg, ca, au, jp, ch)"}
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="get_recent_changes",
        description="Get recent regulatory changes for a jurisdiction",
        inputSchema={
            "type": "object",
            "properties": {
                "jurisdiction": {"type": "string", "description": "Jurisdiction code"},
                "days": {"type": "integer", "default": 7}
            },
            "required": ["jurisdiction"]
        }
    ),
    Tool(
        name="get_compliance_deadlines",
        description="Get upcoming compliance deadlines for a jurisdiction",
        inputSchema={
            "type": "object",
            "properties": {
                "jurisdiction": {"type": "string", "description": "Jurisdiction code"}
            },
            "required": ["jurisdiction"]
        }
    ),
    Tool(
        name="create_watchlist",
        description="Create a regulatory watchlist",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Watchlist name"},
                "jurisdictions": {"type": "array", "items": {"type": "string"}, "description": "Jurisdiction codes"},
                "keywords": {"type": "array", "items": {"type": "string"}, "description": "Keywords to watch"}
            },
            "required": ["name", "jurisdictions"]
        }
    ),
    Tool(
        name="list_watchlists",
        description="List all watchlists",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    )
]

async def list_tools_handler():
    from mcp.types import ListToolsResult
    return ListToolsResult(tools=TOOLS)

async def call_tool_handler(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    try:
        if name == "search_regulations":
            result = await search_regulations(arguments)
        elif name == "get_recent_changes":
            result = await get_recent_changes(arguments)
        elif name == "get_compliance_deadlines":
            result = await get_compliance_deadlines(arguments)
        elif name == "create_watchlist":
            result = await create_watchlist(arguments)
        elif name == "list_watchlists":
            result = await list_watchlists(arguments)
        else:
            return CallToolResult(content=[TextContent(type="text", text=f"Unknown tool: {name}")], isError=True)
        return CallToolResult(content=result)
    except Exception as e:
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {str(e)}")], isError=True)

app = Server(
    name="mcp-regwatch",
    on_list_tools=lambda: list_tools_handler(),
    on_call_tool=lambda name, arguments: call_tool_handler(name, arguments)
)

if __name__ == "__main__":
    from mcp.server.stdio import stdio_server
    
    async def serve():
        server = await stdio_server()
        await app.run(server.stdin, server.stdout)
    
    asyncio.run(serve())