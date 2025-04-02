# Control Plane MCP Server

A Model Context Protocol (MCP) server that provides tools and resources for interacting with the Control Plane REST API.

## Features

This MCP server connects to your control plane API and provides:

### Release Stream API
- **Resources**:
  - `release-streams://list` - View all release streams
  - `release-streams://stack/{stack_name}` - View release streams for a specific stack
- **Tools**:
  - `create_release_stream` - Create a new release stream
  - `delete_release_stream` - Delete an existing release stream by name
- **Prompts**:
  - Guided creation of release streams
  - Guided deletion with risk assessment

## Installation

### Prerequisites
- Python 3.12 or higher
- A running control plane API instance

### Using the MCP CLI

The easiest way to install this server with Claude Desktop is using the MCP CLI:

```bash
# Install the MCP CLI
uv pip install "mcp[cli]"

# Install the server with Claude Desktop
mcp install /path/to/control-plane-mcp-server -v CONTROL_PLANE_API_URL=http://your-api-url -v CONTROL_PLANE_AUTH_USERNAME=your_username -v CONTROL_PLANE_AUTH_TOKEN=your_password
```

### Development Setup

For development and testing:

```bash
# Clone the repository
git clone https://github.com/yourusername/control-plane-mcp-server.git
cd control-plane-mcp-server

# Set up a virtual environment and install dependencies with uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e .

# Run in development mode with the MCP Inspector
uv run mcp dev . -v CONTROL_PLANE_API_URL=http://your-api-url -v CONTROL_PLANE_AUTH_USERNAME=your_username -v CONTROL_PLANE_AUTH_TOKEN=your_password
```

## Environment Variables

The server requires these environment variables:

- `CONTROL_PLANE_API_URL` - Base URL of your control plane API (required)
- `CONTROL_PLANE_AUTH_USERNAME` - Username for Basic authentication (required for secured endpoints)
- `CONTROL_PLANE_AUTH_TOKEN` - Password for Basic authentication (required for secured endpoints)

## Usage with Claude Desktop

Once installed in Claude Desktop, you can:

1. Ask about release streams: "Show me all release streams" or "What release streams are associated with the 'prod' stack?"
2. Create new release streams: "Create a new release stream called 'test-stream'"
3. Delete release streams: "Delete the release stream named 'old-stream'"

Claude will automatically use the appropriate tools and display the results.

## Extending the Server

To add support for more control plane APIs:

1. Add new resource methods using the `@mcp.resource()` decorator
2. Add new tool methods using the `@mcp.tool()` decorator
3. Add helpful prompts using the `@mcp.prompt()` decorator

Follow the existing release stream implementation as a pattern.

## Troubleshooting

If you encounter issues:

- Verify your control plane API is running and accessible
- Check authentication credentials
- Ensure you're using the correct API URL format
- Look for error messages in the logs
