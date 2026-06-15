# MCP Integration: isaacsim_mcp

The NVIDIA `kit-usd-agents` repo includes an **Isaac Sim MCP Server** that provides semantic search over Isaac Sim documentation, extensions, code examples, and settings via the Model Context Protocol.

## What It Is

- **MCP Server** (HTTP on port 9904) exposing NAT/AIQ functions
- **Knowledge layer only** — documentation search, not execution
- Built on **NVIDIA AIQ Toolkit** (formerly NeMo Agent Toolkit)
- Requires: Docker, Python 3.11+, NVIDIA API Key, Git LFS

## MCP Functions Exposed

| Function | Purpose |
|----------|---------|
| `get_isaac_sim_instructions` | Retrieve Isaac Sim framework docs & best practices |
| `search_isaac_sim_extensions` | Semantic search over Isaac Sim extensions |
| `get_isaac_sim_extension_details` | Comprehensive info on specific extension |
| `search_isaac_sim_code_examples` | Find relevant code snippets |
| `search_isaac_sim_settings` | Search configuration settings |

## Quickstart

```bash
# 1. Clone
git clone https://github.com/NVIDIA-Omniverse/kit-usd-agents.git
cd kit-usd-agents/source/mcp

# 2. Configure
cp .env.example .env
# Edit .env: NVIDIA_API_KEY=nvapi-...

# 3. Build & Run
cd isaacsim_mcp
./build-docker.sh  # ~10-15 min, ~1.35 GB
docker run --rm -p 9904:9904 --env-file ../.env isaacsim-mcp:latest
```

## Connect to Hermes

Add to Hermes MCP config or use directly:

```json
{
  "mcpServers": {
    "isaac-sim-mcp": { "url": "http://localhost:9904/mcp" }
  }
}
```

## How It Complements isaac-lab-bridge

| Need | Use |
|------|-----|
| "How to configure domain randomization for sim-to-real?" | `isaacsim_mcp` → search settings/examples |
| "What's the API for TiledCamera?" | `isaacsim_mcp` → get_extension_details |
| "Find pick-place code examples for Franka" | `isaacsim_mcp` → search_code_examples |
| **Actually execute pick-place policy on robot** | `isaac-lab-bridge` → Hermes skill executor |

## Development Workflow

1. **Design** → Use `isaacsim_mcp` to research Isaac Lab APIs, find examples
2. **Implement** → Write bridge code (translators, executor, safety)
3. **Test** → Run `scripts/test_bridge.py` (unit) + Isaac Lab integration test
4. **Deploy** → Register skill in `skills/registry.yaml`, run via Hermes

## Using with Hermes Agent

```bash
# In Hermes session
hermes mcp add isaac-sim-mcp http://localhost:9904/mcp

# Then ask Hermes:
> How do I set up domain randomization for Franka pick-place?
> Search for Isaac Lab camera sensor examples
> What are the recommended physics settings for sim-to-real?
```

## Files in This Skill

```
references/
└── mcp_integration.md    # This file
```

## Resources

- Repo: https://github.com/NVIDIA-Omniverse/kit-usd-agents
- MCP Server: `source/mcp/isaacsim_mcp/`
- Functions: `source/aiq/isaacsim_fns/`
- Python: 3.11–3.13 only (3.10 not supported)