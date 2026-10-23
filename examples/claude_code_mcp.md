# Local MCP configuration

The MCP stdio adapter uses a process identity rather than the REST API-key file. Set these environment variables in the MCP client configuration:

- `AGM_TENANT`: tenant namespace
- `AGM_WRITER`: stable ID for the agent
- `AGM_TIER`: one of `human_verified`, `tool_verified`, `trusted_agent`, `untrusted`
- `AGM_DB_PATH`: SQLite path
- `AGM_SCOPES`: comma-separated scopes, defaults to read/write/delete

A Claude Code-style configuration can be adapted to this shape (replace the Python path for your machine):

```json
{
  "mcpServers": {
    "agm": {
      "command": "D:\\path\\to\\AGM\\.venv\\Scripts\\python.exe",
      "args": ["-m", "agm", "serve-mcp", "--transport", "stdio"],
      "env": {
        "AGM_TENANT": "local-dev",
        "AGM_WRITER": "claude-code",
        "AGM_TIER": "trusted_agent",
        "AGM_PROJECT": "default",
        "AGM_DB_PATH": "D:\\path\\to\\AGM\\agm.db",
        "AGM_SCOPES": "memory:read,memory:write,memory:delete"
      }
    }
  }
}
```

The server registers nine stable tools (memory read/write/supersede/history/delete, handoff save/resume/readback, and admin writer revocation). Streamable HTTP is restricted to loopback and uses one environment-configured identity; stdio is the recommended local integration.

## Alternative: add it from the Claude Code CLI

Claude Code can register a stdio server from the command line. The flag syntax below is from memory of the CLI and has not been verified against your installed version; run `claude mcp add --help` first and adjust:

```
claude mcp add agm -e AGM_TENANT=local-dev -e AGM_WRITER=claude-code -e AGM_TIER=trusted_agent -e AGM_DB_PATH=/abs/path/agm.db -- /abs/path/.venv/bin/python -m agm serve-mcp --transport stdio
```

## Check the server before blaming the client

`python examples/mcp_smoke_client.py` launches the server the same way a host would and runs 12 checks (tools listed, write, correction, secret redaction, quarantine, fresh-session retrieval, handoff, readback). If it passes but your host cannot connect, the problem is the host configuration (absolute paths, environment variables), not AGM. For a plain Python agent over HTTP, `python examples/rest_smoke_client.py` does the same with 11 checks.
