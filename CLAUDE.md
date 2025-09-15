# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the Facets Control Plane MCP (Model Context Protocol) Server - a Python-based server that provides comprehensive tools for interacting with the Facets Control Plane REST API. It enables infrastructure automation through Claude by managing projects, resources, environments, and deployments.

## Development Commands

### Running the Server

```bash
# Run as Python module (for development)
uv run python -m control_plane_mcp

# Run with package command
uv run facets-cp-mcp-server

# Run with streamable HTTP transport
uv run facets-cp-mcp-server --transport streamable-http --port 8080

# Run with debug logging
uv run facets-cp-mcp-server --log-level DEBUG
```

### Package Management

```bash
# Install dependencies
uv sync

# Build the package
python -m build

# Generate Pydantic models from OpenAPI specs
make generate-models
# or
python control_plane_mcp/scripts/generate_pydantic_models.py
```

## Architecture

### Core Components

1. **MCP Server (`server.py`)**: Main entry point that initializes the MCP instance and handles both stdio and streamable-http transports. The server tests authentication on startup and configures logging based on transport type.

2. **Tool Organization (`tools/`)**: Tools are organized by functional domain:
   - `project_tools.py`: Project/stack management and variable operations (11 active tools)
   - `configure_resource_tool.py`: Resource CRUD operations, schema validation, and dependency management (13 active tools)
   - `env_tools.py`: Environment discovery and context management (3 active tools)
   - `env_resource_tool.py`: Environment-specific resource views (2 active tools)
   - `env_override_tool.py`: Environment-specific configuration overrides (5 active tools)
   - `release_tools.py`: Deployment and release management (currently all tools commented out - not active)
   - `resource_guide.py`: Documentation and guidance tools (1 active tool)

3. **Client Configuration (`config.py`)**: Centralizes MCP instance creation and authentication setup using environment variables or Facets CLI profiles.

4. **Utilities (`utils/`)**:
   - `client_utils.py`: Manages API client initialization with authentication
   - `override_utils.py`: Handles property path navigation for configuration overrides
   - `validation_utils.py`: Provides schema validation and error handling
   - `dict_utils.py`: Dictionary manipulation helpers for nested configurations

### Key Design Patterns

1. **Stateful Context Management**: The server maintains current project and environment context across tool calls to avoid repetitive selections.

2. **Safety-First Operations**: All destructive operations require explicit user confirmation and provide dry-run previews.

3. **Schema-Driven Configuration**: Resources are validated against JSON schemas before any API calls, with automatic sample generation.

4. **Hierarchical Override System**: Environment-specific configurations use dot-notation property paths (e.g., `spec.replicas`) to modify base configurations without replacing them entirely.

## Important Implementation Details

### Authentication Flow
The server supports three authentication methods (in priority order):
1. Environment variables: `CONTROL_PLANE_URL`, `FACETS_USERNAME`, `FACETS_TOKEN`
2. Facets CLI profile: `FACETS_PROFILE` environment variable
3. Interactive prompt (stdio transport only)

### Resource Management Workflow
When implementing resource operations, follow this sequence:
1. Discovery: `list_available_resources()` → available types and flavors
2. Dependencies: `get_module_inputs()` → required inputs from other resources
3. Schema: `get_spec_for_module()` → configuration structure
4. Template: `get_sample_for_module()` → starter configuration
5. Validation: Check against schema before API calls
6. Creation/Update: Apply configuration with confirmation

### Environment Override Management
Overrides modify environment-specific configurations without changing the base project:
- Use property paths for surgical updates: `add_or_update_override_property()`
- Always preview changes: `preview_override_effect()`
- Preserve existing overrides when updating: merge, don't replace

### Error Handling Strategy
- All API errors are caught and returned as structured error messages
- Authentication failures trigger re-authentication attempts
- Schema validation errors provide specific field-level feedback
- Network errors include retry guidance

## Transport Modes

### stdio (Default)
- Used by Claude Desktop
- Single-session, interactive mode
- Supports authentication prompts

### streamable-http
- HTTP server with SSE or JSON responses
- Supports multiple concurrent clients
- Configurable for stateless operation
- Cannot prompt for authentication interactively

## Dependencies

Critical dependencies managed via `pyproject.toml`:
- `mcp[cli]>=1.13.0`: Core MCP protocol implementation
- `facets-control-plane-sdk==1.0.3`: Facets API client
- `pydantic~=2.11.2`: Data validation
- `uvicorn` & `starlette`: HTTP transport support
- `httpx`: HTTP client for API calls

## Testing Considerations

While no formal test suite exists, when modifying the codebase:
1. Test authentication with both environment variables and CLI profiles
2. Verify resource CRUD operations maintain schema compliance
3. Ensure environment overrides preserve base configurations
4. Check that all destructive operations require confirmation
5. Validate both stdio and streamable-http transports work correctly