from pydantic_generated.variablesmodel import VariablesModel
from utils.client_utils import ClientUtils
import swagger_client
from swagger_client.models import Variables
from typing import List, Dict

mcp = ClientUtils.get_mcp_instance()

@mcp.tool()
def create_variable(name: str, variable: VariablesModel) -> None:
    """
    Create a new variable in the current project.

    Args:
        name: Name of the variable to create.
        variable: VariablesModel object of the variable to create.

    Raises:
        ValueError: If the variable already exists.

    After:
        Call `get_variable_by_name` to confirm the variable was created correctly and show it to the user.
    """
    current_vars = get_secrets_and_vars()
    current_project = ClientUtils.get_current_project()

    if name in current_vars:
        raise ValueError(f"The variable '{name}' already exists.")

    variable_swagger_instance = ClientUtils.pydantic_instance_to_swagger_instance(variable, Variables)

    api_instance = swagger_client.UiBlueprintDesignerControllerApi(ClientUtils.get_client())
    result = api_instance.add_variables_using_post(current_project.name, {name: variable_swagger_instance})
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
        ValueError: If the variable does not exist.

    After:
        Call `get_variable_by_name` to confirm the updated value and show it to the user.
    """
    current_vars = get_secrets_and_vars()
    current_project = ClientUtils.get_current_project()

    if name not in current_vars:
        raise ValueError(f"The variable '{name}' does not exist.")

    variable_swagger_instance = ClientUtils.pydantic_instance_to_swagger_instance(variable, Variables)

    api_instance = swagger_client.UiBlueprintDesignerControllerApi(ClientUtils.get_client())
    result = api_instance.update_variables_using_put(current_project.name, {name: variable_swagger_instance})
    ClientUtils.refresh_current_project_and_cache()

    return result

@mcp.tool()
def delete_variable(name: str) -> None:
    """
    Delete a variable from the current project.

    Args:
        name: Name of the variable to delete.

    Raises:
        ValueError: If the variable does not exist.

    After:
        Call `get_secrets_and_vars` to confirm the variable was removed and inform the user.
    """
    current_vars = get_secrets_and_vars()
    current_project = ClientUtils.get_current_project()

    if name not in current_vars:
        raise ValueError(f"The variable '{name}' does not exist.")

    api_instance = swagger_client.UiBlueprintDesignerControllerApi(ClientUtils.get_client())
    result = api_instance.delete_variables_using_delete(current_project.name, [name])
    ClientUtils.refresh_current_project_and_cache()

    return result

@mcp.tool()
def get_all_projects() -> str:
    """
    Retrieve and return the names of **all** projects (stacks).

    Use this only if the user explicitly requests **all projects**,
    as this can be a large list. For specific queries, use `get_project_details`.

    Returns:
        str: List of all projects
    """
    api_instance = swagger_client.UiStackControllerApi(ClientUtils.get_client())
    stacks = api_instance.get_stacks_using_get1()
    # Extract just the stack names and return them as a formatted string
    stack_names = [stack.name for stack in stacks]
    return "\n".join(stack_names) if stack_names else "No projects found"

@mcp.tool()
def use_project(project_name: str):
    """
    Set the current project in ClientUtils

    Args:
        project_name: Name of the project to set as current
    """
    api_instance = swagger_client.UiStackControllerApi(ClientUtils.get_client())
    try:
        project = api_instance.get_stack_using_get(project_name)
        ClientUtils.set_current_project(project)
        return f"Current project set to {project.name}"
    except Exception as e:
        raise ValueError(f"Failed to set project: {str(e)}")

@mcp.tool()
def refresh_current_project():
    """
    Refresh the current project data from the server to avoid stale cache.
    
    Returns:
        Stack: The refreshed project object
        
    Raises:
        ValueError: If no current project is set.
    """
    if not ClientUtils.get_current_project():
        raise ValueError("No current project is set.")

    curr_project = ClientUtils.get_current_project()
    api_instance = swagger_client.UiStackControllerApi(ClientUtils.get_client())
    refreshed_project = api_instance.get_stack_using_get(curr_project.name)
    ClientUtils.set_current_project(refreshed_project)
    return refreshed_project

@mcp.tool()
def get_secrets_and_vars():
    """
    Get secrets and vars of the current project. Use This to Prompt user If a variable
    already exists, before calling create_variable

    Returns:
        dict: Contains secrets and vars of the current project.

    Raises:
        ValueError: If no current project is set.
    """
    if not ClientUtils.get_current_project():
        raise ValueError("No current project is set.")

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
        ValueError: If the project does not exist.
    
    Prompt:
        If a user directly mentions or tries to use a project, use this tool to know its
         availability and details.
    """
    api_instance = swagger_client.UiStackControllerApi(ClientUtils.get_client())
    project_details = api_instance.get_stack_using_get(project_name)

    if not project_details:
        raise ValueError(f"The project '{project_name}' does not exist.")

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
        ValueError: If the variable does not exist.
    """
    current_vars = get_secrets_and_vars()
    
    if name not in current_vars:
        raise ValueError(f"The variable '{name}' does not exist.")

    return current_vars[name]
