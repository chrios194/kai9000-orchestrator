# MCP Integration Policy

## Required
- Official MCP specification as protocol reference.
- Official Python SDK for Python integrations.
- Official TypeScript SDK for TypeScript integrations.
- MCP Inspector for compatibility, smoke testing and debugging.
- MCP Registry for discovery metadata where useful.

## Selection rule

Do not add a repository merely because it is popular. Add it only when it supplies a capability required by an active AIOS task.

## Security
- Never commit API keys, OAuth secrets or bearer tokens.
- Use environment/secret stores.
- Treat server URLs containing credentials as sensitive.
- Validate third-party MCP servers before production use.

## Architecture

`AIOS Agent → Orchestrator → MCP Adapter → External Service`

The external service must not become a hidden dependency of the core orchestrator.

## Reference repositories

The official MCP organization currently provides SDKs, Inspector, Registry and other ecosystem repositories. Prefer these official components over abandoned or duplicate implementations.
