from ..utils.client_utils import ClientUtils
from ..utils.dict_utils import deep_merge
from ..utils.override_utils import get_nested_property, set_nested_property, remove_nested_property
import swagger_client
from swagger_client.models import OverrideRequest
from typing import Dict, Any, Optional, Union
import json
import copy
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INVALID_REQUEST

mcp = ClientUtils.get_mcp_instance()


@mcp.tool()
def add_or_update_override_property(resource_type: str, resource_name: str, property_path: str, value: Any) -> Dict[str, Any]:
    """
    Safely add or update a specific property in the resource overrides.
    
    This function retrieves the current overrides, adds or updates the specified property,
    and then applies the modified overrides. It will not overwrite other existing overrides.
    
    Args:
        resource_type: The type of resource (e.g., service, ingress, postgres)
        resource_name: The name of the specific resource
        property_path: Dot-separated path to the property (e.g., "spec.replicas", "spec.resources.limits.memory")
        value: The value to set for the property
        
    Returns:
        Dict[str, Any]: The updated override configuration
        
    Raises:
        McpError: If no current project or environment is set, or if the operation fails
    """
    # Check if both project and environment are set
    if not ClientUtils.is_current_cluster_and_project_set():
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project or environment is set. Please set a project using project_tools.use_project() and an environment using env_tools.use_environment()."
            )
        )
    
    # Get current environment
    current_environment = ClientUtils.get_current_cluster()
    cluster_id = current_environment.id
    
    # Create an instance of the API class
    api_instance = swagger_client.UiApplicationControllerApi(ClientUtils.get_client())
    
    try:
        # Get current overrides
        try:
            current_override_obj = api_instance.get_resource_override_object(
                cluster_id=cluster_id,
                resource_name=resource_name,
                resource_type=resource_type
            )
            
            # Parse existing overrides
            if current_override_obj and hasattr(current_override_obj, 'overrides') and current_override_obj.overrides:
                if isinstance(current_override_obj.overrides, str):
                    current_overrides = json.loads(current_override_obj.overrides)
                else:
                    current_overrides = current_override_obj.overrides
            else:
                current_overrides = {}
        except Exception:
            # If getting current overrides fails, start with empty overrides
            current_overrides = {}
        
        # Set the new property value
        set_nested_property(current_overrides, property_path, value)
        
        # Create the override request
        override_request = OverrideRequest()
        override_request.overrides = current_overrides
        
        # Apply the updated overrides
        result = api_instance.post_resource_override_object(
            body=override_request,
            cluster_id=cluster_id,
            resource_name=resource_name,
            resource_type=resource_type
        )
        
        # Format and return the result
        return {
            "message": f"Successfully updated override property '{property_path}' for resource '{resource_name}' of type '{resource_type}' in environment '{current_environment.name}'",
            "resource_name": resource_name,
            "resource_type": resource_type,
            "environment": current_environment.name,
            "property_path": property_path,
            "new_value": value,
            "all_overrides": current_overrides
        }
        
    except Exception as e:
        error_message = ClientUtils.extract_error_message(e)
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Failed to update override property '{property_path}' for resource '{resource_name}' of type '{resource_type}' in environment '{current_environment.name}': {error_message}"
            )
        )


@mcp.tool()
def remove_override_property(resource_type: str, resource_name: str, property_path: str) -> Dict[str, Any]:
    """
    Remove a specific property from the resource overrides.
    
    This function removes only the specified property from the overrides, leaving all
    other overrides intact. Empty parent objects are automatically cleaned up.
    
    Args:
        resource_type: The type of resource (e.g., service, ingress, postgres)
        resource_name: The name of the specific resource
        property_path: Dot-separated path to the property (e.g., "spec.replicas", "spec.resources.limits.memory")
        
    Returns:
        Dict[str, Any]: Result of the operation including remaining overrides
        
    Raises:
        McpError: If no current project or environment is set, or if the operation fails
    """
    # Check if both project and environment are set
    if not ClientUtils.is_current_cluster_and_project_set():
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project or environment is set. Please set a project using project_tools.use_project() and an environment using env_tools.use_environment()."
            )
        )
    
    # Get current environment
    current_environment = ClientUtils.get_current_cluster()
    cluster_id = current_environment.id
    
    # Create an instance of the API class
    api_instance = swagger_client.UiApplicationControllerApi(ClientUtils.get_client())
    
    try:
        # Get current overrides
        try:
            current_override_obj = api_instance.get_resource_override_object(
                cluster_id=cluster_id,
                resource_name=resource_name,
                resource_type=resource_type
            )
            
            # Parse existing overrides
            if current_override_obj and hasattr(current_override_obj, 'overrides') and current_override_obj.overrides:
                if isinstance(current_override_obj.overrides, str):
                    current_overrides = json.loads(current_override_obj.overrides)
                else:
                    current_overrides = current_override_obj.overrides
            else:
                return {
                    "message": f"No overrides found for resource '{resource_name}' of type '{resource_type}' in environment '{current_environment.name}'",
                    "resource_name": resource_name,
                    "resource_type": resource_type,
                    "environment": current_environment.name,
                    "property_path": property_path
                }
        except Exception:
            return {
                "message": f"No overrides found for resource '{resource_name}' of type '{resource_type}' in environment '{current_environment.name}'",
                "resource_name": resource_name,
                "resource_type": resource_type,
                "environment": current_environment.name,
                "property_path": property_path
            }
        
        # Remove the specified property
        if not remove_nested_property(current_overrides, property_path):
            return {
                "message": f"Property '{property_path}' not found in overrides for resource '{resource_name}' of type '{resource_type}' in environment '{current_environment.name}'",
                "resource_name": resource_name,
                "resource_type": resource_type,
                "environment": current_environment.name,
                "property_path": property_path,
                "current_overrides": current_overrides
            }
        
        # Create the override request
        override_request = OverrideRequest()
        
        if current_overrides:
            # If there are still overrides left, update them
            override_request.overrides = current_overrides
        else:
            # If no overrides left, clear all overrides
            override_request.overrides = {}
        
        # Apply the updated overrides
        result = api_instance.post_resource_override_object(
            body=override_request,
            cluster_id=cluster_id,
            resource_name=resource_name,
            resource_type=resource_type
        )
        
        # Format and return the result
        message = f"Successfully removed override property '{property_path}' for resource '{resource_name}' of type '{resource_type}' in environment '{current_environment.name}'"
        if not current_overrides:
            message += " (all overrides have been cleared)"
        
        return {
            "message": message,
            "resource_name": resource_name,
            "resource_type": resource_type,
            "environment": current_environment.name,
            "property_path": property_path,
            "remaining_overrides": current_overrides or None
        }
        
    except Exception as e:
        error_message = ClientUtils.extract_error_message(e)
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Failed to remove override property '{property_path}' for resource '{resource_name}' of type '{resource_type}' in environment '{current_environment.name}': {error_message}"
            )
        )


@mcp.tool()
def replace_all_overrides(resource_type: str, resource_name: str, override_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Replace all existing overrides with a completely new override configuration.
    
    WARNING: This function will COMPLETELY REPLACE all existing overrides for the resource.
    Any existing overrides will be lost. Use add_or_update_override_property() if you want
    to modify specific properties while preserving other overrides.
    
    Args:
        resource_type: The type of resource (e.g., service, ingress, postgres)
        resource_name: The name of the specific resource
        override_data: A dictionary containing the complete new override configuration
        
    Returns:
        Dict[str, Any]: The new override configuration
        
    Raises:
        McpError: If no current project or environment is set, or if the operation fails
    """
    # Check if both project and environment are set
    if not ClientUtils.is_current_cluster_and_project_set():
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project or environment is set. Please set a project using project_tools.use_project() and an environment using env_tools.use_environment()."
            )
        )
    
    # Get current environment
    current_environment = ClientUtils.get_current_cluster()
    cluster_id = current_environment.id
    
    # Create an instance of the API class
    api_instance = swagger_client.UiApplicationControllerApi(ClientUtils.get_client())
    
    try:
        # Create the override request object
        override_request = OverrideRequest()
        override_request.overrides = override_data
        
        # Call the API to apply the override
        result = api_instance.post_resource_override_object(
            body=override_request,
            cluster_id=cluster_id,
            resource_name=resource_name,
            resource_type=resource_type
        )
        
        # Format and return the result
        return {
            "message": f"Successfully replaced all overrides for resource '{resource_name}' of type '{resource_type}' in environment '{current_environment.name}'",
            "resource_name": resource_name,
            "resource_type": resource_type,
            "environment": current_environment.name,
            "new_overrides": override_data
        }
        
    except Exception as e:
        error_message = ClientUtils.extract_error_message(e)
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Failed to replace overrides for resource '{resource_name}' of type '{resource_type}' in environment '{current_environment.name}': {error_message}"
            )
        )


@mcp.tool()
def clear_all_overrides(resource_type: str, resource_name: str) -> Dict[str, Any]:
    """
    Remove all overrides for a resource in the current environment.
    
    This function completely removes all environment-specific overrides for the resource,
    causing it to use only the base configuration from the project.
    
    Args:
        resource_type: The type of resource (e.g., service, ingress, postgres)
        resource_name: The name of the specific resource
        
    Returns:
        Dict[str, Any]: A message indicating the result of the operation
        
    Raises:
        McpError: If no current project or environment is set, or if the operation fails
    """
    # Check if both project and environment are set
    if not ClientUtils.is_current_cluster_and_project_set():
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project or environment is set. Please set a project using project_tools.use_project() and an environment using env_tools.use_environment()."
            )
        )
    
    # Get current environment
    current_environment = ClientUtils.get_current_cluster()
    cluster_id = current_environment.id
    
    # Create an instance of the API class
    api_instance = swagger_client.UiApplicationControllerApi(ClientUtils.get_client())
    
    try:
        # Create an empty override request
        override_request = OverrideRequest()
        override_request.overrides = {}
        
        # Call the API to clear all overrides
        result = api_instance.post_resource_override_object(
            body=override_request,
            cluster_id=cluster_id,
            resource_name=resource_name,
            resource_type=resource_type
        )
        
        return {
            "message": f"Successfully cleared all overrides for resource '{resource_name}' of type '{resource_type}' in environment '{current_environment.name}'",
            "resource_name": resource_name,
            "resource_type": resource_type,
            "environment": current_environment.name
        }
        
    except Exception as e:
        error_message = ClientUtils.extract_error_message(e)
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Failed to clear overrides for resource '{resource_name}' of type '{resource_type}' in environment '{current_environment.name}': {error_message}"
            )
        )


@mcp.tool()
def preview_override_effect(resource_type: str, resource_name: str, property_path: str, value: Any) -> Dict[str, Any]:
    """
    Preview what the effective configuration would be if a specific override is applied.
    
    This function shows the result of applying a proposed override without actually
    modifying the resource. Useful for understanding the impact before making changes.
    
    Args:
        resource_type: The type of resource (e.g., service, ingress, postgres)
        resource_name: The name of the specific resource
        property_path: Dot-separated path to the property (e.g., "spec.replicas")
        value: The proposed value for the property
        
    Returns:
        Dict[str, Any]: Preview of the effective configuration with the proposed change
        
    Raises:
        McpError: If no current project or environment is set, or if the operation fails
    """
    # Check if both project and environment are set
    if not ClientUtils.is_current_cluster_and_project_set():
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project or environment is set. Please set a project using project_tools.use_project() and an environment using env_tools.use_environment()."
            )
        )
    
    # Get current environment
    current_environment = ClientUtils.get_current_cluster()
    cluster_id = current_environment.id
    
    # Create API instances
    dropdown_api = swagger_client.UiDropdownsControllerApi(ClientUtils.get_client())
    override_api = swagger_client.UiApplicationControllerApi(ClientUtils.get_client())
    
    try:
        # Get the current resource configuration
        resource = dropdown_api.get_resource_by_cluster_id(
            cluster_id=cluster_id,
            resource_name=resource_name,
            resource_type=resource_type,
            include_content=True
        )
        
        # Parse base content
        base_config = json.loads(resource.content) if resource.content else {}
        
        # Get current overrides
        current_overrides = {}
        try:
            current_override_obj = override_api.get_resource_override_object(
                cluster_id=cluster_id,
                resource_name=resource_name,
                resource_type=resource_type
            )
            
            if current_override_obj and hasattr(current_override_obj, 'overrides') and current_override_obj.overrides:
                if isinstance(current_override_obj.overrides, str):
                    current_overrides = json.loads(current_override_obj.overrides)
                else:
                    current_overrides = current_override_obj.overrides
        except Exception:
            # No current overrides
            pass
        
        # Create a copy of current overrides with the proposed change
        proposed_overrides = copy.deepcopy(current_overrides)
        set_nested_property(proposed_overrides, property_path, value)
        
        # Calculate the effective configuration
        current_effective = deep_merge(copy.deepcopy(base_config), current_overrides) if current_overrides else base_config
        proposed_effective = deep_merge(copy.deepcopy(base_config), proposed_overrides)
        
        return {
            "resource_name": resource_name,
            "resource_type": resource_type,
            "environment": current_environment.name,
            "property_path": property_path,
            "proposed_value": value,
            "current_overrides": current_overrides or None,
            "proposed_overrides": proposed_overrides,
            "current_effective_config": current_effective,
            "proposed_effective_config": proposed_effective
        }
        
    except Exception as e:
        error_message = ClientUtils.extract_error_message(e)
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Failed to preview override effect for resource '{resource_name}' of type '{resource_type}' in environment '{current_environment.name}': {error_message}"
            )
        )

