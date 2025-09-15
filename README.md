# Facets Control Plane MCP Server

This MCP (Model Context Protocol) Server provides comprehensive tools for interacting with the Facets Control Plane REST API. It enables seamless management of projects, resources, environments, and deployments through Claude, offering secure and robust infrastructure automation workflows.

## Key Features

* **Complete Project Management**  
  Full lifecycle project management including project discovery, variable management, and resource configuration with built-in validation and safety checks.

* **Resource Lifecycle Management**  
  End-to-end resource management from discovery and creation to updates and deletion. Supports complex resource dependencies, input validation, and schema-driven configuration.

* **Environment Management**
  Environment discovery, selection, and configuration/override management with validation and safety checks.

* **Safety-First Design**  
  All destructive operations require explicit user confirmation with dry-run previews. Comprehensive validation ensures safe execution of infrastructure changes.

* **Schema-Driven Configuration**  
  Automatic schema validation and sample generation for all resource types, ensuring configurations meet requirements before deployment.

## Available MCP Tools

| Tool Name                                    | Description                                                                                                               |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **Project Management**                      |                                                                                                                           |
| `get_all_projects`                           | Retrieve a list of all projects (stacks) available in the control plane.                                                 |
| `get_project_details`                       | Fetch detailed information about a specific project including configuration and metadata.                                |
| `use_project`                               | Set the current active project for all subsequent operations.                                                            |
| `refresh_current_project`                   | Refresh project data from the server to avoid stale cache issues.                                                        |
| **Variable Management**                     |                                                                                                                           |
| `get_secrets_and_vars`                      | View all variables and secrets for the current project with type and status information.                                 |
| `get_variable_by_name`                      | Retrieve a specific variable by name with full configuration details.                                                    |
| `create_variable`                           | Create a new variable in the current project with validation and type checking.                                          |
| `update_variable`                           | Update an existing variable's value, description, or configuration safely.                                               |
| `delete_variable`                           | Delete a variable from the current project with confirmation requirements.                                               |
| `get_variable_environment_values`           | Get environment-specific values for a variable across all environments.                                                  |
| `update_variable_environment_value`         | Update the value of a variable for the current environment.                                                              |
| **Resource Discovery & Management**         |                                                                                                                           |
| `list_available_resources`                  | List all available resource types and flavors that can be added to the current project.                                  |
| `get_all_resources_by_project`              | Get all resources currently configured in the project with full details.                                                 |
| `get_resource_by_project`                   | Get complete configuration for a specific resource including base config and effective settings.                        |
| `get_spec_for_resource`                     | Get the JSON schema specification for a specific resource's configuration options.                                       |
| `get_module_inputs`                         | Get required inputs and compatible resources needed before adding a new resource.                                        |
| `get_spec_for_module`                       | Get specification details for a module based on intent, flavor, and version.                                            |
| `get_sample_for_module`                     | Get a complete sample JSON template for creating a new resource of a specific type.                                      |
| `get_resource_schema_public`                | Get the complete schema definition for any Facets resource type.                                                         |
| `add_resource`                              | Add a new resource to the project with dependency resolution and validation. Supports dry-run preview.                  |
| `update_resource`                           | Update an existing resource's configuration with schema validation and change preview.                                   |
| `delete_resource`                           | Delete a specific resource from the project with confirmation and dependency checking.                                   |
| **Resource Configuration Helpers**          |                                                                                                                           |
| `get_output_references`                     | Get available output references from resources based on output type for cross-resource linking.                         |
| `explain_ui_annotation`                     | Get explanation and handling instructions for special UI annotations in resource specifications.                         |
| `get_resource_output_tree`                  | Get the hierarchical output tree for a specific resource type for reference building.                                    |
| `get_resource_management_guide`             | Get comprehensive instructions for the complete resource management workflow.                                            |
| **Environment Management**                  |                                                                                                                           |
| `get_all_environments`                      | Retrieve all environments (clusters) available in the current project.                                                   |
| `use_environment`                           | Set the current active environment for deployment and monitoring operations.                                             |
| `get_current_environment_details`           | Get detailed information about the current environment including status and configuration.                               |
| `get_all_resources_by_environment`          | Get all resources deployed in the current environment with override information.                                         |
| `get_resource_by_environment`               | Get environment-specific resource configuration including base config, overrides, and effective settings.               |
| **Environment Overrides**                   |                                                                                                                           |
| `add_or_update_override_property`           | Safely add or update a specific property in environment-specific resource overrides.                                     |
| `remove_override_property`                  | Remove a specific property from resource overrides while preserving other override settings.                             |
| `replace_all_overrides`                     | Replace all existing overrides with a completely new override configuration.                                             |
| `clear_all_overrides`                       | Remove all overrides for a resource, reverting to base project configuration.                                            |
| `preview_override_effect`                   | Preview the effective configuration that would result from applying a proposed override.                                 |

## Prerequisites

The MCP Server requires [uv](https://github.com/astral-sh/uv) for dependency management and execution.

The package is available on PyPI: [facets-cp-mcp-server](https://pypi.org/project/facets-cp-mcp-server/)

#### Install `uv` with Homebrew:
```bash
brew install uv
```

For other methods, see the [official uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

## Transport Modes

The Facets Control Plane MCP server supports two transport modes:

### 1. **stdio** (default)
Traditional stdio-based communication, ideal for local development with Claude Desktop or other MCP clients.

### 2. **streamable-http**
HTTP-based transport that enables:
- Remote server deployment
- Multiple concurrent clients
- Server-Sent Events (SSE) for real-time streaming
- Stateless or stateful session management
- JSON or SSE response formats

Use `--help` to see all available options:
```bash
uv run facets-cp-mcp-server --help
```

### Integration with Claude

#### Option 1: stdio Transport (Default)

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "facets-control-plane": {
      "command": "uvx",
      "args": [
        "facets-cp-mcp-server@latest"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "CONTROL_PLANE_URL": "<YOUR_CONTROL_PLANE_URL>",
        "FACETS_USERNAME": "<YOUR_USERNAME>",
        "FACETS_TOKEN": "<YOUR_TOKEN>",
        "FACETS_PROFILE": "default"
      }
    }
  }
}
```

#### Option 2: Streamable HTTP Transport - does not work with claude desktop (use claude code)

For HTTP-based communication, first start the server:

```bash
# Basic HTTP server on default port 3000
uv run facets-cp-mcp-server --transport streamable-http

# Custom port and host
uv run facets-cp-mcp-server --transport streamable-http --port 8080 --host 0.0.0.0

# Stateless mode with JSON responses
uv run facets-cp-mcp-server --transport streamable-http --stateless --json-response

# With debug logging
uv run facets-cp-mcp-server --transport streamable-http --log-level DEBUG
```

Then configure Claude Desktop to connect to the HTTP server:

```bash
claude mcp add --transport http facets-cp-mcp-server http://localhost:3000/mcp
```

#### Option 3: Local Development with stdio

For a locally cloned repository, use one of these approaches:

**Approach A: Run as Python module (Recommended)**
```json
{
  "mcpServers": {
    "facets-control-plane": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/control-plane-mcp-server",
        "python",
        "-m",
        "control_plane_mcp"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "CONTROL_PLANE_URL": "<YOUR_CONTROL_PLANE_URL>",
        "FACETS_USERNAME": "<YOUR_USERNAME>",
        "FACETS_TOKEN": "<YOUR_TOKEN>",
        "FACETS_PROFILE": "default"
      }
    }
  }
}
```

**Approach B: Run via package command**
```json
{
  "mcpServers": {
    "facets-control-plane": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/control-plane-mcp-server",
        "facets-cp-mcp-server"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "CONTROL_PLANE_URL": "<YOUR_CONTROL_PLANE_URL>",
        "FACETS_USERNAME": "<YOUR_USERNAME>",
        "FACETS_TOKEN": "<YOUR_TOKEN>",
        "FACETS_PROFILE": "default"
      }
    }
  }
}
```

⚠ Replace `<YOUR_USERNAME>`, `<YOUR_TOKEN>`, and `<YOUR_CONTROL_PLANE_URL>` with your actual authentication data.

The `uv` runner automatically manages environment and dependency setup using the `pyproject.toml` file.

If you have already logged into FTF CLI, specifying `FACETS_PROFILE` is sufficient.

### Running the Server

#### Command Line Options

```bash
uv run facets-cp-mcp-server [OPTIONS]

Options:
  --transport [stdio|streamable-http]  Transport protocol to use [default: stdio]
  --port INTEGER                       Port for streamable-http [default: 3000]
  --host TEXT                         Host for streamable-http [default: localhost]
  --stateless                         Run in stateless mode (streamable-http only)
  --json-response                     Use JSON responses instead of SSE (streamable-http only)
  --log-level [DEBUG|INFO|WARNING|ERROR]  Logging level [default: INFO]
  --help                              Show this message and exit
```

#### Examples

```bash
# Traditional stdio mode (for Claude Desktop)
uv run facets-cp-mcp-server

# HTTP server on default port
uv run facets-cp-mcp-server --transport streamable-http

# HTTP server with custom settings
uv run facets-cp-mcp-server --transport streamable-http --port 8080 --host 0.0.0.0 --log-level DEBUG

# Stateless HTTP with JSON responses
uv run facets-cp-mcp-server --transport streamable-http --stateless --json-response
```

---

For token generation and authentication setup, please refer to the official Facets documentation:  
[https://readme.facets.cloud/reference/authentication-setup](https://readme.facets.cloud/reference/authentication-setup)

Note: Similar setup is available in Cursor read [here](https://docs.cursor.com/context/model-context-protocol)

---

## Usage Highlights

### Resource Management Workflow

Complete workflow for creating, updating, and configuring resources:

1. **Discovery**: Use `list_available_resources()` to explore available resource types and flavors
2. **Dependencies**: Call `get_module_inputs()` to understand required inputs and compatible resources  
3. **Understanding**: Use `get_spec_for_module()` and `get_sample_for_module()` for schema and structure
4. **Creation**: Create resources with `add_resource()` including dependency resolution and validation
5. **Configuration**: Update settings with `update_resource()` and validate with `get_spec_for_resource()`
6. **Cross-referencing**: Link resources using `get_output_references()` and `get_resource_output_tree()`

### Environment Management Workflow

Complete environment configuration management:

1. **Discovery**: Use `get_all_environments()` to see available environments in your project
2. **Selection**: Set active environment with `use_environment()` for all operations
3. **Monitoring**: Track environment status with `get_current_environment_details()`
4. **Configuration**: View environment-specific resources with `get_all_resources_by_environment()`
5. **Override Management**: Apply environment-specific configurations while preserving base project settings

### Safety Features

- **Dry-run Previews**: All destructive operations show change previews before execution
- **User Confirmation**: Explicit confirmation required for irreversible actions
- **Schema Validation**: All configurations validated against resource schemas before deployment
- **Dependency Checking**: Automatic validation of resource dependencies and compatibility

---

## Example Usage

Once configured with Claude Desktop, you can:

1. **Project Operations**: "Show me all available projects" → "Use project 'my-web-app'" → "List all resources in this project"
2. **Resource Creation**: "Help me add a new PostgreSQL database" → "Connect my service to the database" → "Update the service configuration"
3. **Environment Management**: "List all environments" → "Use the staging environment" → "View resources in staging"
4. **Variable Management**: "Show me all project variables" → "Update the database URL for staging environment"
5. **Override Management**: "Set the replica count to 3 in staging" → "Preview the effect of this change" → "Apply the override"

All operations include comprehensive validation, safety checks, and clear feedback on success or failure conditions.

---

## Development Setup

For development and testing:

```bash
# Clone the repository
git clone https://github.com/Facets-cloud/control-plane-mcp-server.git
cd control-plane-mcp-server

# Set up environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync

# Run the server for development
uv run --module control_plane_mcp.server
```

### Extending the Server

To add support for more Control Plane APIs:

1. Add new tool methods using the `@mcp.tool()` decorator in the `control_plane_mcp/tools/` directory
2. Import your tools in the appropriate `__init__.py` to register them with the MCP instance
3. Follow existing implementation patterns for error handling, validation, and user confirmation

---

## License

This project is licensed under the MIT License. You are free to use, modify, and distribute it under its terms.
