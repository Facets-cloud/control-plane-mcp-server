from utils.client_utils import ClientUtils
import swagger_client
from swagger_client.models import OverrideRequest
from typing import Dict, Any, Optional
import json

mcp = ClientUtils.get_mcp_instance()


@mcp.tool()
def get_resource_overrides(resource_type: str, resource_name: str) -> Dict[str, Any]:
    """
    Get the current overrides for a specific resource in the current environment.
    
    This function retrieves any environment-specific configuration overrides that have been
    applied to a resource. These overrides modify how a resource is deployed in a specific
    environment without changing the base project configuration.
    
    Args:
        resource_type: The type of resource (e.g., service, ingress, postgres)
        resource_name: The name of the specific resource
        
    Returns:
        Dict[str, Any]: The current override configuration for the resource in the environment
        
    Raises:
        ValueError: If no current project or environment is set, or if the resource has no overrides
    """
    # Check if both project and environment are set
    if not ClientUtils.is_current_cluster_and_project_set():
        raise ValueError(
            "No current project or environment is set. "
            "Please set a project using project_tools.use_project() and an environment using env_tools.use_environment()."
        )
    
    # Get current environment
    current_environment = ClientUtils.get_current_cluster()
    cluster_id = current_environment.id
    
    # Create an instance of the API class
    api_instance = swagger_client.UiApplicationControllerApi(ClientUtils.get_client())
    
    try:
        # Call the API to get resource overrides
        override_object = api_instance.get_resource_override_object_using_get(
            cluster_id=cluster_id,
            resource_name=resource_name,
            resource_type=resource_type
        )
        
        # The API might return an empty object if there are no overrides
        if not override_object or not hasattr(override_object, 'overrides') or not override_object.overrides:
            return {"message": f"No overrides found for resource '{resource_name}' of type '{resource_type}' in environment '{current_environment.name}'"}
            
        # Convert the overrides to a dictionary
        if isinstance(override_object.overrides, str):
            overrides = json.loads(override_object.overrides)
        else:
            overrides = override_object.overrides
            
        return {
            "resource_name": resource_name,
            "resource_type": resource_type,
            "environment": current_environment.name,
            "overrides": overrides
        }
        
    except Exception as e:
        raise ValueError(f"Failed to get overrides for resource '{resource_name}' of type '{resource_type}' in environment '{current_environment.name}': {str(e)}")


@mcp.tool()
def override_resource(resource_type: str, resource_name: str, override_data: Dict[str, Any], sync: bool = True) -> Dict[str, Any]:
    """
    Create or update overrides for a specific resource in the current environment.
    
    This function allows you to customize how a resource is deployed in a specific environment
    without changing the base project configuration. The override_data should only include
    the properties you want to override - all other properties will be inherited from the
    base resource configuration.
    
    IMPORTANT: This operation can impact how resources are deployed in the environment.
    Always verify the override_data before applying it.
    
    Args:
        resource_type: The type of resource (e.g., service, ingress, postgres)
        resource_name: The name of the specific resource
        override_data: A dictionary containing only the properties to override
        sync: Whether to synchronize the changes immediately (default: True)
        
    Returns:
        Dict[str, Any]: The updated override configuration
        
    Raises:
        ValueError: If no current project or environment is set, or if the override operation fails
    """
    # Check if both project and environment are set
    if not ClientUtils.is_current_cluster_and_project_set():
        raise ValueError(
            "No current project or environment is set. "
            "Please set a project using project_tools.use_project() and an environment using env_tools.use_environment()."
        )
    
    # Get current environment
    current_environment = ClientUtils.get_current_cluster()
    cluster_id = current_environment.id
    
    # Create an instance of the API class
    api_instance = swagger_client.UiApplicationControllerApi(ClientUtils.get_client())
    
    try:
        # Create the override request object
        override_request = OverrideRequest()
        
        # Convert dictionary to JSON string if it's not already a string
        if isinstance(override_data, dict):
            override_request.overrides = json.dumps(override_data)
        else:
            override_request.overrides = override_data
            
        # Call the API to apply the override
        result = api_instance.post_resource_override_object_using_post(
            body=override_request,
            cluster_id=cluster_id,
            resource_name=resource_name,
            resource_type=resource_type,
            do_sync=sync
        )
        
        # Format and return the result
        if result and hasattr(result, 'overrides'):
            if isinstance(result.overrides, str):
                overrides = json.loads(result.overrides)
            else:
                overrides = result.overrides
                
            return {
                "message": f"Successfully applied overrides for resource '{resource_name}' of type '{resource_type}' in environment '{current_environment.name}'",
                "resource_name": resource_name,
                "resource_type": resource_type,
                "environment": current_environment.name,
                "overrides": overrides
            }
        else:
            return {
                "message": f"Override operation completed for resource '{resource_name}' of type '{resource_type}' in environment '{current_environment.name}', but no override data was returned"
            }
            
    except Exception as e:
        raise ValueError(f"Failed to override resource '{resource_name}' of type '{resource_type}' in environment '{current_environment.name}': {str(e)}")


@mcp.tool()
def remove_resource_override(resource_type: str, resource_name: str, property_path: Optional[str] = None, sync: bool = True) -> Dict[str, Any]:
    """
    Remove overrides for a specific resource or a specific property in the current environment.
    
    This function removes environment-specific configuration overrides. If property_path is
    provided, only the specified property override is removed. If property_path is not provided,
    all overrides for the resource are removed.
    
    The property_path should be a dot-separated path to the property to remove, e.g.,
    "spec.replicas" or "spec.resources.limits.memory".
    
    Args:
        resource_type: The type of resource (e.g., service, ingress, postgres)
        resource_name: The name of the specific resource
        property_path: Optional dot-separated path to the specific property to remove
        sync: Whether to synchronize the changes immediately (default: True)
        
    Returns:
        Dict[str, Any]: A message indicating the result of the operation
        
    Raises:
        ValueError: If no current project or environment is set, or if the operation fails
    """
    # Check if both project and environment are set
    if not ClientUtils.is_current_cluster_and_project_set():
        raise ValueError(
            "No current project or environment is set. "
            "Please set a project using project_tools.use_project() and an environment using env_tools.use_environment()."
        )
    
    # Get current environment
    current_environment = ClientUtils.get_current_cluster()
    cluster_id = current_environment.id
    
    # Create an instance of the API class
    api_instance = swagger_client.UiApplicationControllerApi(ClientUtils.get_client())
    
    try:
        # First, get the current overrides
        current_overrides = get_resource_overrides(resource_type, resource_name)
        
        # If there are no overrides, return a message
        if "message" in current_overrides and "No overrides found" in current_overrides["message"]:
            return {"message": f"No overrides found for resource '{resource_name}' of type '{resource_type}' in environment '{current_environment.name}'"}
            
        # If property_path is provided, only remove that specific property
        if property_path and "overrides" in current_overrides:
            # Get the current overrides
            overrides = current_overrides["overrides"]
            
            # Split the property path into parts
            path_parts = property_path.split(".")
            
            # Traverse the overrides to the parent of the property to remove
            current_level = overrides
            parent_level = None
            last_key = path_parts[-1]
            
            for i, part in enumerate(path_parts[:-1]):
                if part not in current_level:
                    return {"message": f"Property path '{property_path}' not found in overrides for resource '{resource_name}' of type '{resource_type}' in environment '{current_environment.name}'"}
                    
                parent_level = current_level
                current_level = current_level[part]
            
            # If we've reached the parent of the property to remove
            if last_key in current_level:
                # Remove the property
                del current_level[last_key]
                
                # If this makes a parent object empty, clean it up
                for i in range(len(path_parts) - 2, -1, -1):
                    parent = path_parts[:i+1]
                    child = path_parts[:i+2]
                    
                    parent_obj = overrides
                    for p in parent:
                        parent_obj = parent_obj[p]
                        
                    if not parent_obj:
                        current = overrides
                        for j in range(i):
                            current = current[path_parts[j]]
                        del current[path_parts[i]]
                
                # If the whole overrides is now empty, remove all overrides
                if not overrides:
                    # Create an empty override request
                    override_request = OverrideRequest()
                    override_request.overrides = None
                    
                    # Call the API to apply the empty override
                    api_instance.post_resource_override_object_using_post(
                        body=override_request,
                        cluster_id=cluster_id,
                        resource_name=resource_name,
                        resource_type=resource_type,
                        do_sync=sync
                    )
                    
                    return {
                        "message": f"Successfully removed all overrides for resource '{resource_name}' of type '{resource_type}' in environment '{current_environment.name}' because the overrides became empty after removing '{property_path}'"
                    }
                else:
                    # Apply the modified overrides
                    return override_resource(resource_type, resource_name, overrides, sync)
            else:
                return {"message": f"Property path '{property_path}' not found in overrides for resource '{resource_name}' of type '{resource_type}' in environment '{current_environment.name}'"}
        else:
            # Remove all overrides
            override_request = OverrideRequest()
            override_request.overrides = None
            
            # Call the API to apply the empty override
            api_instance.post_resource_override_object_using_post(
                body=override_request,
                cluster_id=cluster_id,
                resource_name=resource_name,
                resource_type=resource_type,
                do_sync=sync
            )
            
            return {
                "message": f"Successfully removed all overrides for resource '{resource_name}' of type '{resource_type}' in environment '{current_environment.name}'"
            }
            
    except Exception as e:
        raise ValueError(f"Failed to remove overrides for resource '{resource_name}' of type '{resource_type}' in environment '{current_environment.name}': {str(e)}")
