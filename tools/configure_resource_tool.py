from utils.client_utils import ClientUtils
import swagger_client
from swagger_client.models import ResourceFileRequest
from typing import List, Dict, Any
import json
import project_tools

mcp = ClientUtils.get_mcp_instance()


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
        resource_request = ResourceFileRequest()
        resource_request.content = content
        resource_request.directory = current_resource.get("directory")
        resource_request.filename = current_resource.get("filename")
        resource_request.resource_name = resource_name
        resource_request.resource_type = resource_type
        
        # Get default branch (typically "master")
        api_stack = swagger_client.UiStackControllerApi(ClientUtils.get_client())
        stack = api_stack.get_stack_using_get(project_name)
        branch = stack.branch if hasattr(stack, 'branch') and stack.branch else None
        
        # Create an API instance and update the resource
        api_instance = swagger_client.UiBlueprintDesignerControllerApi(ClientUtils.get_client())
        result = api_instance.update_resources_using_put(branch, [resource_request], project_name)
        
        return result
        
    except Exception as e:
        raise ValueError(f"Failed to update resource '{resource_name}' of type '{resource_type}' in project '{project_name}': {str(e)}")
