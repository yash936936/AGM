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

The server registers nine stable tools. Handoff and writer-revocation tools return a Phase 4 not-implemented response until that phase lands. Streamable HTTP is restricted to loopback and uses one environment-configured identity; stdio is the recommended local integration.
