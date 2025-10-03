from ..utils.client_utils import ClientUtils
from ..utils.dict_utils import deep_merge
from ..config import mcp
import swagger_client
from typing import List, Dict, Any, Optional, Annotated
import json
import copy
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INVALID_REQUEST


@mcp.tool()
def get_all_resources_by_environment(
    limit: Annotated[int, "Maximum number of resources to return (default: 50)"] = 50,
    offset: Annotated[int, "Number of resources to skip (default: 0)"] = 0,
    search: str = None,
    resource_type: str = None
) -> Dict[str, Any]:
    """
    Get all resources for the current environment (cluster) with pagination and filtering.

    Returns paginated list of resources with metadata. Default returns first 50 resources.
    Use limit/offset for pagination, search for name filtering, resource_type for type filtering.

    Args:
        limit: Maximum number of resources to return (default: 50)
        offset: Number of resources to skip for pagination (default: 0)
        search: Optional - Filter by resource name (case-insensitive partial match)
        resource_type: Optional - Filter by resource type (e.g., service, postgres, redis, mongo)

    Returns:
        Dict containing:
            - resources: List of resource objects
            - pagination: Metadata (total, limit, offset, has_more)
            - filters_applied: Active filters (if any)

    Raises:
        McpError: If no current project or environment is set.
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
    api_instance = swagger_client.UiDropdownsControllerApi(ClientUtils.get_client())

    try:
        # Call the API to get all resources for the environment
        resources = api_instance.get_all_resources_by_cluster(
            cluster_id=cluster_id,
            include_content=False
        )

        # Extract and transform the relevant information
        all_resources = []
        for resource in resources:
            # Check if resource should be excluded
            should_exclude = False

            # Safely check if resource.info.ui.base_resource exists and is True
            try:
                if not resource.directory:
                    should_exclude = True
                if resource.info and resource.info.ui and resource.info.ui.get("base_resource"):
                    should_exclude = True
            except AttributeError:
                # If any attribute is missing along the path, don't exclude
                pass

            # Only include resources that shouldn't be excluded
            if not should_exclude:
                resource_data = {
                    "name": resource.resource_name,
                    "type": resource.resource_type,
                    "directory": resource.directory,
                    "filename": resource.filename,
                    "info": resource.info.to_dict() if resource.info else None
                }
                all_resources.append(resource_data)

        # Apply filters
        filtered_resources = all_resources
        filters_applied = {}

        if resource_type:
            filtered_resources = [r for r in filtered_resources if r["type"] == resource_type]
            filters_applied["resource_type"] = resource_type

        if search:
            search_lower = search.lower()
            filtered_resources = [r for r in filtered_resources if search_lower in r["name"].lower()]
            filters_applied["search"] = search

        # Calculate pagination
        total_count = len(filtered_resources)
        start_idx = offset
        end_idx = offset + limit
        paginated_resources = filtered_resources[start_idx:end_idx]
        has_more = end_idx < total_count

        return {
            "resources": paginated_resources,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "returned": len(paginated_resources),
                "has_more": has_more
            },
            "filters_applied": filters_applied if filters_applied else None
        }

    except Exception as e:
        error_message = ClientUtils.extract_error_message(e)
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Failed to get resources for environment '{current_environment.name}': {error_message}"
            )
        )


@mcp.tool()
def get_resource_by_environment(resource_type: str, resource_name: str) -> Dict[str, Any]:
    """
    Get a specific resource by type and name for the current environment (cluster).
    
    This returns the resource configuration including the base JSON, overrides,
    effective configuration (deep merge of base + overrides), and override flag.
    
    Args:
        resource_type: The type of resource to retrieve (e.g., service, ingress, postgres, redis)
        resource_name: The name of the specific resource to retrieve
        
    Returns:
        Dict[str, Any]: Resource details including:
            - name: Resource name
            - type: Resource type
            - directory: Resource directory
            - filename: Resource filename
            - module_id: Terraform module ID (if available)
            - base_config: The base JSON configuration
            - overrides: Override configuration (if any)
            - effective_config: Deep merged configuration (base + overrides)
            - is_overridden: Boolean indicating if resource has overrides
            - info: Resource info object
            - errors: Any validation errors (if present)
        
    Raises:
        McpError: If no current project or environment is set, or if the resource is not found.
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
    api_instance = swagger_client.UiDropdownsControllerApi(ClientUtils.get_client())
    
    try:
        # Call the API directly with resource name, type, and cluster id
        resource = api_instance.get_resource_by_cluster_id(
            cluster_id=cluster_id,
            resource_name=resource_name,
            resource_type=resource_type,
            include_content=True
        )
        
        # Parse base content
        base_config = json.loads(resource.content) if resource.content else None
        
        # Get override configuration
        overrides = None
        if hasattr(resource, 'override') and resource.override:
            overrides = resource.override
        
        # Check if resource is overridden
        is_overridden = False
        if hasattr(resource, 'overridden'):
            is_overridden = resource.overridden
        elif overrides is not None:
            # Fallback: if we have overrides but no overridden flag, assume it's overridden
            is_overridden = True
        
        # Calculate effective configuration (deep merge of base + overrides)
        effective_config = base_config
        if base_config and overrides:
            effective_config = deep_merge(copy.deepcopy(base_config), overrides)
        
        # Format the response
        resource_data = {
            "name": resource.resource_name,
            "type": resource.resource_type,
            "directory": resource.directory,
            "filename": resource.filename,
            "module_id": resource.info.tf_module_id if (resource.info and hasattr(resource.info, 'tf_module_id')) else None,
            "base_config": base_config,
            "overrides": overrides,
            "effective_config": effective_config,
            "is_overridden": is_overridden,
            "info": resource.info.to_dict() if resource.info else None
        }
        
        # Add errors if any exist
        if hasattr(resource, 'errors') and resource.errors:
            errors = []
            for error in resource.errors:
                error_info = {
                    "message": error.message,
                    "category": error.category,
                    "severity": error.severity if hasattr(error, 'severity') else None
                }
                errors.append(error_info)
            resource_data["errors"] = errors
            
        return resource_data
        
    except Exception as e:
        error_message = ClientUtils.extract_error_message(e)
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Failed to get resource '{resource_name}' of type '{resource_type}' for environment '{current_environment.name}': {error_message}"
            )
        )
