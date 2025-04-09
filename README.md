# Control Plane MCP Server

A Model Context Protocol (MCP) server that provides tools for interacting with the Control Plane REST API.

## Features

This MCP server connects to your control plane API and provides:

### Release Stream Management
- **Tools**:
  - `create_release_stream` - Create a new release stream with options for production status and description

### Project Management
- **Tools**:
  - `get_all_projects` - Retrieve a list of all projects
  - `use_project` - Set the current active project
  - `refresh_current_project` - Refresh project data from the server to avoid stale cache

### Variables Management
- **Tools**:
  - `get_secrets_and_vars` - View all variables and secrets for the current project
  - `create_variables` - Create multiple new variables in the current project
  - `update_variables` - Update existing variables in the current project
  - `delete_variables` - Delete variables from the current project
- **Models**:
  - `VariablesModel` - Pydantic model for variable definition with fields for description, global status, secret status, and value

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

1. Manage projects: "Show me all available projects" or "Set the current project to 'my-project'"
2. Work with variables: "Show me all variables in the current project" or "Create a new secret variable for API authentication"
3. Create release streams: "Create a new release stream called 'test-stream'"

Claude will automatically use the appropriate tools and display the results.

## Extending the Server

To add support for more control plane APIs:

1. Add new tool methods using the `@mcp.tool()` decorator in the tools directory
2. Import your tools in main.py to register them with the MCP instance

Follow the existing implementation patterns in the tools directory.

## Troubleshooting

If you encounter issues:

- Verify your control plane API is running and accessible
- Check authentication credentials
- Ensure you're using the correct API URL format
- Look for error messages in the logs
