#!/usr/bin/env python3
"""MCP server for regwatch - Regulatory Research Subscription"""

import json
import os
from datetime import datetime, timedelta
from mcp.server import Server
from mcp.types import Tool, TextContent

app = Server("mcp-regwatch")

# Simulated regulatory database
REGULATIONS = {
    "eu": [
        {"id": "MICA-2024", "title": "Markets in Crypto-Assets Regulation", "jurisdiction": "EU", "status": "active", "effective_date": "2024-12-30", "summary": "Comprehensive framework for crypto-asset markets"},
        {"id": "TFR-2024", "title": "Transfer of Funds Regulation", "jurisdiction": "EU", "status": "active", "effective_date": "2024-12-30", "summary": "Travel rule for crypto transfers"},
        {"id": "DORA-2024", "title": "Digital Operational Resilience Act", "jurisdiction": "EU", "status": "active", "effective_date": "2025-01-17", "summary": "ICT risk management for financial entities"},
    ],
    "us": [
        {"id": "SEC-2024-001", "title": "SEC Crypto Custody Rule", "jurisdiction": "US", "status": "proposed", "effective_date": "2025-06-01", "summary": "Custody requirements for crypto assets"},
        {"id": "FINCEN-2024", "title": "FinCEN Crypto Travel Rule", "jurisdiction": "US", "status": "active", "effective_date": "2024-01-01", "summary": "Travel rule for crypto transactions"},
    ],
    "uk": [
        {"id": "FCA-2024", "title": "FCA Crypto Asset Registration", "jurisdiction": "UK", "status": "active", "effective_date": "2024-01-01", "summary": "Registration regime for crypto businesses"},
    ],
    "sg": [
        {"id": "MAS-2024", "title": "MAS Stablecoin Framework", "jurisdiction": "SG", "status": "consultation", "effective_date": "2025-06-01", "summary": "Regulatory framework for stablecoins"},
    ],
}

app = Server("mcp-regwatch")

TOOLS = [
    Tool(
        name="search_regulations",
        description="Search regulations by keyword, jurisdiction, or status",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "jurisdiction": {"type": "string", "enum": ["eu", "us", "uk", "sg", "all"], "default": "all", "description": "Jurisdiction to search"},
                "status": {"type": "string", "enum": ["active", "proposed", "consultation", "all"], "default": "all", "description": "Regulation status"},
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="get_recent_changes",
        description="Get recent regulatory changes within a time window",
        inputSchema={
            "type": "object",
            "properties": {
                "jurisdiction": {"type": "string", "enum": ["eu", "us", "uk", "sg", "all"], "default": "all", "description": "Jurisdiction"},
                "days": {"type": "integer", "default": 30, "description": "Days to look back"},
            },
            "required": ["jurisdiction"]
        }
    ),
    Tool(
        name="get_compliance_deadlines",
        description="Get upcoming compliance deadlines",
        inputSchema={
            "type": "object",
            "properties": {
                "jurisdiction": {"type": "string", "enum": ["eu", "us", "uk", "sg", "all"], "default": "all", "description": "Jurisdiction"},
                "days_ahead": {"type": "integer", "default": 90, "description": "Days ahead to check"},
            },
            "required": ["jurisdiction"]
        }
    )
]

app = Server("mcp-regwatch")

@app.list_tools()
async def list_tools():
    return TOOLS

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "search_regulations":
        query = arguments.get("query", "").lower()
        jurisdiction = arguments.get("jurisdiction", "all")
        status = arguments.get("status", "all")
        
        results = []
        jurisdictions = [jurisdiction] if jurisdiction != "all" else ["eu", "us", "uk", "sg"]
        
        for jur in jurisdictions:
            for reg in REGULATIONS.get(jur, []):
                if status != "all" and reg["status"] != status:
                    continue
                if query in reg["title"].lower() or query in reg["summary"].lower() or query in reg["id"].lower():
                    results.append(reg)
        
        result = {
            "status": "ok",
            "tool": "search_regulations",
            "query": arguments.get("query"),
            "jurisdiction": jurisdiction,
            "status_filter": status,
            "count": len(results),
            "results": results
        }
        return [TextContent(type="text", text=json.dumps(result))]
    
    elif name == "get_recent_changes":
        jurisdiction = arguments.get("jurisdiction")
        days = arguments.get("days", 30)
        
        cutoff = datetime.now() - timedelta(days=days)
        results = []
        
        jurisdictions = [jurisdiction] if jurisdiction != "all" else ["eu", "us", "uk", "sg"]
        
        for jur in jurisdictions:
            for reg in REGULATIONS.get(jur, []):
                try:
                    eff_date = datetime.strptime(reg["effective_date"], "%Y-%m-%d")
                    if eff_date >= cutoff:
                        results.append(reg)
                except:
                    pass
        
        result = {
            "status": "ok",
            "tool": "get_recent_changes",
            "jurisdiction": jurisdiction,
            "days": days,
            "count": len(results),
            "results": results
        }
        return [TextContent(type="text", text=json.dumps(result))]
    
    elif name == "get_compliance_deadlines":
        jurisdiction = arguments.get("jurisdiction")
        days_ahead = arguments.get("days_ahead", 90)
        
        future = datetime.now() + timedelta(days=days_ahead)
        results = []
        
        jurisdictions = [jurisdiction] if jurisdiction != "all" else ["eu", "us", "uk", "sg"]
        
        for jur in jurisdictions:
            for reg in REGULATIONS.get(jur, []):
                try:
                    eff_date = datetime.strptime(reg["effective_date"], "%Y-%m-%d")
                    if datetime.now() <= eff_date <= future:
                        results.append({
                            "regulation_id": reg["id"],
                            "title": reg["title"],
                            "jurisdiction": reg["jurisdiction"],
                            "deadline": reg["effective_date"],
                            "status": reg["status"],
                            "days_remaining": (eff_date - datetime.now()).days
                        })
                except:
                    pass
        
        results.sort(key=lambda x: x["deadline"])
        
        result = {
            "status": "ok",
            "tool": "get_compliance_deadlines",
            "jurisdiction": jurisdiction,
            "days_ahead": days_ahead,
            "count": len(results),
            "deadlines": results
        }
        return [TextContent(type="text", text=json.dumps(result))]
    
    return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

if __name__ == "__main__":
    import asyncio
    from mcp.server.stdio import stdio_server
    
    async def serve():
        reader, writer = await stdio_server()
        await app.run(reader, writer)
    
    asyncio.run(serve())