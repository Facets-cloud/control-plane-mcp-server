from pydantic_generated.variablesmodel import VariablesModel
from utils.client_utils import ClientUtils
import swagger_client
from swagger_client.models import Variables, BlueprintFile, ResourceFileRequest
from typing import List, Dict, Any, Optional
import json

mcp = ClientUtils.get_mcp_instance()


@mcp.tool()
def get_all_projects() -> str:
    """
    Retrieve all projects

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


@mcp.tool()
def get_all_resources_by_project(project_name: str) -> List[Dict[str, Any]]:
    """
    Get all resources for a specific project.

    Args:
        project_name: The name of the project to retrieve resources for
    """
    api_instance = swagger_client.UiDropdownsControllerApi(ClientUtils.get_client())
    
    try:
        # Call the API to get all resources for the project
        resources = api_instance.get_all_resources_by_stack_using_get(project_name, include_content=True)
        
        # Extract and transform the relevant information
        result = []
        for resource in resources:
            resource_data = {
                "name": resource.resource_name,
                "type": resource.resource_type,  # This is the intent/resource type
                "directory": resource.directory,
                "filename": resource.filename,
                "content": json.loads(resource.content) if resource.content else None
            }
            result.append(resource_data)
            
        return result
    
    except Exception as e:
        raise ValueError(f"Failed to get resources for project '{project_name}': {str(e)}")


@mcp.tool()
def get_resource_by_project(project_name: str, resource_type: str, resource_name: str) -> Dict[str, Any]:
    """
    Get a specific resource by type and name for a project.

    Args:
        project_name: The name of the project to retrieve the resource from
        resource_type: The type of resource to retrieve (e.g., service, ingress, postgres, redis)
        resource_name: The name of the specific resource to retrieve
    """
    api_instance = swagger_client.UiDropdownsControllerApi(ClientUtils.get_client())
    
    try:
        # Call the API directly with resource name, type, and project name
        resource = api_instance.get_resource_by_stack_using_get(resource_name, resource_type, project_name)
        
        # Format the response
        resource_data = {
            "name": resource.resource_name,
            "type": resource.resource_type,
            "directory": resource.directory,
            "filename": resource.filename,
            "content": json.loads(resource.content) if resource.content else None,
            "info": resource.info.to_dict() if resource.info else None  # Add the info object as a separate field
        }
            
        return resource_data
        
    except Exception as e:
        raise ValueError(f"Failed to get resource '{resource_name}' of type '{resource_type}' for project '{project_name}': {str(e)}")


@mcp.tool()
def get_spec_for_resource(project_name: str, resource_type: str, resource_name: str) -> Dict[str, Any]:
    """
    Get specification details for a specific resource in a project.

    Args:
        project_name: The name of the project the resource belongs to
        resource_type: The type of resource (e.g., service, ingress, postgres, redis)
        resource_name: The name of the specific resource
    """
    # First, get the resource details to extract intent, flavor, and version
    try:
        # Get the specific resource
        resource = get_resource_by_project(project_name, resource_type, resource_name)
        
        # Extract intent (resource_type), flavor, and version from info
        if not resource.get("info"):
            raise ValueError(f"Resource '{resource_name}' of type '{resource_type}' does not have info data")
        
        # Get info section
        info = resource["info"]
        
        # Extract flavor and version
        flavor = info.get("flavour")  # Note: flavour is the field name used in the Info model
        version = info.get("version")
        
        # Validate required fields
        if not flavor:
            raise ValueError(f"Resource '{resource_name}' of type '{resource_type}' does not have a flavor defined")
        if not version:
            raise ValueError(f"Resource '{resource_name}' of type '{resource_type}' does not have a version defined")
            
        # Now call the TF Module API to get the spec
        api_instance = swagger_client.UiTfModuleControllerApi(ClientUtils.get_client())
        module_response = api_instance.get_module_for_ifv_and_stack_using_get(
            flavor=flavor,
            intent=resource_type,
            stack_name=project_name,
            version=version
        )
        
        # Extract and parse the spec from the response
        if not module_response.spec:
            raise ValueError(f"No specification found for resource '{resource_name}' of type '{resource_type}'")
            
        # Return the spec as a JSON object
        return json.loads(module_response.spec)
        
    except Exception as e:
        raise ValueError(f"Failed to get specification for resource '{resource_name}' of type '{resource_type}' in project '{project_name}': {str(e)}")


@mcp.tool()
def update_resource(project_name: str, resource_type: str, resource_name: str, content: Dict[str, Any]) -> None:
    """
    Update a specific resource in a project.

    Args:
        project_name: The name of the project containing the resource
        resource_type: The type of resource to update (e.g., service, ingress, postgres)
        resource_name: The name of the specific resource to update
        content: The updated content for the resource as a dictionary

    Raises:
        ValueError: If the resource doesn't exist or update fails
    """
    try:
        # First, get the current resource to obtain metadata
        current_resource = get_resource_by_project(project_name, resource_type, resource_name)
        
        # Create a ResourceFileRequest instance with the updated content
        request = ResourceFileRequest()
        request.content = content
        request.directory = current_resource.get("directory")
        request.filename = current_resource.get("filename")
        request.resource_name = resource_name
        request.resource_type = resource_type

        # Get the branch from the stack info (default to "master" if not specified)
        api_stack = swagger_client.UiStackControllerApi(ClientUtils.get_client())
        stack = api_stack.get_stack_using_get(project_name)
        branch = stack.branch if hasattr(stack, 'branch') and stack.branch else None

        # Call the API to update the resource
        api_instance = swagger_client.UiBlueprintDesignerControllerApi(ClientUtils.get_client())
        result = api_instance.create_resources_using_post(branch, [request], project_name)

        return result
        
    except Exception as e:
        raise ValueError(f"Failed to update resource '{resource_name}' of type '{resource_type}' in project '{project_name}': {str(e)}")
