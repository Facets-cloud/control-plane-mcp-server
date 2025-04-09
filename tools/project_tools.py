from pydantic_generated.variablesmodel import VariablesModel
from utils.client_utils import ClientUtils
import swagger_client
from swagger_client.models import Variables
from typing import List, Dict

mcp = ClientUtils.get_mcp_instance()


@mcp.tool()
def get_all_projects() -> str:
    """
    Retrieve all projects

    Returns:
        str: List of all projects
    """
    api_instance = swagger_client.UiStackControllerApi(ClientUtils.get_client())
    return api_instance.get_stacks_using_get1()


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
def create_variables(variables: Dict[str, VariablesModel]) -> None:
    """
    Create multiple new variables in the current project.

    Args:
        variables: Dictionary with variable names as keys and VariablesModel objects as values.
                  Each VariablesModel should contain:
                  - description: (str) Optional description of the variable
                  - secret: (bool) Whether this is a secret variable
                  - value: (str) The actual value of the variable
                  - global: (bool) Always set to False

        Prompt:
            Ask the user to describe the variables they want to create — what they're for,
            whether they should be treated as secrets, and their values. Use this conversation
            to infer meaningful descriptions and default values. Confirm your understanding
            with the user and allow edits before creating the variables.

    Raises:
        ValueError: If any of the variables already exist.
    """
    current_vars = get_secrets_and_vars()
    curr_project = ClientUtils.get_current_project()
    ClientUtils.set_current_project(curr_project)

    # Check if any variables already exist
    existing_vars = [name for name in variables.keys() if name in current_vars]
    if existing_vars:
        raise ValueError(f"The following variables already exist: {', '.join(existing_vars)}")

    # Convert all variables to swagger format
    variables_swagger_dict = {}
    for name, var in variables.items():
        variables_swagger_dict[name] = ClientUtils.pydantic_instance_to_swagger_instance(var, Variables)

    api_instance = swagger_client.UiBlueprintDesignerControllerApi(ClientUtils.get_client())
    result = api_instance.add_variables_using_post(curr_project.name, variables_swagger_dict)
    
    # Refresh the project to update the cache
    refresh_current_project()
    
    return result

@mcp.tool()
def update_variables(variables: Dict[str, VariablesModel]) -> None:
    """
    Update multiple existing variables in the current project.

    Args:
        variables: Dictionary with variable names as keys and VariablesModel objects as values.
                  Each VariablesModel should contain:
                  - description: (str) Optional description of the variable
                  - secret: (bool) Whether this is a secret variable
                  - value: (str) The actual value of the variable
                  - global: (bool) Always set to False

        Prompt:
            Ask the user which variables they want to update and what changes they want to make.
            Verify that all variables exist before attempting to update them.
            Confirm your understanding with the user and allow edits before updating the variables.

    Raises:
        ValueError: If any of the variables do not exist.
    """
    current_vars = get_secrets_and_vars()
    curr_project = ClientUtils.get_current_project()
    ClientUtils.set_current_project(curr_project)

    # Check if all variables exist
    missing_vars = [name for name in variables.keys() if name not in current_vars]
    if missing_vars:
        raise ValueError(f"The following variables do not exist: {', '.join(missing_vars)}")

    # Convert all variables to swagger format
    variables_swagger_dict = {}
    for name, var in variables.items():
        variables_swagger_dict[name] = ClientUtils.pydantic_instance_to_swagger_instance(var, Variables)

    api_instance = swagger_client.UiBlueprintDesignerControllerApi(ClientUtils.get_client())
    result = api_instance.update_variables_using_put(curr_project.name, variables_swagger_dict)
    
    # Refresh the project to update the cache
    refresh_current_project()
    
    return result

@mcp.tool()
def delete_variables(variable_names: List[str]) -> None:
    """
    Delete multiple variables from the current project.

    Args:
        variable_names: List of names of the variables to delete.

        Prompt:
            Ask the user which variables they want to delete.
            Confirm deletion with the user before proceeding as this action cannot be undone.
            Verify that all variables exist before attempting to delete them.

    Raises:
        ValueError: If any of the variables do not exist.
    """
    current_vars = get_secrets_and_vars()
    curr_project = ClientUtils.get_current_project()
    ClientUtils.set_current_project(curr_project)

    # Check if all variables exist
    missing_vars = [name for name in variable_names if name not in current_vars]
    if missing_vars:
        raise ValueError(f"The following variables do not exist: {', '.join(missing_vars)}")

    api_instance = swagger_client.UiBlueprintDesignerControllerApi(ClientUtils.get_client())
    result = api_instance.delete_variables_using_delete(curr_project.name, variable_names)
    
    # Refresh the project to update the cache
    refresh_current_project()
    
    return result
