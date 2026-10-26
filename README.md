# mcp-regwatch

MCP server for regulatory research subscription - search regulations, track changes, and monitor compliance deadlines.

## Tools

### search_regulations
Search regulations by keyword, jurisdiction, or status.

**Parameters:**
- `query` (string, required): Search query
- `jurisdiction` (string, optional): "eu", "us", "uk", "sg", or "all" (default: "all")
- `status` (string, optional): "active", "proposed", "consultation", or "all" (default: "all")

### get_recent_changes
Get recent regulatory changes within a time window.

**Parameters:**
- `jurisdiction` (string, required): "eu", "us", "uk", "sg", or "all"
- `days` (integer, optional): Days to look back (default: 30)

### get_compliance_deadlines
Get upcoming compliance deadlines.

**Parameters:**
- `jurisdiction` (string, required): "eu", "us", "uk", "sg", or "all"
- `days_ahead` (integer, optional): Days ahead to check (default: 90)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Connecting to Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "regwatch": {
      "command": "python",
      "args": ["/path/to/mcp-regwatch/main.py"],
      "cwd": "/path/to/mcp-regwatch"
    }
  }
}
```

## License

MIT