# Control Plane MCP Server

A Model Context Protocol (MCP) server that provides tools for interacting with the Control Plane REST API.

## Features

This MCP server connects to your Control Plane API and provides:

### Project Management
- **Tools**:
  - `get_all_projects` - Retrieve a list of all projects (stacks)
  - `get_project_details` - Fetch details of a specific project
  - `use_project` - Set the current active project
  - `refresh_current_project` - Refresh project data from the server to avoid stale cache

### Variables Management
- **Tools**:
  - `get_secrets_and_vars` - View all variables and secrets for the current project
  - `get_variable_by_name` - Get a specific variable by name
  - `create_variable` - Create a new variable in the current project
  - `update_variable` - Update an existing variable in the current project
  - `delete_variable` - Delete a variable from the current project

### Resource Management
- **Tools**:
  - `get_all_resources_by_project` - Get all resources for a specific project
  - `get_resource_by_project` - Get a specific resource by type and name
  - `get_spec_for_resource` - Get specification details for a specific resource
  - `update_resource` - Update a specific resource in a project
  - `add_resource` - Add a new resource to a project
  - `delete_resource` - Delete a specific resource from a project
  - `get_spec_for_module` - Get specification details for a module
  - `get_sample_for_module` - Get a sample JSON template for creating a resource
  - `list_available_resources` - List all available resources that can be added

## Installation

### Prerequisites
- Python 3.12 or higher
- A running Control Plane API instance

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
uv pip install -r requirements.txt

# Run the server
uv run main.py
```

## Environment Variables

The server requires these environment variables:

- `CONTROL_PLANE_URL` - URL of your Control Plane API (required)
- `FACETS_USERNAME` - Username for authentication (required)
- `FACETS_TOKEN` - Token for authentication (required)
- `FACETS_PROFILE` - Optional profile name (if credentials are stored in ~/.facets/credentials)

## Usage with Claude Desktop

To use this MCP server with Claude Desktop, add the following configuration to your `claude_desktop_config.json` file (typically located at `~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
"ControlPlaneServer": {
  "command": "uv",
  "args": [
    "run",
    "--directory",
    "/path/to/control-plane-mcp-server",
    "main.py"
  ],
  "env": {
    "CONTROL_PLANE_URL": "https://your-control-plane-url",
    "FACETS_TOKEN": "your-facets-token",
    "FACETS_USERNAME": "your-facets-username"
  }
}
```

**Important Notes:**
1. Replace `/path/to/control-plane-mcp-server` with the absolute path to the repository on your machine
2. The `--directory` flag is critical - it sets the working directory for the script execution
3. Update the environment variables with your Control Plane credentials
4. After saving the configuration, restart Claude Desktop for the changes to take effect

Using a simpler command like `uv run /path/to/control-plane-mcp-server/main.py` without the `--directory` flag will not work correctly, as the script needs to execute from its project directory to properly locate dependencies and modules.

## Example Usage with Claude

Once configured in Claude Desktop, you can:

1. Browse projects: "Show me all available projects" or "Get details about project XYZ"
2. Select a project: "Use project 'my-project'"
3. Work with variables: "Show me all variables in the current project" or "Create a new secret variable for API authentication"
4. Manage resources: "List all resources in project X" or "Update the configuration for service Y"

Claude will automatically use the appropriate tools and display the results.

## Extending the Server

To add support for more Control Plane APIs:

1. Add new tool methods using the `@mcp.tool()` decorator in the tools directory
2. Import your tools in `__init__.py` to register them with the MCP instance

Follow the existing implementation patterns in the tools directory.

## Troubleshooting

If you encounter issues:

- Verify your Control Plane API is running and accessible
- Check that authentication credentials are correct
- Ensure you're using the correct API URL format
- Make sure the `--directory` flag is used to correctly set the working directory
- Check Claude Desktop logs for error messages
- Try running the server directly to see any error output
- Verify all required environment variables are set correctly
