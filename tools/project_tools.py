from pydantic_generated.variablesmodel import VariablesModel
from utils.client_utils import ClientUtils
import swagger_client
from swagger_client.models import Variables

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

    # Assuming _current_project has fields `secrets` and `vars`
    return ClientUtils.get_current_project().cluster_variables_meta,


@mcp.tool()
def create_variable(variable_name: str, variable: VariablesModel) -> None:
    """
    Create a new variable in the current project.

    Args:
        variable_name: The unique name of the variable to create.
        variable: A VariablesModel object containing:
            - description: (str) Optional description of the variable
            - secret: (bool) Whether this is a secret variable
            - value: (str) The actual value of the variable
            - global: (bool) Always set to False

        Prompt:
            Ask the user to describe the new variable they want to create — what it’s for, whether it should be treated as a secret, and what its value should be. Use this conversation to infer a meaningful description and default value. Confirm your understanding with the user and allow edits before creating the variable.

    Raises:
        ValueError: If a variable with the same name already exists.
    """
    variable_swagger_dict = ClientUtils.pydantic_instance_to_swagger_instance(variable, Variables)
    current_vars = get_secrets_and_vars()
    curr_project = ClientUtils.get_current_project()
    ClientUtils.set_current_project(curr_project)

    if variable_name in current_vars:
        raise ValueError("Variable already exists.")

    api_instance = swagger_client.UiBlueprintDesignerControllerApi(ClientUtils.get_client())
    return api_instance.add_variables_using_post(curr_project.name, {variable_name: variable_swagger_dict})
