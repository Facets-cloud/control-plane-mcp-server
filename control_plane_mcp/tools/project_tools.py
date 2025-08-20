"""
PROJECT & ENVIRONMENT CONTEXT TOOLS

Foundational tools for establishing working context in Facets infrastructure management.
Most operations require project context; environment-specific operations need both project and environment context.

**Context Hierarchy & Dependencies:**
- **Projects** (stacks): Top-level containers that group related infrastructure
- **Environments**: Deployment targets within projects (dev, staging, production)  
- **Resources**: Infrastructure components deployed within projects
- **Variables**: Configuration values that can be referenced by resources

**Context Requirements:**
- **Project context required for**: Resource operations, environment discovery, variable management
- **Environment context required for**: Environment-specific overrides, environment resource queries
- **No context required for**: Project discovery, schema exploration with `get_resource_schema_public()`

**Variable & Secret Management:**
Variables and secrets store configuration values that resources can reference using template syntax:
- Variables: `${blueprint.self.variables.variable_name}`
- Secrets: `${blueprint.self.secrets.secret_name}`
- Resource outputs: `${blueprint.resource_name.outputs.output_field}`

Variables can have:
- **Project-level defaults**: Base values used across all environments
- **Environment-specific overrides**: Different values per environment (dev vs prod)

**Essential Context Flow:**
1. **Project Discovery**: `get_all_projects()` (when user doesn't know available projects)
2. **Project Selection**: `use_project(name)` (enables most other operations)
3. **Environment Operations**: `get_all_environments()` → `use_environment(name)` (for env-specific work)
4. **Variable Management**: Create, read, update variables and environment-specific values

Most tools will fail without proper context - project context is foundational for resource and environment operations.
"""

from ..pydantic_generated.variablesmodel import VariablesModel
from ..utils.client_utils import ClientUtils
from ..config import mcp
import swagger_client
from swagger_client.models import Variables, VariableRequest
from swagger_client.api.variable_management_api import VariableManagementApi
from typing import List, Dict
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INVALID_REQUEST


@mcp.tool()
def create_variable(name: str, variable: VariablesModel) -> None:
    """
    Create a new variable or secret in the current project.
    
    **Purpose & Context:**
    Variables and secrets store configuration values and sensitive data that can be
    referenced by resources across the project. Variables are plain text values,
    while secrets are encrypted values for sensitive data like passwords and API keys.
    
    **Prerequisites:**
    - Current project must be set (use `use_project()` first)
    - Variable name must not already exist in the project
    - Recommended: Call `get_secrets_and_vars()` first to check existing variables
    
    **Usage Patterns:**
    - Creating database credentials: `create_variable("db_password", secret_model)`
    - Setting API endpoints: `create_variable("api_url", variable_model)` 
    - Storing environment-specific configs that resources will reference
    
    **LLM-Friendly Tags:** [FOUNDATIONAL] [PROJECT-LEVEL] [CONFIGURATION]

    Args:
        name: Name of the variable to create (must be unique within project)
        variable: VariablesModel object containing value, description, and secret flag

    Raises:
        McpError: If the variable already exists or no current project is set
        
    **See Also:**
    - `get_secrets_and_vars()` - Check existing variables before creating
    - `update_variable()` - Modify existing variable values
    - `get_variable_by_name()` - Retrieve specific variable details
    """
    current_vars = get_secrets_and_vars()
    current_project = ClientUtils.get_current_project()

    if name in current_vars:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"The variable '{name}' already exists."
            )
        )

    variable_swagger_instance = ClientUtils.pydantic_instance_to_swagger_instance(variable, Variables)

    api_instance = swagger_client.UiBlueprintDesignerControllerApi(ClientUtils.get_client())
    result = api_instance.add_variables({name: variable_swagger_instance}, current_project.name)
    ClientUtils.refresh_current_project_and_cache()
    return result


@mcp.tool()
def update_variable(name: str, variable: VariablesModel) -> None:
    """
    Update an existing variable in the current project.

    Args:
        name: Name of the variable to update.
        variable: VariablesModel object of the variable to update.

    Raises:
        McpError: If the variable does not exist.
    """
    current_vars = get_secrets_and_vars()
    current_project = ClientUtils.get_current_project()

    if name not in current_vars:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"The variable '{name}' does not exist."
            )
        )

    variable_swagger_instance = ClientUtils.pydantic_instance_to_swagger_instance(variable, Variables)

    api_instance = swagger_client.UiBlueprintDesignerControllerApi(ClientUtils.get_client())
    result = api_instance.update_variables({name: variable_swagger_instance}, current_project.name)
    ClientUtils.refresh_current_project_and_cache()

    return result


@mcp.tool()
def delete_variable(name: str, confirmed_by_user: bool = False) -> None:
    """
    Delete a variable from the current project.

    Args:
        name: Name of the variable to delete.
        confirmed_by_user: Flag to check if changes have been confirmed by the user.
        IMPORTANT: Only send this true if you have asked user and warned him that this will remove variable and is a destructive action

    Raises:
        McpError: If the variable does not exist or if changes have not been confirmed.
    """
    if not confirmed_by_user:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="You need to confirm the changes with the user first as this is a destructive change."
            )
        )

    current_vars = get_secrets_and_vars()
    current_project = ClientUtils.get_current_project()

    if name not in current_vars:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"The variable '{name}' does not exist."
            )
        )

    api_instance = swagger_client.UiBlueprintDesignerControllerApi(ClientUtils.get_client())
    result = api_instance.delete_variables([name], current_project.name)
    ClientUtils.refresh_current_project_and_cache()

    return result


@mcp.tool()
def get_all_projects() -> str:
    """
    Retrieve and return the names of all projects (also called stacks) in the system.
    
    **Purpose & Context:**
    Projects are the top-level containers that group related infrastructure resources
    together. Each project can contain multiple environments (dev, staging, prod) and
    resources (services, databases, etc.). This function provides discovery of available
    projects before selecting one to work with.
    
    **Prerequisites:**
    - Valid Facets authentication and API access
    - No current project needs to be set
    
    **Usage Patterns:**
    - **Project Discovery**: First step when user doesn't know available projects
    - **Project Switching**: When user wants to see all options before switching
    - **System Overview**: Understanding the scope of managed infrastructure
    
    **When NOT to Use:**
    - When you already know the specific project name (use `use_project()` directly)
    - For getting details of one project (use `get_project_details()` instead)
    - In automated scripts where project name is predetermined
    
    **LLM-Friendly Tags:** [FOUNDATIONAL] [DISCOVERY] [READ-ONLY]

    Returns:
        str: Newline-separated list of all project names
        
    **Workflow Integration:**
    1. `get_all_projects()` ← **You are here**
    2. `use_project(project_name)` - Select a project to work with
    3. `get_project_details(project_name)` - Get detailed project information
    
    **See Also:**
    - `use_project()` - Set current working project
    - `get_project_details()` - Get detailed info about a specific project
    - `refresh_current_project()` - Refresh current project data
    """
    api_instance = swagger_client.UiStackControllerApi(ClientUtils.get_client())
    stacks = api_instance.get_stacks()
    # Extract just the stack names and return them as a formatted string
    stack_names = [stack.name for stack in stacks]
    return "\n".join(stack_names) if stack_names else "No projects found"


@mcp.tool()
def use_project(project_name: str):
    """
    Set the current working project (stack) for all subsequent operations.
    
    **Context Requirement:**
    This is a **foundational function** that establishes project context for nearly all other operations.
    Most resource, environment, and variable tools require a current project to be set before they can function.
    This is equivalent to "changing directory" to a project workspace.
    
    **Prerequisites:**
    - Project must exist in the system (use `get_all_projects()` to discover available options)
    - Valid Facets authentication and API access
    
    **Impact on Other Tools:**
    Setting project context enables:
    - Resource operations (`list_available_resources`, `add_resource`, etc.)
    - Environment operations (`get_all_environments`, `use_environment`, etc.)  
    - Variable operations (`get_secrets_and_vars`, `create_variable`, etc.)
    - Resource configuration and management within this project's scope
    
    **Usage Context:**
    - **Workflow Start**: Typically the first operation after discovering available projects
    - **Project Switching**: When user wants to work with a different project
    - **Context Reset**: When previous operations were in a different project context
    
    Args:
        project_name: Exact name of the project to set as current working context
        
    Returns:
        str: Confirmation message indicating the project has been set
        
    **Common Follow-up Operations:**
    - `get_all_environments()` - Discover environments within this project
    - `list_available_resources()` - See what infrastructure can be deployed  
    - `get_secrets_and_vars()` - View existing project configuration values
    
    **Context Flow:** Project selection → Environment/resource operations → Configuration management
    """
    api_instance = swagger_client.UiStackControllerApi(ClientUtils.get_client())
    try:
        project = api_instance.get_stack(project_name)
        ClientUtils.set_current_project(project)
        return f"Current project set to {project.name}"
    except Exception as e:
        error_message = ClientUtils.extract_error_message(e)
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Failed to set project: {error_message}"
            )
        )


@mcp.tool()
def refresh_current_project():
    """
    Refresh the current project data from the server to avoid stale cache.
    
    Returns:
        Stack: The refreshed project object
        
    Raises:
        McpError: If no current project is set.
    """
    if not ClientUtils.get_current_project():
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project is set."
            )
        )

    curr_project = ClientUtils.get_current_project()
    api_instance = swagger_client.UiStackControllerApi(ClientUtils.get_client())
    refreshed_project = api_instance.get_stack(curr_project.name)
    ClientUtils.set_current_project(refreshed_project)
    return refreshed_project


@mcp.tool()
def get_secrets_and_vars():
    """
    Get all variables and secrets defined in the current project.
    
    **Purpose & Context:**
    Variables and secrets are key-value pairs that store configuration data and sensitive
    information that can be referenced by resources throughout the project. This function
    provides visibility into what configuration values are already available.
    
    **Prerequisites:**
    - Current project must be set (use `use_project()` first)
    
    **Usage Patterns:**
    - **Pre-Creation Check**: Before creating new variables to avoid duplicates
    - **Configuration Discovery**: Understanding what config values are available
    - **Resource Planning**: Knowing what references can be used in resource configs
    - **Debugging**: Troubleshooting missing or incorrect configuration values
    
    **Data Structure:**
    Returns a dictionary where:
    - Keys are variable/secret names
    - Values contain metadata (description, secret flag, default values, etc.)
    - Actual secret values are not exposed for security
    
    **LLM-Friendly Tags:** [FOUNDATIONAL] [READ-ONLY] [CONFIGURATION] [DISCOVERY]

    Returns:
        dict: Dictionary mapping variable names to their metadata and configuration
        
    **Workflow Integration:**
    - **Before** `create_variable()` - Check if name already exists
    - **Before** resource creation - See what variables can be referenced
    - **During** debugging - Verify expected variables are present
    
    **Common Patterns:**
    ```python
    vars = get_secrets_and_vars()
    if "db_password" not in vars:
        create_variable("db_password", secret_model)
    ```

    Raises:
        McpError: If no current project is set
        
    **See Also:**
    - `create_variable()` - Add new variables or secrets
    - `get_variable_by_name()` - Get specific variable details
    - `update_variable()` - Modify existing variable values
    - `use_project()` - Set project context first
    """
    if not ClientUtils.get_current_project():
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project is set."
            )
        )

    # Return the variables from the cached project
    return ClientUtils.get_current_project().cluster_variables_meta


@mcp.tool()
def get_project_details(project_name: str):
    """
    Fetch details of a specific project by name and check if it exists.

    Args:
        project_name: Name of the project to fetch details for.

    Returns:
        dict: Contains details of the project.

    Raises:
        McpError: If the project does not exist.
    
    Prompt:
        If a user directly mentions or tries to use a project, use this tool to know its
         availability and details.
    """
    api_instance = swagger_client.UiStackControllerApi(ClientUtils.get_client())
    project_details = api_instance.get_stack(project_name)

    if not project_details:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"The project '{project_name}' does not exist."
            )
        )

    return project_details


@mcp.tool()
def get_variable_by_name(name: str):
    """
    Get a specific variable by its name from the current project.

    Args:
        name: Name of the variable to retrieve.

    Returns:
        VariablesModel: The variable object corresponding to the name.

    Raises:
        McpError: If the variable does not exist.
    """
    current_vars = get_secrets_and_vars()

    if name not in current_vars:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"The variable '{name}' does not exist."
            )
        )

    return current_vars[name]


@mcp.tool()
def get_variable_environment_values(variable_name: str):
    """
    Get current values of a variable/secret across all environments in the project.
    
    **Purpose & Context:**
    Variables can have different values in different environments (dev, staging, prod).
    This function shows the project-level default value AND any environment-specific
    overrides, giving you a complete view of how a variable is configured across
    all deployment targets.
    
    **Prerequisites:**
    - Current project must be set (use `use_project()` first)
    - Variable must exist in the project (check with `get_secrets_and_vars()`)
    
    **Usage Patterns:**
    - **Configuration Audit**: Understanding how a variable differs across environments
    - **Pre-Update Planning**: Before setting environment-specific values
    - **Debugging**: When a service behaves differently in different environments
    - **Compliance Review**: Ensuring sensitive values are properly configured
    
    **When to Use:**
    - Before calling `update_variable_environment_value()` to understand current state
    - When troubleshooting environment-specific issues
    - During environment promotion workflows
    
    **LLM-Friendly Tags:** [ENVIRONMENT-AWARE] [READ-ONLY] [CONFIGURATION] [DEBUG]

    Args:
        variable_name: Name of the variable to retrieve across environments

    Returns:
        VariableEnvironmentResponse: Contains project default and environment overrides
        - `stack_default`: The project-level default value
        - `environment_values`: List of environment-specific overrides
        - `description`: Variable description and metadata
        
    **Workflow Integration:**
    1. `get_secrets_and_vars()` - Verify variable exists
    2. `get_variable_environment_values()` ← **You are here**
    3. `update_variable_environment_value()` - Set environment-specific value

    Raises:
        McpError: If no current project is set or variable does not exist
        
    **See Also:**
    - `update_variable_environment_value()` - Set environment-specific values
    - `get_secrets_and_vars()` - Check if variable exists first
    - `get_all_environments()` - See available environments
    """
    current_project = ClientUtils.get_current_project()
    if not current_project:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project is set. Please set a project using use_project()."
            )
        )

    # Check if variable exists in the project
    current_vars = get_secrets_and_vars()
    if variable_name not in current_vars:
        available_vars = list(current_vars.keys())
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Variable '{variable_name}' does not exist in project '{current_project.name}'. "
                f"Available variables: {', '.join(available_vars) if available_vars else 'None'}"
            )
        )

    api_instance = VariableManagementApi(ClientUtils.get_client())
    try:
        result = api_instance.get_variable_across_environments(current_project.name, variable_name)
        return result
    except Exception as e:
        error_message = ClientUtils.extract_error_message(e)
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Failed to retrieve variable across environments: {error_message}"
            )
        )


@mcp.tool()
def update_variable_environment_value(variable_name: str, value: str):
    """
    Set an environment-specific value for an existing project variable/secret.
    
    **Purpose & Context:**
    This function creates environment-specific overrides for variables, allowing the
    same variable to have different values in different environments (dev, staging, prod).
    For example, a database URL variable might point to different databases per environment.
    
    **Prerequisites:**
    - Current project must be set (use `use_project()` first)  
    - Current environment must be set (use `use_environment()` first)
    - Variable must already exist in the project (use `create_variable()` first)
    
    **Usage Patterns:**
    - **Environment-Specific Configuration**: Different API endpoints per environment
    - **Staged Rollouts**: Testing new values in dev before promoting to prod
    - **Security Isolation**: Different credentials for each environment
    - **Performance Tuning**: Different resource limits per environment
    
    **Important Behavior:**
    - Creates an override for the current environment only
    - Does NOT affect the project-level default value
    - Does NOT affect other environments' values
    - If environment value is removed later, falls back to project default
    
    **Critical Safety:**
    ⚠️ This modifies live configuration that affects deployed resources.
    Consider the impact on running services in the target environment.
    
    **LLM-Friendly Tags:** [ENVIRONMENT-AWARE] [CONFIGURATION] [DESTRUCTIVE] [ADVANCED]

    Args:
        variable_name: Name of the existing variable/secret to override
        value: New value to set specifically for the current environment

    Returns:
        str: Success confirmation message
        
    **Workflow Integration:**
    1. `use_project()` - Set project context
    2. `use_environment()` - Set environment context  
    3. `get_variable_environment_values()` - Check current state (optional)
    4. `update_variable_environment_value()` ← **You are here**
    
    **Example Workflow:**
    ```
    use_project("my-app")
    use_environment("production") 
    update_variable_environment_value("api_url", "https://api.prod.example.com")
    ```

    Raises:
        McpError: If no current project/environment is set, variable doesn't exist, 
                 or API call fails
                 
    **See Also:**
    - `get_variable_environment_values()` - View current values before updating
    - `use_environment()` - Set environment context first
    - `create_variable()` - Create the base variable first
    - `get_all_environments()` - See available environments
    """
    # Validate prerequisites
    current_project = ClientUtils.get_current_project()
    current_environment = ClientUtils.get_current_cluster()
    
    if not current_project:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project is set. Please set a project using use_project()."
            )
        )
    
    if not current_environment:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current environment is set. Please set an environment using use_environment()."
            )
        )

    # Check if variable exists in the project
    current_vars = get_secrets_and_vars()
    if variable_name not in current_vars:
        available_vars = list(current_vars.keys())
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Variable '{variable_name}' does not exist in project '{current_project.name}'. "
                f"Available variables: {', '.join(available_vars) if available_vars else 'None'}"
            )
        )

    try:
        api_instance = VariableManagementApi(ClientUtils.get_client())
        
        # Get current variable configuration across all environments
        current_config = api_instance.get_variable_across_environments(current_project.name, variable_name)
        
        # Build cluster_id_to_value_map with existing environment values
        cluster_id_to_value_map = {}
        if current_config.environment_values:
            for env_value in current_config.environment_values:
                if env_value.status == "OVERRIDDEN" and env_value.value:
                    cluster_id_to_value_map[env_value.cluster_id] = env_value.value
        
        # Add/update the value for the current environment
        cluster_id_to_value_map[current_environment.id] = value
        
        # Create VariableRequest with existing metadata and updated environment values
        variable_request = VariableRequest(
            variable_name=variable_name,
            description=current_config.description,
            _global=current_config._global,
            stack_default=current_config.stack_default,
            cluster_id_to_value_map=cluster_id_to_value_map,
            secret=current_config.is_secret
        )
        
        # Update the variable
        api_instance.update_variable(variable_request, current_project.name)
        
        # Refresh project cache
        ClientUtils.refresh_current_project_and_cache()
        
        return f"Successfully updated variable '{variable_name}' for environment '{current_environment.name}' with new value."
        
    except Exception as e:
        error_message = ClientUtils.extract_error_message(e)
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Failed to update variable environment value: {error_message}"
            )
        )
