import pytest
import asyncio
import json
from datetime import datetime
from mcp_regwatch.server import (
    search_regulations, 
    get_recent_changes, 
    get_compliance_deadlines,
    create_watchlist,
    list_watchlists,
    list_tools_handler,
    call_tool_handler
)

@pytest.fixture
async def clean_db():
    import sqlite3
    from mcp_regwatch.server import DB_PATH
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM regulations")
        conn.execute("DELETE FROM watchlists")
    yield
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM regulations")
        conn.execute("DELETE FROM watchlists")

@pytest.mark.asyncio
async def test_list_tools():
    from mcp_regwatch.server import list_tools_handler
    from mcp.types import ListToolsResult
    result = await list_tools_handler()
    assert len(result.tools) == 5

@pytest.mark.asyncio
async def test_search_regulations(clean_db):
    from mcp_regwatch.server import search_regulations
    import sqlite3
    from mcp_regwatch.server import DB_PATH
    
    # Add test data
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO regulations (id, jurisdiction, title, category, severity, source_url, published_at, effective_at, summary, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("eu-1", "eu", "MiCA Regulation", "stablecoin", "critical", "https://example.com", "2024-01-15", "2024-12-30", "MiCA summary", '["stablecoin"]'))
    
    result = await search_regulations({"query": "MiCA", "jurisdiction": "eu"})
    assert len(result) > 0
    data = json.loads(result[0].text)
    assert len(data["results"]) == 1
    assert data["results"][0]["title"] == "MiCA Regulation"

@pytest.mark.asyncio
async def test_get_recent_changes(clean_db):
    from mcp_regwatch.server import get_recent_changes
    import sqlite3
    from mcp_regwatch.server import DB_PATH
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO regulations (id, jurisdiction, title, category, severity, source_url, published_at, effective_at, summary, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("eu-1", "eu", "MiCA", "stablecoin", "critical", "https://ex.com", datetime.now().isoformat(), "2024-12-30", "summary", '["stablecoin"]'))
    
    result = await get_recent_changes({"jurisdiction": "eu", "days": 30})
    data = json.loads(result[0].text)
    assert len(data["changes"]) == 1

@pytest.mark.asyncio
async def test_get_compliance_deadlines():
    from mcp_regwatch.server import get_compliance_deadlines
    result = await get_compliance_deadlines({"jurisdiction": "eu"})
    data = json.loads(result[0].text)
    assert "deadlines" in data
    assert len(data["deadlines"]) > 0

@pytest.mark.asyncio
async def test_create_watchlist():
    from mcp_regwatch.server import create_watchlist
    result = await create_watchlist({
        "name": "Test Watchlist",
        "jurisdictions": ["eu", "us"],
        "keywords": ["MiCA", "stablecoin"]
    })
    data = json.loads(result[0].text)
    assert data["name"] == "Test Watchlist"
    assert "eu" in data["jurisdictions"]

@pytest.mark.asyncio
async def test_list_watchlists():
    from mcp_regwatch.server import list_watchlists
    result = await list_watchlists({})
    data = json.loads(result[0].text)
    assert "watchlists" in data

if __name__ == "__main__":
    pytest.main([__file__, "-v"])