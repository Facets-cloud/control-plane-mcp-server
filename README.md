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
  - `get_all_resources_by_project` - Get all resources for the current project
  - `get_resource_by_project` - Get a specific resource by type and name (provides complete resource configuration)
  - `get_spec_for_resource` - Get specification details (schema) for a specific resource
  - `update_resource` - Update a specific resource in a project
  - `get_module_inputs` - Get required inputs for a module before adding a resource
  - `add_resource` - Add a new resource to a project
  - `delete_resource` - Delete a specific resource from a project
  - `get_spec_for_module` - Get specification details for a module
  - `get_sample_for_module` - Get a sample JSON template for creating a resource
  - `list_available_resources` - List all available resources that can be added
  - `get_output_references` - Get a list of available output references from resources based on output type
  - `explain_ui_annotation` - Get explanation and handling instructions for UI annotations
  - `get_resource_output_tree` - Get the hierarchical output tree for a specific resource type
  - `get_resource_management_guide` - Get comprehensive instructions for managing resources

### Environment Management
- **Tools**:
  - `get_all_environments` - Retrieve a list of all environments in the current project
  - `use_environment` - Set the current active environment for operations
  - `get_current_environment_details` - Get detailed information about the current environment
  - `check_if_environment_is_running` - Verify if the current environment is in running state
  - `get_releases_of_current_environment` - List all releases for the current environment
  - `get_release_details` - Get detailed information about a specific release
  - `get_release_logs_of_current_environment` - Get logs for a specific release
  - `get_active_releases_of_current_environment` - List all currently running releases
  - `get_active_release_logs_of_current_environment` - Get logs from all running releases
  - `get_latest_release_of_current_environment` - Get the most recent release information
  - `launch_environment` - Initialize and start up an environment
  - `destroy_environment` - Remove all resources in an environment
  - `create_selective_release_plan_for_environment` - Create a plan for targeted resource fixes
  - `create_selective_release_for_environment` - Apply targeted fixes to specific resources
  - `create_full_release_plan_for_environment` - Create a plan for updating all resources
  - `create_full_release_for_environment` - Update all resources with latest changes
  - `create_custom_release_for_environment` - Execute custom deployment steps
  - `unlock_state_of_environment` - Unlock terraform state if locked
  - `scale_up_environment` - Scale up a scaled-down environment
  - `scale_down_environment` - Scale down a running environment

## Resource Management Workflow

The resource management tools support a complete workflow for creating, updating, and configuring resources:

1. **Exploration**: Use `list_available_resources()` to see what resource types and flavors are available
2. **Dependencies**: Call `get_module_inputs()` to check what inputs are required for a resource
3. **Understanding**: Call `get_spec_for_module()` and `get_sample_for_module()` to understand the schema and structure
4. **Creation**: Use `add_resource()` with the required parameters to create the resource
5. **Configuration**: Update settings with `update_resource()` and refer to `get_spec_for_resource()` for valid fields
6. **Referencing**: Use `get_output_references()` and `get_resource_output_tree()` for cross-resource references
7. **Special Fields**: Handle special field types with guidance from `explain_ui_annotation()`

For comprehensive guidance, use `get_resource_management_guide()` which provides detailed instructions on the entire process.

## Environment Management Workflow

The environment management tools support a complete workflow for managing clusters (environments) and deployments:

1. **Discovery**: Use `get_all_environments()` to see all available environments in your project
2. **Selection**: Call `use_environment()` to set a specific environment as active for all operations
3. **Status Check**: Use `get_current_environment_details()` and `check_if_environment_is_running()` to verify the environment state
4. **Monitoring**: Track releases with `get_releases_of_current_environment()` and `get_release_logs_of_current_environment()`
5. **Environment Lifecycle**:
   - **Launch**: Start a new environment with `launch_environment()`
   - **Update**: Create update plans with `create_full_release_plan_for_environment()` and apply with `create_full_release_for_environment()`
   - **Selective Updates**: Target specific resources with `create_selective_release_plan_for_environment()` and apply with `create_selective_release_for_environment()`
   - **Scale**: Manage resource allocation with `scale_down_environment()` and `scale_up_environment()`
   - **Recovery**: Fix locked states with `unlock_state_of_environment()`
   - **Custom Operations**: Perform advanced operations with `create_custom_release_for_environment()`
   - **Cleanup**: Remove environments with `destroy_environment()`

Each operation requires specific checks and confirmations to ensure safe execution, and the tools provide extensive validation to prevent errors.

## Installation

### Prerequisites
- Python 3.12 or higher
- uv package manager (install using `brew install uv`)
- A running Control Plane API instance

### Installation via PyPI

```bash
# Install the package
pip install facets-cp-mcp-server

# Run the server
facets-cp-mcp-server
```

### Usage with Claude Desktop

To use this MCP server with Claude Desktop, add the following configuration to your `claude_desktop_config.json` file (typically located at `~/Library/Application Support/Claude/claude_desktop_config.json`):

#### Option 1: Using installed package (Recommended)

```json
{
  "mcpServers": {
    "ControlPlaneServer": {
      "command": "facets-cp-mcp-server",
      "env": {
        "CONTROL_PLANE_URL": "https://your-control-plane-url",
        "FACETS_TOKEN": "your-facets-token",
        "FACETS_USERNAME": "your-facets-username"
      }
    }
  }
}
```

#### Option 2: Using uv for development

```json
{
  "mcpServers": {
    "ControlPlaneServer": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/control-plane-mcp-server",
        "--module",
        "control_plane_mcp.server"
      ],
      "env": {
        "CONTROL_PLANE_URL": "https://your-control-plane-url",
        "FACETS_TOKEN": "your-facets-token",
        "FACETS_USERNAME": "your-facets-username"
      }
    }
  }
}
```

**Important Notes:**
1. Replace `/path/to/control-plane-mcp-server` with the absolute path to the repository on your machine (for development setup)
2. The `--directory` flag is critical for development - it sets the working directory for the script execution
3. The `--module` flag runs the package module directly
4. Update the environment variables with your Control Plane credentials
5. After saving the configuration, restart Claude Desktop for the changes to take effect

### Environment Variables

The server requires these environment variables:

- `CONTROL_PLANE_URL` - URL of your Control Plane API (required if not using profile)
- `FACETS_USERNAME` - Username for authentication (required if not using profile)
- `FACETS_TOKEN` - Token for authentication (required if not using profile)
- `FACETS_PROFILE` - Optional profile name (if credentials are stored in ~/.facets/credentials)

### Development Setup

For development and testing:

```bash
# Clone the repository
git clone https://github.com/Facets-cloud/control-plane-mcp-server.git
cd control-plane-mcp-server

# Set up a virtual environment and install dependencies with uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv sync

# Run the server for development
uv run --module control_plane_mcp.server

# Or install in development mode and run
uv pip install -e .
facets-cp-mcp-server
```

## Example Usage with Claude

Once configured in Claude Desktop, you can:

1. Browse projects: "Show me all available projects" or "Get details about project XYZ"
2. Select a project: "Use project 'my-project'"
3. Work with variables: "Show me all variables in the current project" or "Create a new secret variable for API authentication"
4. Manage resources: "List all resources in project X" or "Update the configuration for service Y"
5. Create complex resources: "Help me add a new service resource that connects to my database"
6. Manage environments: "List all clusters in my project" or "Launch the dev-cluster environment"
7. Monitor releases: "Show me active releases in my environment" or "Get logs for the latest release"
8. Perform operations: "Create a selective release plan for the auth service" or "Scale down my staging environment"

Claude will automatically use the appropriate tools and display the results.

## Extending the Server

To add support for more Control Plane APIs:

1. Add new tool methods using the `@mcp.tool()` decorator in the `control_plane_mcp/tools/` directory
2. Import your tools in `__init__.py` to register them with the MCP instance

Follow the existing implementation patterns in the tools directory.

## Troubleshooting

If you encounter issues:

- Verify your Control Plane API is running and accessible
- Check that authentication credentials are correct
- Ensure you're using the correct API URL format
- For development: Make sure the `--directory` flag is used to correctly set the working directory
- Check Claude Desktop logs for error messages
- Try running the server directly to see any error output: `facets-cp-mcp-server` or `uv run --module control_plane_mcp.server`
- Verify all required environment variables are set correctly

## Publishing

This package is published to PyPI as `facets-cp-mcp-server`. Releases are automatically published when tags are pushed:

```bash
git tag v1.0.0
git push origin v1.0.0
```
