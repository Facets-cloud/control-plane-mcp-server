"""
RESOURCE CONFIGURATION TOOLS

Tools for discovering, creating, and managing infrastructure resources in Facets projects.
Resources use organization-specific abstractions rather than standard cloud provider formats.

**Critical Schema Understanding:**
Facets resources have custom schemas that abstract complex infrastructure into simplified,
organization-defined patterns. Each resource type (postgres, service, redis) has unique property
names, validation rules, and special annotations. Never assume standard property names like "host"
or "port" - the organization may use "database_endpoint" or "connection_config" instead.

**Essential Workflow Context:**
1. **Discovery**: Use `list_available_resources()` to find available resource types and flavors
2. **Schema Analysis**: Use `get_resource_schema_public()` to understand actual property names and requirements
3. **Template Review**: Use `get_sample_for_module()` to see schema structure in practice
4. **Dependency Check**: Use `get_module_inputs()` to understand resource dependencies
5. **Safe Creation**: Use `add_resource(dry_run=True)` to preview, then `dry_run=False` after user confirmation

**Key Technical Concepts:**
- Resources have unique schemas per organization (not standard K8s/AWS formats)
- `properties` field defines available configuration options with types and constraints
- `required` field lists mandatory properties that must be provided
- `x-ui-*` annotations define special behaviors (secret references, output connections)
- Templates show working examples of the organization's specific patterns
- Dependencies between resources are handled through input/output connections
- Safety patterns (dry_run) allow preview before making destructive changes

**Enhanced Schema Validation:**
Resource creation and updates now use strict JSON schema validation against the complete organization
schema from `get_resource_schema_public()`. This ensures configurations match exact organizational
requirements including property types, constraints, required fields, and special annotations.

**Reference Patterns:**
- Variables: `${blueprint.self.variables.my_var}` 
- Secrets: `${blueprint.self.secrets.my_secret}`
- Resource outputs: `${blueprint.resource_name.outputs.connection_string}`

Schema exploration is essential - it reveals the actual property names, types, validation rules,
and patterns the organization has designed for their infrastructure abstractions.
"""

from ..utils.client_utils import ClientUtils
from ..config import mcp
import swagger_client
from swagger_client.models import ResourceFileRequest, UpdateBlueprintRequest
from typing import List, Dict, Any, Optional, Annotated
import json
from ..utils.validation_utils import validate_resource, validate_resource_with_public_schema, get_schema_validation_summary
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INVALID_REQUEST
from pydantic import BaseModel, Field


class ResourceInput(BaseModel):
    """Model for a single resource input connection."""
    resource_name: str = Field(..., description="Name of the resource to connect to")
    resource_type: str = Field(..., description="Type of the resource to connect to")
    output_name: Optional[str] = Field(default=None, description="Output name to use from the connected resource (optional, defaults to 'default')")


class CompatibleResource(BaseModel):
    """Model for a compatible resource that can be used as an input."""
    output_name: str = Field(..., description="Name of the output from this resource")
    resource_name: str = Field(..., description="Name of the compatible resource")
    resource_type: str = Field(..., description="Type of the compatible resource")


class ModuleInputSpec(BaseModel):
    """Model for a module input specification."""
    display_name: str = Field(..., description="Human-readable name for the input")
    description: Optional[str] = Field(default=None, description="Description of what this input is used for")
    optional: bool = Field(..., description="Whether this input is optional or required")
    type: str = Field(..., description="Data type of the input")
    compatible_resources: List[CompatibleResource] = Field(default_factory=list, description="List of resources that can be used for this input")


@mcp.tool()
def get_all_resources_by_project(
    limit: Annotated[int, "Maximum number of resources to return (default: 50)"] = 50,
    offset: Annotated[int, "Number of resources to skip (default: 0)"] = 0,
    search: str = None,
    resource_type: str = None
) -> Dict[str, Any]:
    """
    Get all resources for the current project with pagination and filtering.

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
    """
    api_instance = swagger_client.UiDropdownsControllerApi(ClientUtils.get_client())

    # Get current project
    current_project = ClientUtils.get_current_project()
    if not current_project:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project is set. Please set a project using project_tools.use_project()."
            )
        )
    project_name = current_project.name

    try:
        # Call the API to get all resources for the project
        resources = api_instance.get_all_resources_by_stack(project_name, include_content=True)

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
                    "type": resource.resource_type,  # This is the intent/resource type
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
                message=f"Failed to get resources for project '{project_name}': {error_message}"
            )
        )


@mcp.tool()
def get_resource_by_project(resource_type: str, resource_name: str) -> Dict[str, Any]:
    """
        Get a specific resource by type and name for the current project.

        This returns the current configuration of the resource. The "content" field contains
        the resource's actual configuration that would be validated against the schema from
        get_spec_for_resource() when making updates.

        Args:
            resource_type: The type of resource to retrieve (e.g., service, ingress, postgres, redis)
            resource_name: The name of the specific resource to retrieve

        Returns:
            Resource details including name, type, and current configuration in the "content" field
    """
    api_instance = swagger_client.UiDropdownsControllerApi(ClientUtils.get_client())

    # Get current project
    current_project = ClientUtils.get_current_project()
    if not current_project:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project is set. Please set a project using project_tools.use_project()."
            )
        )
    project_name = current_project.name
    
    try:

        # Call the API directly with resource name, type, and project name
        resource = api_instance.get_resource_by_stack(project_name, resource_type, resource_name)

        # Format the response
        resource_data = {
            "name": resource.resource_name,
            "type": resource.resource_type,
            "directory": resource.directory,
            "filename": resource.filename,
            "content": json.loads(resource.content) if resource.content else None,
            "info": resource.info.to_dict() if resource.info else None  # Add the info object as a separate field
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
            
            # Add suggestion for Invalid Reference Expression errors
            if any(error.category == "Invalid Reference Expression" for error in resource.errors):
                resource_data["suggestion"] = "Use get_resource_output_tree for the resource you're trying to reference."

        return resource_data

    except Exception as e:
        error_message = ClientUtils.extract_error_message(e)
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Failed to get resource '{resource_name}' of type '{resource_type}' for project '{project_name}': {error_message}"
            )
        )


@mcp.tool()
def get_spec_for_resource(resource_type: str, resource_name: str) -> Dict[str, Any]:
    """
        Get specification details for the module mapped to a specific resource in the current project.

        This returns the schema that defines valid fields, allowed values, and validation rules
        ONLY for the "spec" part of the resource JSON. A complete resource JSON has other fields 
        such as kind, metadata, flavor, version, etc., which are not covered by this schema.
        
        To understand the complete resource structure, refer to the sample JSON from 
        get_sample_for_module() which shows all required fields including those outside the "spec" section.
        
        Use this spec before updating resources to understand the available configuration options 
        and requirements for the "spec" section specifically.
        
        Note: If you find fields with annotations starting with "x-ui-" (e.g., x-ui-secret-ref, x-ui-output-type),
        call explain_ui_annotation() with the annotation name to understand how to handle them properly.

        Args:
            resource_type: The type of resource (e.g., service, ingress, postgres, redis)
            resource_name: The name of the specific resource

        Returns:
            A schema specification that describes valid fields and values for the "spec" section of this resource type
    """
    # First, get the resource details to extract intent, flavor, and version
    # Get current project
    current_project = ClientUtils.get_current_project()
    if not current_project:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project is set. Please set a project using project_tools.use_project()."
            )
        )
    project_name = current_project.name
    
    try:

        # Get the specific resource
        resource = get_resource_by_project(resource_type, resource_name)

        # Extract intent (resource_type), flavor, and version from info
        if not resource.get("info"):
            raise McpError(
                ErrorData(
                    code=INVALID_REQUEST,
                    message=f"Resource '{resource_name}' of type '{resource_type}' does not have info data"
                )
            )

        # Get info section
        info = resource["info"]

        # Extract flavor and version
        flavor = info.get("flavour")  # Note: flavour is the field name used in the Info model
        version = info.get("version")

        # Validate required fields
        if not flavor:
            raise McpError(
                ErrorData(
                    code=INVALID_REQUEST,
                    message=f"Resource '{resource_name}' of type '{resource_type}' does not have a flavor defined"
                )
            )
        if not version:
            raise McpError(
                ErrorData(
                    code=INVALID_REQUEST,
                    message=f"Resource '{resource_name}' of type '{resource_type}' does not have a version defined"
                )
            )

        # Now call the TF Module API to get the spec
        api_instance = swagger_client.ModuleManagementApi(ClientUtils.get_client())
        module_response = api_instance.get_module_for_ifv_and_stack(
            flavor=flavor,
            intent=resource_type,
            stack_name=project_name,
            version=version
        )

        # Extract and parse the spec from the response
        if not module_response.spec:
            raise McpError(
                ErrorData(
                    code=INVALID_REQUEST,
                    message=f"No specification found for resource '{resource_name}' of type '{resource_type}'"
                )
            )

        # Return the spec as a JSON object
        return json.loads(module_response.spec)

    except Exception as e:
        error_message = ClientUtils.extract_error_message(e)
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Failed to get specification for resource '{resource_name}' of type '{resource_type}' in project '{project_name}': {error_message}"
            )
        )


@mcp.tool()
def update_resource(resource_type: str, resource_name: str, content: Dict[str, Any], dry_run: bool = True) -> str:
    """
    Update a specific resource in the current project with strict schema validation.
    
    IMPORTANT: This is a potentially irreversible operation that modifies resources.
    Always run with `dry_run=True` first to preview changes before committing them.
    
    **Enhanced Schema Validation:**
    This function now performs comprehensive validation using the organization's complete schema
    from `get_resource_schema_public()` to ensure the updated configuration matches exact requirements
    including all properties, types, constraints, and special annotations.
    
    **Safe Update Workflow:**
    1. **Preview Changes**: Always run with `dry_run=True` first
    2. **Review Diff**: Examine the differences between current and proposed configuration
    3. **User Confirmation**: ASK THE USER EXPLICITLY if they want to proceed
    4. **Apply Changes**: Only if user confirms, run again with `dry_run=False`

    **Schema-Driven Updates:**
    Before updating, it's recommended to:
    - Use `get_resource_by_project()` to see current configuration
    - Use `get_resource_schema_public()` to understand valid properties and constraints
    - Ensure your updates conform to the organization's schema requirements

    Args:
        resource_type: The type of resource to update (e.g., service, ingress, postgres)
        resource_name: The name of the specific resource to update
        content: The updated content for the resource as a dictionary. Must conform
                to the organization's schema with all required fields and valid values.
        dry_run: If True, only preview changes without making them. Default is True.

    Returns:
        Preview of changes with diff (if dry_run=True) or confirmation of update (if dry_run=False)

    Raises:
        McpError: If the resource doesn't exist, validation fails, or update fails
    """
    # Get current project
    current_project = ClientUtils.get_current_project()
    if not current_project:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project is set. Please set a project using project_tools.use_project()."
            )
        )
    project_name = current_project.name
    
    try:

        # First, get the current resource to obtain metadata and current content
        current_resource = get_resource_by_project(resource_type, resource_name)
        current_content = current_resource.get("content", {})
        
        # Create a ResourceFileRequest instance with the updated content
        resource_request = ResourceFileRequest(
            resource_name=resource_name,
            resource_type=resource_type,
            content=content,
            directory=current_resource.get("directory"),
            filename=current_resource.get("filename")
        )

        # Validate the updated content against the organization's complete schema
        # Get resource metadata to determine flavor and version for schema validation
        current_resource_content = current_resource.get("content", {})
        flavor = current_resource_content.get("flavor")
        version = current_resource_content.get("version")
        
        if flavor and version:
            try:
                # Get the complete schema from the public API 
                schema_response = get_resource_schema_public(resource_type, flavor, version)
                
                # Perform strict JSON schema validation using the organization's schema
                validate_resource_with_public_schema(content, schema_response)
                
            except Exception as schema_error:
                # Provide helpful error message with schema context
                error_message = str(schema_error)
                
                # Try to get schema summary for debugging context
                try:
                    schema_response = get_resource_schema_public(resource_type, flavor, version)
                    schema_summary = get_schema_validation_summary(schema_response)
                    error_message += f"\n\nSchema Requirements:\n{schema_summary}"
                except:
                    pass  # Schema summary is helpful but not critical
                
                raise McpError(
                    ErrorData(
                        code=INVALID_REQUEST,
                        message=f"Resource update validation failed: {error_message}"
                    )
                )
        else:
            # Fallback to basic validation if flavor/version cannot be determined
            resource_data = {
                "name": resource_name,
                "type": resource_type,
                "content": content
            }
            try:
                resource_spec_schema = get_spec_for_resource(resource_type, resource_name)
            except:
                resource_spec_schema = {}
            
            validate_resource(resource_data, resource_spec_schema)

        # Get project branch
        api_stack = swagger_client.UiStackControllerApi(ClientUtils.get_client())
        stack = api_stack.get_stack(project_name)
        branch = stack.branch if hasattr(stack, 'branch') and stack.branch else None
        
        # If dry_run is True, show a preview of changes rather than applying them
        if dry_run:
            import json
            import difflib
            
            # Format the current and new content for comparison
            current_json = json.dumps(current_content, indent=2).splitlines()
            new_json = json.dumps(content, indent=2).splitlines()
            
            # Generate a diff between current and new content
            diff = difflib.unified_diff(
                current_json, 
                new_json,
                fromfile=f"{resource_type}/{resource_name} (current)",
                tofile=f"{resource_type}/{resource_name} (proposed)",
                lineterm='',
                n=3  # Context lines
            )
            
            # Format the diff for readability
            formatted_diff = '\n'.join(list(diff))
            
            # Create a structured response for the dry run
            result = {
                "type": "dry_run",
                "resource_type": resource_type,
                "resource_name": resource_name,
                "diff": formatted_diff,
                "instructions": "Review the proposed changes above. ➕ Added lines, ➖ Removed lines, and unchanged lines for context. ASK THE USER EXPLICITLY if they want to proceed with these changes. Only if the user confirms, run the update_resource function again with dry_run=False."
            }
            
            return json.dumps(result, indent=2)
        else:
            # Create an API instance and update the resource
            api_instance = swagger_client.UiBlueprintDesignerControllerApi(ClientUtils.get_client())
            update_request = UpdateBlueprintRequest(files=[resource_request])
            api_instance.update_resources(update_request, project_name, branch)
            
            # Check for errors after the update
            dropdown_api = swagger_client.UiDropdownsControllerApi(ClientUtils.get_client())
            resource_response = dropdown_api.get_resource_by_stack(project_name, resource_type, resource_name)
            
            update_result = {
                "message": f"Successfully updated resource '{resource_name}' of type '{resource_type}'."
            }
            
            # Add errors if any
            if hasattr(resource_response, 'errors') and resource_response.errors:
                errors = []
                for error in resource_response.errors:
                    error_info = {
                        "message": error.message,
                        "category": error.category,
                        "severity": error.severity if hasattr(error, 'severity') else None
                    }
                    errors.append(error_info)
                
                update_result["errors"] = errors
                update_result["warning"] = "Resource was updated but has validation errors that need to be fixed."
                
                # If it's an Invalid Reference Expression, suggest checking outputs
                if any(error.category == "Invalid Reference Expression" for error in resource_response.errors):
                    update_result["suggestion"] = "Please call get_resource_output_tree for the resource you are trying to refer to."
            
            import json
            return json.dumps(update_result, indent=2)
    except Exception as e:
        error_message = ClientUtils.extract_error_message(e)
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Failed to update resource '{resource_name}' of type '{resource_type}' in project '{project_name}': {error_message}"
            )
        )


@mcp.tool()
def get_module_inputs(resource_type: str, flavor: str) -> Dict[str, ModuleInputSpec]:
    """
    Get required inputs for a module before adding a resource.
    
    IMPORTANT: This tool MUST be called before attempting to add a resource using add_resource().
    It checks what inputs are required for a specific module and what existing resources are compatible
    with each input.
    
    Each module input will be a ModuleInputSpec object with:
    - optional: Boolean indicating if this input is required
    - compatible_resources: List of CompatibleResource objects that can be used for this input
    
    If there are multiple compatible resources for a required input, DO NOT select one automatically.
    Instead, you MUST ASK THE USER to choose which resource they want to use for each input.
    Present them with the options and get their explicit selection.
    
    For each non-optional input, you must select a compatible resource and include it in the 
    'inputs' parameter of add_resource(). If an input is not optional and has no compatible
    resources, the resource cannot be added until those dependencies are created.
    
    Example workflow:
    1. Call get_module_inputs('service', 'default')
    2. If it returns an input 'database' that is not optional and has multiple compatible resources:
       - Present the options to the user: "I see you need to select a database input. Available options are: X, Y, Z. Which would you like to use?"
       - Use their selection when calling add_resource()
    
    Args:
        resource_type: The type of resource to create (e.g., service, ingress, postgres) - this is the same as 'intent'
        flavor: The flavor of the resource to create
        
    Returns:
        A dictionary of input names to ModuleInputSpec objects, including compatible resources
    """
    # Get current project
    current_project = ClientUtils.get_current_project()
    if not current_project:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project is set. Please set a project using project_tools.use_project()."
            )
        )
    project_name = current_project.name
    
    try:

        # Create an API instance
        api_instance = swagger_client.UiBlueprintDesignerControllerApi(ClientUtils.get_client())

        # Call the API to get module inputs
        module_inputs = api_instance.get_module_inputs(project_name, resource_type, flavor)

        # Format the response using Pydantic models
        result = {}
        for input_name, input_data in module_inputs.items():
            # Extract compatible resources as Pydantic objects
            compatible_resources = []
            if input_data.compatible_resources:
                for resource in input_data.compatible_resources:
                    compatible_resources.append(CompatibleResource(
                        output_name=resource.output_name,
                        resource_name=resource.resource_name,
                        resource_type=resource.resource_type
                    ))

            # Create ModuleInputSpec object
            result[input_name] = ModuleInputSpec(
                display_name=input_data.display_name,
                description=input_data.description,
                optional=input_data.optional,
                type=input_data.type,
                compatible_resources=compatible_resources
            )

        return result

    except Exception as e:
        error_message = ClientUtils.extract_error_message(e)
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Failed to get module inputs for resource type '{resource_type}' with flavor '{flavor}' in project '{project_name}': {error_message}"
            )
        )


@mcp.tool()
def add_resource(resource_type: str, resource_name: str, flavor: str, version: str,
                 content: Dict[str, Any] = None, inputs: Dict[str, ResourceInput] = None,
                 dry_run: bool = True) -> str:
    """
    Add a new resource to the current project.

    IMPORTANT: This is a potentially irreversible operation that creates new resources.
    Always run with `dry_run=True` first to preview the resource before creating it.
    
    Steps for safe resource creation:
    1. Always run with `dry_run=True` first to preview the resource configuration.
    2. Review the proposed resource configuration.
    3. ASK THE USER EXPLICITLY if they want to proceed with creating this resource.
    4. Only if user confirms, run again with `dry_run=False` to create the resource.

    This function creates a new resource in the current project. It uses strict JSON schema validation
    against the organization's complete schema to ensure proper configuration.
    
    **Schema Validation Enhancement:**
    This function now performs comprehensive validation using `get_resource_schema_public()` to ensure
    the resource configuration matches the organization's exact schema requirements including all
    properties, types, constraints, and special annotations.
    
    **Essential Prerequisites:**
    1. **Schema Understanding**: Use `get_resource_schema_public()` to understand the organization's schema
    2. **Input Dependencies**: Call `get_module_inputs()` to check required resource connections
    3. **Template Structure**: Use `get_sample_for_module()` to see proper configuration structure
    
    **Complete Resource Creation Workflow:**
    1. **Discover Resources**: `list_available_resources()` to see available types and flavors
    2. **Understand Schema**: `get_resource_schema_public(intent, flavor, version)` to learn actual property requirements
    3. **Check Dependencies**: `get_module_inputs(intent, flavor)` to identify required connections
       - For each required input with multiple compatible resources, ASK THE USER which one to use
       - Present options clearly: "For the 'database' input, I see these compatible resources: X, Y, Z. Which would you like to use?"
       - If required input has no compatible resources, the resource CANNOT be created until dependencies are added
       - The function will raise an error listing which dependencies need to be created first
    4. **Get Template**: `get_sample_for_module(intent, flavor, version)` to see working example structure
    5. **Customize Configuration**: Modify template based on schema requirements and user needs
    6. **Create Resource**: Call `add_resource()` with proper content and input connections
    
    **Schema-Driven Configuration:**
    The validation now checks against the complete organization schema, so ensure your content includes:
    - All required fields identified in the schema
    - Proper data types and formats as defined by the organization
    - Valid enum values where constrained
    - Correct nested object structures for complex properties

    Example inputs parameter:
    {
        "database": ResourceInput(
            resource_name="my-postgres",
            resource_type="postgres",
            output_name="postgres_connection"
        )
    }

    Args:
        resource_type: The type of resource to create (e.g., service, ingress, postgres, redis) - this is the same as 'intent'
        resource_name: The name for the new resource
        flavor: The flavor of the resource - must be one of the flavors available for the chosen resource_type
        version: The version of the resource - must match the version from list_available_resources
        content: The content/configuration for the resource as a dictionary. This must conform
                to the schema for the specified resource type and flavor.
        inputs: A dictionary mapping input names to ResourceInput objects containing
               resource_name, resource_type, and optional output_name.
        dry_run: If True, only preview the resource without creating it. Default is True.

    Returns:
        Preview of resource (if dry_run=True) or confirmation of creation (if dry_run=False)

    Raises:
        ValueError: If the resource already exists, creation fails, or required parameters are missing
    """
    # Get current project
    current_project = ClientUtils.get_current_project()
    if not current_project:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project is set. Please set a project using project_tools.use_project()."
            )
        )
    project_name = current_project.name
    
    try:

        # If flavor is not provided, prompt the user
        if not flavor:
            raise McpError(
                ErrorData(
                    code=INVALID_REQUEST,
                    message=f"Flavor must be specified for creating a new resource of type '{resource_type}'. "
                             "Please provide a flavor parameter."
                )
            )

        # If version is not provided, prompt the user
        if not version:
            raise McpError(
                ErrorData(
                    code=INVALID_REQUEST,
                    message=f"Version must be specified for creating a new resource of type '{resource_type}'. "
                             "Please provide a version parameter."
                )
            )

        # Check if content is provided
        if not content:
            raise McpError(
                ErrorData(
                    code=INVALID_REQUEST,
                    message=f"Content must be specified for creating a new resource of type '{resource_type}'. "
                             "First use get_sample_for_module() to get a template, then customize it."
                )
            )

        # Always validate inputs - get module requirements first
        module_inputs = get_module_inputs(resource_type, flavor)

        # Check for required inputs without any compatible resources
        required_without_compatible = [
            input_name for input_name, input_spec in module_inputs.items()
            if not input_spec.optional and not input_spec.compatible_resources
        ]

        # If there are required inputs without compatible resources, block creation
        if required_without_compatible:
            missing_deps_list = []
            for input_name in required_without_compatible:
                input_spec = module_inputs[input_name]
                missing_deps_list.append(f"'{input_name}' ({input_spec.display_name})")

            missing_deps = ", ".join(missing_deps_list)
            raise McpError(
                ErrorData(
                    code=INVALID_REQUEST,
                    message=f"Cannot create resource '{resource_type}' because the following required inputs have no compatible resources available: {missing_deps}. "
                            f"You need to create the required dependency resources first. "
                            f"Use list_available_resources() to see what resources you can create."
                )
            )

        # Get required inputs that have compatible resources available
        required_inputs = [input_name for input_name, input_spec in module_inputs.items()
                          if not input_spec.optional and input_spec.compatible_resources]

        # Check if inputs is None but required inputs exist
        if inputs is None:
            if required_inputs:
                input_list = ", ".join(required_inputs)
                raise McpError(
                    ErrorData(
                        code=INVALID_REQUEST,
                        message=f"Inputs must be specified for creating a resource of type '{resource_type}'. "
                                 f"The following inputs are required: {input_list}. "
                                 f"Call get_module_inputs('{resource_type}', '{flavor}') "
                                 f"to see all required inputs and their compatible resources."
                    )
                )
        else:
            # Validate provided inputs
            provided_inputs = set(inputs.keys()) if inputs else set()
            required_input_set = set(required_inputs)

            # Check for missing required inputs
            missing_inputs = required_input_set - provided_inputs
            if missing_inputs:
                missing_list = ", ".join(sorted(missing_inputs))
                raise McpError(
                    ErrorData(
                        code=INVALID_REQUEST,
                        message=f"Missing required inputs for resource type '{resource_type}': {missing_list}. "
                                 f"Call get_module_inputs('{resource_type}', '{flavor}') "
                                 f"to see all required inputs and their compatible resources."
                    )
                )

            # Check for invalid input names (inputs not defined in module)
            valid_input_names = set(module_inputs.keys())
            invalid_inputs = provided_inputs - valid_input_names
            if invalid_inputs:
                invalid_list = ", ".join(sorted(invalid_inputs))
                valid_list = ", ".join(sorted(valid_input_names))
                raise McpError(
                    ErrorData(
                        code=INVALID_REQUEST,
                        message=f"Invalid input names for resource type '{resource_type}': {invalid_list}. "
                                 f"Valid input names are: {valid_list}."
                    )
                )

            # Validate compatibility of provided resources
            for input_name, input_value in inputs.items():
                input_spec = module_inputs[input_name]
                compatible_resources = input_spec.compatible_resources

                # Find if the provided resource is compatible
                is_compatible = False
                for compatible_resource in compatible_resources:
                    if (compatible_resource.resource_name == input_value.resource_name and
                        compatible_resource.resource_type == input_value.resource_type):
                        # Check if output_name matches (if specified)
                        if input_value.output_name is None or input_value.output_name == compatible_resource.output_name:
                            is_compatible = True
                            break

                if not is_compatible:
                    compatible_list = []
                    for cr in compatible_resources:
                        compatible_list.append(f"{cr.resource_type}/{cr.resource_name} (output: {cr.output_name})")
                    compatible_str = ", ".join(compatible_list) if compatible_list else "none available"

                    raise McpError(
                        ErrorData(
                            code=INVALID_REQUEST,
                            message=f"Resource '{input_value.resource_type}/{input_value.resource_name}' "
                                     f"(output: {input_value.output_name or 'default'}) is not compatible with input '{input_name}'. "
                                     f"Compatible resources are: {compatible_str}."
                        )
                    )

        # If inputs are provided, add them to the content dictionary
        if inputs:
            # Create a copy of the content to avoid modifying the original
            if content is None:
                content = {}
            else:
                content = dict(content)  # Create a shallow copy

            # Add inputs to the content dictionary
            formatted_inputs = {}
            for input_name, input_value in inputs.items():
                # Create input entry without output_name first
                input_entry = {
                    "resource_name": input_value.resource_name,
                    "resource_type": input_value.resource_type
                }

                # Only add output_name if it's provided and not 'default'
                if input_value.output_name is not None and input_value.output_name != 'default':
                    input_entry["output_name"] = input_value.output_name

                formatted_inputs[input_name] = input_entry

            # Add the inputs to the content dictionary
            content["inputs"] = formatted_inputs

        # Create a ResourceFileRequest instance with the resource details (after inputs are processed)
        resource_request = ResourceFileRequest(
            resource_name=resource_name,
            resource_type=resource_type,
            content=content,
            flavor=flavor
        )

        # Directory and filename will be determined by the server

        # Validate the resource content against the organization's complete schema
        try:
            # Get the complete schema from the public API 
            schema_response = get_resource_schema_public(resource_type, flavor, version)
            
            # Perform strict JSON schema validation using the organization's schema
            validate_resource_with_public_schema(content, schema_response)
            
        except Exception as schema_error:
            # Provide helpful error message with schema context
            error_message = str(schema_error)
            
            # Try to get schema summary for debugging context
            try:
                schema_response = get_resource_schema_public(resource_type, flavor, version)
                schema_summary = get_schema_validation_summary(schema_response)
                error_message += f"\n\nSchema Requirements:\n{schema_summary}"
            except:
                pass  # Schema summary is helpful but not critical
            
            raise McpError(
                ErrorData(
                    code=INVALID_REQUEST,
                    message=f"Resource configuration validation failed: {error_message}"
                )
            )

        # Get project branch
        api_stack = swagger_client.UiStackControllerApi(ClientUtils.get_client())
        stack = api_stack.get_stack(project_name)
        branch = stack.branch if hasattr(stack, 'branch') and stack.branch else None
        
        # If dry_run is True, show a preview of the resource rather than creating it
        if dry_run:
            import json
            
            # Format the content for preview
            formatted_content = json.dumps(content, indent=2) if content else "No content provided"
            
            # Display information about inputs if they exist
            inputs_info = ""
            if inputs:
                inputs_info = "\nConnections to other resources:\n"
                for input_name, input_data in inputs.items():
                    input_resource = f"{input_data.resource_type}/{input_data.resource_name}"
                    output_name = input_data.output_name or 'default'
                    inputs_info += f"  - {input_name}: Connected to {input_resource} (output: {output_name})\n"
            
            # Create a structured response for the dry run
            result = {
                "type": "dry_run",
                "resource_type": resource_type,
                "resource_name": resource_name,
                "flavor": flavor,
                "version": version,
                "content_preview": formatted_content,
                "inputs_preview": inputs_info,
                "instructions": "THIS IS A IRREVERSIBLE CRITICAL OPERATION, CONFIRM WITH USER if they want to proceed with creating this resource OR ANY CHANGES ARE NEEDED. Only if the user confirms, run the add_resource function again with dry_run=False."
            }
            
            return json.dumps(result, indent=2)
        else:
            # Create an API instance and create the resource
            api_instance = swagger_client.UiBlueprintDesignerControllerApi(ClientUtils.get_client())
            api_instance.create_resources([resource_request], project_name, branch)
            
            # Check for errors after the addition
            dropdown_api = swagger_client.UiDropdownsControllerApi(ClientUtils.get_client())
            resource_response = dropdown_api.get_resource_by_stack(project_name, resource_type, resource_name)
            
            add_result = {
                "message": f"Successfully created resource '{resource_name}' of type '{resource_type}'."
            }
            
            # Add errors if any
            if hasattr(resource_response, 'errors') and resource_response.errors:
                errors = []
                for error in resource_response.errors:
                    error_info = {
                        "message": error.message,
                        "category": error.category,
                        "severity": error.severity if hasattr(error, 'severity') else None
                    }
                    errors.append(error_info)
                
                add_result["errors"] = errors
                add_result["warning"] = "Resource was added but has validation errors that need to be fixed."
                
                # If it's an Invalid Reference Expression, suggest checking outputs
                if any(error.category == "Invalid Reference Expression" for error in resource_response.errors):
                    add_result["suggestion"] = "Please call get_resource_output_tree for the resource you are trying to refer to."
            
            import json
            return json.dumps(add_result, indent=2)

    except Exception as e:
        error_message = ClientUtils.extract_error_message(e)
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Failed to add resource '{resource_name}' of type '{resource_type}' to project '{project_name}': {error_message}"
            )
        )


@mcp.tool()
def delete_resource(resource_type: str, resource_name: str, dry_run: bool = True) -> str:
    """
    Delete a specific resource from the current project.

    IMPORTANT: This is an irreversible operation that permanently removes a resource.
    Always run with `dry_run=True` first to confirm which resource will be deleted.
    
    Steps for safe resource deletion:
    1. Always run with `dry_run=True` first to confirm the resource details.
    2. Review the resource that will be deleted, including any potential dependencies.
    3. ASK THE USER EXPLICITLY if they want to proceed with deleting this resource.
    4. Only if user explicitly confirms, run again with `dry_run=False` to delete the resource.
    
    Args:
        resource_type: The type of resource to delete (e.g., service, ingress, postgres)
        resource_name: The name of the specific resource to delete
        dry_run: If True, only preview the deletion without actually deleting. Default is True.

    Returns:
        Preview of deletion (if dry_run=True) or confirmation of deletion (if dry_run=False)

    Raises:
        ValueError: If the resource doesn't exist or deletion fails
    """
    # Get current project
    current_project = ClientUtils.get_current_project()
    if not current_project:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project is set. Please set a project using project_tools.use_project()."
            )
        )
    project_name = current_project.name
    
    try:

        # First, get the current resource to obtain metadata
        current_resource = get_resource_by_project(resource_type, resource_name)

        resource_request = ResourceFileRequest(
            resource_name=resource_name,
            resource_type=resource_type,
            directory=current_resource.get("directory"),
            filename=current_resource.get("filename")
        )

        # Get project branch
        api_stack = swagger_client.UiStackControllerApi(ClientUtils.get_client())
        stack = api_stack.get_stack(project_name)
        branch = stack.branch if hasattr(stack, 'branch') and stack.branch else None
        
        # If dry_run is True, show a preview of the deletion rather than deleting
        if dry_run:
            import json
            
            # Get more details about the resource for confirmation
            content_preview = json.dumps(current_resource.get("content", {}), indent=2)[:500]  # Truncate for readability
            if len(content_preview) >= 500:
                content_preview += "\n...\n(content truncated for preview)"
                
            # Warn about potential dependencies
            dependencies_warning = ("\nWARNING: Deleting this resource may affect other resources that depend on it. "
                                  "Please check for dependencies before confirming deletion.")
            
            # Create a structured response for the dry run
            result = {
                "type": "dry_run",
                "resource_type": resource_type,
                "resource_name": resource_name,
                "directory": current_resource.get("directory"),
                "filename": current_resource.get("filename"),
                "content_preview": content_preview,
                "warning": dependencies_warning,
                "instructions": "This will PERMANENTLY DELETE the resource shown above. ASK THE USER EXPLICITLY if they want to proceed with deleting this resource. Only if the user EXPLICITLY confirms, run the delete_resource function again with dry_run=False."
            }
            
            return json.dumps(result, indent=2)
        else:
            # Create an API instance and delete the resource
            api_instance = swagger_client.UiBlueprintDesignerControllerApi(ClientUtils.get_client())
            api_instance.delete_resources([resource_request], project_name, branch)
            
            return f"Successfully deleted resource '{resource_name}' of type '{resource_type}'."

    except Exception as e:
        error_message = ClientUtils.extract_error_message(e)
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Failed to delete resource '{resource_name}' of type '{resource_type}' from project '{project_name}': {error_message}"
            )
        )


@mcp.tool()
def get_spec_for_module(intent: str, flavor: str, version: str) -> Dict[str, Any]:
    """
    Get specification details for a module based on intent, flavor, and version.
    
    This returns the schema that defines valid fields, allowed values, and validation rules
    ONLY for the "spec" part of the resource JSON. A complete resource JSON has other fields 
    such as kind, metadata, flavor, version, etc., which are not covered by this schema.
    
    These other fields can be understood from the sample returned by get_sample_for_module(),
    which shows all required fields including those outside the "spec" section.
    
    Use this spec before creating or updating resources to understand the available 
    configuration options and requirements for the "spec" section specifically.
        
    Note: If you find fields with annotations starting with "x-ui-" (e.g., x-ui-secret-ref, x-ui-output-type),
    call explain_ui_annotation() with the annotation name to understand how to handle them properly.
    
    Args:
        intent: The intent/resource type (e.g., service, ingress, postgres, redis)
        flavor: The flavor of the resource
        version: The version of the resource
        
    Returns:
        A schema specification that describes valid fields and values for the "spec" section of this resource type
    """
    # Get current project
    current_project = ClientUtils.get_current_project()
    if not current_project:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project is set. Please set a project using project_tools.use_project()."
            )
        )
    project_name = current_project.name
    
    try:

        # Call the TF Module API to get the spec
        api_instance = swagger_client.ModuleManagementApi(ClientUtils.get_client())
        module_response = api_instance.get_module_for_ifv_and_stack(
            flavor=flavor,
            intent=intent,
            stack_name=project_name,
            version=version
        )

        # Extract and parse the spec from the response
        if not module_response.spec:
            raise McpError(
                ErrorData(
                    code=INVALID_REQUEST,
                    message=f"No specification found for module with intent '{intent}', flavor '{flavor}', version '{version}'"
                )
            )

        # Return the spec as a JSON object
        return json.loads(module_response.spec)

    except Exception as e:
        error_message = ClientUtils.extract_error_message(e)
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Failed to get specification for module with intent '{intent}', flavor '{flavor}', version '{version}' in project '{project_name}': {error_message}"
            )
        )


@mcp.tool()
def get_sample_for_module(intent: str, flavor: str, version: str) -> Dict[str, Any]:
    """
    Get a complete sample configuration template for a resource type.
    
    **Template Purpose:**
    Provides a working example of how the organization's schema is applied in practice.
    This shows the complete resource structure with organization-specific property names,
    proper nesting, and example values that demonstrate expected formats and patterns.
    
    **Template Structure Analysis:**
    - **Top-level**: Contains `kind`, `flavor`, `version`, and `spec` fields (not standard K8s structure)
    - **spec section**: Main configuration using the organization's schema properties
    - **Reference patterns**: Shows how to connect to variables, secrets, and other resources
    - **Nested objects**: Demonstrates proper structure for complex configurations
    - **Example values**: Illustrates expected data types and formats
    
    **Key Template Elements:**
    - Organization-specific property names (not standard cloud provider names)
    - Proper reference syntax for variables: `${blueprint.self.variables.name}`
    - Proper reference syntax for secrets: `${blueprint.self.secrets.name}`
    - Proper reference syntax for resource outputs: `${blueprint.resource_name.outputs.field}`
    - Nested configuration objects with specific structure requirements
    - Enum values and constraints specific to the organization
    
    **Customization Approach:**
    1. Preserve the overall structure (kind, flavor, version, spec)
    2. Keep organization-specific property names exactly as shown
    3. Replace example values with user-specific values
    4. Maintain reference patterns and nested object structures
    5. Follow data type requirements shown in the examples
    
    **Prerequisites:**
    - Current project must be set (use `use_project()` first)
    - Recommended: Review schema with `get_resource_schema_public()` first
    
    Args:
        intent: Resource type (e.g., "postgres", "service", "redis")  
        flavor: Implementation variant (e.g., "rds", "cloudsql", "k8s")
        version: Module version (e.g., "0.2", "1.0")
        
    Returns:
        Complete sample configuration with:
        - Full resource structure using organization's patterns
        - Example values that can be replaced with user values
        - Proper reference formats for variables, secrets, outputs
        - Correct nesting and data types per organization schema
        
    **Usage Flow:** Schema exploration → Template examination → Value customization → Resource creation
    """
    # Get current project
    current_project = ClientUtils.get_current_project()
    if not current_project:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project is set. Please set a project using project_tools.use_project()."
            )
        )
    project_name = current_project.name
    
    try:

        # Call the TF Module API to get the module
        api_instance = swagger_client.ModuleManagementApi(ClientUtils.get_client())
        module_response = api_instance.get_module_for_ifv_and_stack(
            flavor=flavor,
            intent=intent,
            stack_name=project_name,
            version=version
        )

        # Extract and parse the sample JSON from the response
        if not module_response.sample_json:
            raise McpError(
                ErrorData(
                    code=INVALID_REQUEST,
                    message=f"No sample JSON found for module with intent '{intent}', flavor '{flavor}', version '{version}'"
                )
            )

        # Return the sample JSON as a JSON object
        return json.loads(module_response.sample_json)

    except Exception as e:
        error_message = ClientUtils.extract_error_message(e)
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Failed to get sample JSON for module with intent '{intent}', flavor '{flavor}', version '{version}' in project '{project_name}': {error_message}"
            )
        )


@mcp.tool()
def get_output_references(output_type: str) -> List[Dict[str, Any]]:
    """
    Get a list of available output references from resources in the current project based on the output type.
    
    This tool is used in conjunction with the x-ui-output-type annotation to allow users to select
    outputs from existing resources to reference in their resource configuration.
    
    Args:
        output_type: The type of output to search for (e.g., "iam_policy_arn", "database_connection_string")
        
    Returns:
        A list of output references with resource details and output information
    """
    # Get current project
    current_project = ClientUtils.get_current_project()
    if not current_project:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project is set. Please set a project using project_tools.use_project()."
            )
        )
    project_name = current_project.name
    
    try:

        api_instance = swagger_client.UiDropdownsControllerApi(ClientUtils.get_client())

        # Call the API to get output references
        references = api_instance.get_output_references(project_name, output_type)

        # Format the response to make it easier to present to users
        formatted_references = []
        for ref in references:
            formatted_ref = {
                "resource_type": ref.resource_type,
                "resource_name": ref.resource_name,
                "output_name": ref.output_name,
                "output_title": ref.output_title,
                # Create a fully formatted reference string
                "reference": f"${{{ref.resource_type}.{ref.resource_name}.out.{ref.output_name}}}"
            }
            formatted_references.append(formatted_ref)

        return formatted_references

    except Exception as e:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Failed to get output references for project '{project_name}' and output type '{output_type}': {str(e)}"
            )
        )


@mcp.tool()
def explain_ui_annotation(annotation_name: str) -> str:
    """
    Get explanation and handling instructions for UI annotations in resource specifications.
    
    In the specification of modules, fields may contain special UI annotations that start with "x-ui-". 
    These annotations provide additional instructions on how to handle and process these fields.
    You should use this information when generating or modifying resource specifications.
    
    Args:
        annotation_name: The name of the UI annotation to explain (e.g., "x-ui-secret-ref")
        
    Returns:
        Detailed explanation of the annotation and instructions for handling fields with this annotation
    """
    # Dictionary of known UI annotations with their explanations and handling instructions
    ui_annotations = {
        "x-ui-secret-ref": {
            "description": "Indicates that the field value should be treated as sensitive and stored as a secret.",
            "handling": """
When a field has 'x-ui-secret-ref' set to true:

1. DO NOT insert the actual value directly in the resource JSON
2. Instead, use the reference format: "${blueprint.self.secrets.<name_of_secret>}" 
3. Ask the user if a secret has already been created for this field
4. If no existing secret, ask if they want to create one with an appropriate name
5. To create a new secret, call the 'create_variables' tool with appropriate parameters

Example:
If a database password field has 'x-ui-secret-ref: true', instead of:
  "password": "actual-password-here"
Use:
  "password": "${blueprint.self.secrets.db_password}"
"""
        },
        "x-ui-output-type": {
            "description": "Indicates that the field can reference output from another resource in the project.",
            "handling": """
When a field has 'x-ui-output-type' set to a value (e.g., "iam_policy_arn", "database_connection_string"):

1. Call the 'get_output_references' tool with the project name and the output type value
2. Ask the user to choose one of the outputs from the list of available references
3. Do not select an output automatically unless there is only one option or it is clearly implied by the context
4. Use the 'reference' value directly from the tool output in the field
5. If the field also has 'x-ui-typeable: true', the user can either select an output reference or provide their own custom value

Example:
If an 'apiUrl' field has 'x-ui-output-type: "iam_policy_arn"', after calling get_output_references:
- Present the options: "For the API URL, I can reference outputs from other resources. Available options are: [list options]"
- After user selects: "Using reference to API Gateway URL"
- Set the value using the 'reference' field from the selected output
"""
        },
        # Add more annotations here as they are discovered/implemented
    }

    # Check if the annotation exists in our dictionary
    if annotation_name in ui_annotations:
        annotation = ui_annotations[annotation_name]

        # Format the response
        response = f"# {annotation_name}\n\n"
        response += f"**Description:** {annotation['description']}\n\n"
        response += f"**Handling Instructions:**\n{annotation['handling']}"

        return response

    # For unknown annotations, provide a generic response
    return f"""
# {annotation_name}

Unknown UI annotation. You can ignore this annotation and proceed normally.
"""


@mcp.tool()
def get_resource_output_tree(resource_type: str) -> Dict[str, Any]:
    """
    Get the output tree for a specific resource type in the current project.
    
    This tool returns a hierarchical tree of all output fields available for the specified resource type.
    The output tree is used for referencing data from one resource in another resource using the
    format ${resourceType.resourceName.out.x.y}, where x.y is the path in the output tree.
    
    For example, to reference a database connection string from a postgres resource named 'my-db',
    you would use: ${postgres.my-db.out.connection_string}
    
    Args:
        resource_type: The type of resource to get outputs for (e.g., service, ingress, postgres, redis)
        
    Returns:
        A hierarchical tree of available output properties for the specified resource type
    """
    # Get current project
    current_project = ClientUtils.get_current_project()
    if not current_project:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project is set. Please set a project using project_tools.use_project()."
            )
        )
    project_name = current_project.name
    
    try:

        # Create an API instance
        api_instance = swagger_client.UiBlueprintDesignerControllerApi(ClientUtils.get_client())

        # Call the API to get autocomplete data
        autocomplete_data = api_instance.get_autocomplete_data(project_name)

        # Check if outProperties exists and contains data for the specified resource type
        if not autocomplete_data.out_properties:
            raise McpError(
                ErrorData(
                    code=INVALID_REQUEST,
                    message=f"No output properties found for project '{project_name}'"
                )
            )

        # Get the output tree for the specified resource type
        output_tree = autocomplete_data.out_properties.get(resource_type)
        if not output_tree:
            raise McpError(
                ErrorData(
                    code=INVALID_REQUEST,
                    message=f"No output properties found for resource type '{resource_type}' in project '{project_name}'"
                )
            )

        # Convert to dictionary for easier consumption
        if hasattr(output_tree, 'to_dict'):
            output_tree = output_tree.to_dict()

        # Return the output tree
        return {
            "resource_type": resource_type,
            "output_tree": output_tree,
            "reference_format": f"${{resourceType.resourceName.out.x.y}} where resourceType='{resource_type}' and out.x.y is the path to the desired output"
        }

    except Exception as e:
        error_message = ClientUtils.extract_error_message(e)
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Failed to get output tree for resource type '{resource_type}' in project '{project_name}': {error_message}"
            )
        )


def _extract_attribute_paths(obj: Any, current_path: str) -> List[str]:
    """
    Recursively extract all valid attribute paths from a nested object structure.

    This helper function traverses the output tree structure returned by the autocomplete API
    and generates all possible dot-notation paths that can be used in dollar references.

    Args:
        obj: The object to traverse (dict, list, or primitive value)
        current_path: The current path prefix (e.g., "postgres.my-db.out")

    Returns:
        List of complete paths (e.g., ["postgres.my-db.out.host", "postgres.my-db.out.port"])

    Examples:
        >>> tree = {"host": "localhost", "config": {"port": 5432}}
        >>> _extract_attribute_paths(tree, "postgres.db.out")
        ["postgres.db.out.host", "postgres.db.out.config", "postgres.db.out.config.port"]
    """
    paths = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            new_path = f"{current_path}.{key}"
            # Always add the current level path
            paths.append(new_path)

            # If value is nested (dict or list), recursively traverse it
            if isinstance(value, (dict, list)):
                paths.extend(_extract_attribute_paths(value, new_path))

    elif isinstance(obj, list):
        # For lists, traverse each element with array index notation
        for idx, item in enumerate(obj):
            new_path = f"{current_path}[{idx}]"
            paths.append(new_path)

            if isinstance(item, (dict, list)):
                paths.extend(_extract_attribute_paths(item, new_path))

    return paths


@mcp.tool()
def get_resource_outputs(
    resource_type: Optional[str] = None,
    resource_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get all available output references from resources in the current project.

    This tool returns actual dollar reference expressions (${...}) that can be used in resource
    configurations to reference outputs from existing resources. Unlike get_resource_output_tree()
    which shows schema structure, this returns actual instances with complete reference paths ready to use.

    Requires a current project to be set using use_project() first.

    Use this tool when you need to discover what outputs are available, resolve "has no attribute" errors,
    or find valid reference expressions for connecting resources.

    For example, to get all postgres database outputs: get_resource_outputs(resource_type="postgres")
    Or for a specific resource: get_resource_outputs(resource_type="service", resource_name="api")

    Returns references in format: ${postgres.my-db.out.connection_string}

    Args:
        resource_type: Optional - Filter to specific resource type (e.g., "postgres", "mongo", "service", "redis")
        resource_name: Optional - Filter to specific resource name (e.g., "my-database", "api-service")

    Returns:
        Dict containing all_dollar_references (sorted list), total_references count, and filters_applied
    """
    # Check if current project is set
    current_project = ClientUtils.get_current_project()
    if not current_project:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project is set. Please set a project using use_project() first."
            )
        )

    project_name = current_project.name

    try:
        # Create API instance
        api_instance = swagger_client.UiBlueprintDesignerControllerApi(ClientUtils.get_client())

        # Call the autocomplete v2 API which returns module-specific output trees
        response = api_instance.get_autocomplete_data_v2(stack_name=project_name)

        # Convert response to dict if needed
        if hasattr(response, "to_dict"):
            response_dict = response.to_dict()
        else:
            response_dict = response

        # Get resource output trees from the response
        # Structure: {resource_type: {resource_name: output_tree}}
        resource_trees = response_dict.get("resource_output_trees", {})

        # Extract dollar reference paths with optional filtering
        all_references = []
        for res_type, resources in resource_trees.items():
            # Filter by resource_type if provided
            if resource_type and res_type != resource_type:
                continue

            if isinstance(resources, dict):
                for res_name, outputs in resources.items():
                    # Filter by resource_name if provided
                    if resource_name and res_name != resource_name:
                        continue

                    # Extract all attribute paths from this resource's output tree
                    # Starting path format: resource_type.resource_name.out
                    paths = _extract_attribute_paths(outputs, f"{res_type}.{res_name}.out")

                    # Wrap each path in ${...} to create dollar references
                    for path in paths:
                        all_references.append(f"${{{path}}}")

        # Build filter information for response
        filters_applied = {}
        if resource_type:
            filters_applied["resource_type"] = resource_type
        if resource_name:
            filters_applied["resource_name"] = resource_name

        # Return structured result
        result = {
            "status": "success",
            "project_name": project_name,
            "all_dollar_references": sorted(all_references),
            "total_references": len(all_references),
            "filters_applied": filters_applied if filters_applied else None
        }

        return result

    except Exception as e:
        error_message = ClientUtils.extract_error_message(e)
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Failed to get resource output references for project '{project_name}': {error_message}"
            )
        )


@mcp.tool()
def list_available_resources() -> List[Dict[str, Any]]:
    """
    Discover all infrastructure resource types that can be added to the current project.

    **Purpose & Context:**
    This is the **ESSENTIAL FIRST STEP** in the resource creation workflow. Resources are
    infrastructure components like databases, services, load balancers, etc. Each resource
    type comes in different "flavors" (e.g., postgres can be RDS, CloudSQL, or K8s-based).
    
    **Prerequisites:**
    - Current project must be set (use `use_project()` first)
    
    **Usage Patterns:**
    - **Resource Discovery**: "What can I deploy in this project?"
    - **Planning Infrastructure**: Understanding available components before architecting
    - **Exploring Options**: Seeing all flavors available for a resource type
    - **Getting Started**: First step when building new infrastructure
    
    **Data Structure:**
    Each resource entry contains:
    - `resource_type`: The intent/type (e.g., 'postgres', 'service', 'redis')
    - `flavor`: Specific implementation (e.g., 'rds', 'cloudsql', 'k8s')
    - `version`: Module version to use
    - `description`: What this resource does
    - `display_name`: Human-friendly name
    
    **LLM-Friendly Tags:** [FOUNDATIONAL] [DISCOVERY] [READ-ONLY] [WORKFLOW-START]

    Returns:
        List[Dict[str, Any]]: Complete catalog of available resources with metadata
        
    **Complete Resource Creation Workflow:**
    1. `list_available_resources()` ← **You are here** (Discover options)
    2. `get_module_inputs(type, flavor)` - Check dependencies
    3. `get_spec_for_module(type, flavor, version)` - Understand schema
    4. `get_sample_for_module(type, flavor, version)` - Get template  
    5. `add_resource()` - Create with customized content
    
    **Common Next Steps:**
    - Choose a resource type and flavor from the results
    - Call `get_module_inputs()` to understand what connections are needed
    - Use `get_resource_schema_public()` to explore properties without project context
    
    **Pro Tips for LLMs:**
    - Group resources by type to help users understand options
    - Recommend flavors based on user's cloud provider or preferences
    - Explain the difference between similar resources (e.g., RDS vs Aurora)
    
    **See Also:**
    - `get_module_inputs()` - Check resource dependencies 
    - `get_sample_for_module()` - Get configuration templates
    - `get_resource_schema_public()` - Explore resource properties
    - `add_resource()` - Create resources after planning
    """
    # Get current project
    current_project = ClientUtils.get_current_project()
    if not current_project:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project is set. Please set a project using project_tools.use_project()."
            )
        )
    project_name = current_project.name

    try:
        # Create an API instance
        api_instance = swagger_client.ModuleManagementApi(ClientUtils.get_client())

        # Get grouped modules for the specified project
        response = api_instance.get_grouped_modules_for_stack(project_name)

        # Process the response to extract resource information
        result = []

        # The resources property is a nested dictionary structure
        # The first level key is not relevant (usually 'resources')
        # The second level key is the intent (resource type)
        if response.resources:
            for _, resource_types in response.resources.items():
                for resource_type, resource_info in resource_types.items():
                    # Each resource type (intent) has a list of modules
                    if resource_info and resource_info.modules:
                        for module in resource_info.modules:
                            resource_data = {
                                "resource_type": resource_type,  # This is the intent
                                "flavor": module.flavor,
                                "version": module.version,
                                "description": resource_info.description or "",
                                "display_name": resource_info.display_name or resource_type,
                            }
                            result.append(resource_data)

        return result

    except Exception as e:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Failed to list available resources for project '{project_name}': {str(e)}"
            )
        )


@mcp.tool()
def get_resource_schema_public(intent: str, flavor: str, version: str) -> Dict[str, Any]:
    """
    Get the complete schema definition for any Facets resource type.
    
    **Critical Schema Context:** 
    Facets resources use organization-specific abstractions rather than standard Kubernetes or AWS formats.
    Each resource type has a unique schema with custom property names, validation rules, and special annotations.
    Never assume standard property names - the organization may use "database_endpoint" instead of "host",
    or "backup_retention_days" instead of "BackupRetentionPeriod".
    
    **Essential Schema Elements:**
    - `properties`: All available configuration fields with their data types, constraints, and descriptions
    - `required`: Fields that must be provided in the resource configuration (cannot be omitted)
    - `x-ui-secret-ref`: Properties that require secret reference format like `${blueprint.self.secrets.db_password}`
    - `x-ui-output-type`: Properties that can reference outputs from other resources
    - `enum` constraints: Valid values for fields with restricted options
    - `type` definitions: string, integer, boolean, object, array with specific validation rules
    
    **Schema Analysis Approach:**
    1. Examine `properties` object to understand all available fields and their data types
    2. Check `required` array to identify mandatory fields for the resource
    3. Look for `x-ui-*` annotations that define special Facets behaviors
    4. Note enum constraints and validation patterns specific to the organization
    5. Understand nested object structures for complex configurations
    
    **Key Schema Patterns:**
    - Properties may have nested objects requiring specific structure
    - Some fields accept template expressions for dynamic values
    - Special annotations indicate integration points (secrets, outputs, variables)
    - Organization-defined enums replace cloud provider specific values
    
    Args:
        intent: Resource type (e.g., "postgres", "service", "redis")
        flavor: Implementation variant (e.g., "rds", "cloudsql", "k8s")
        version: Module version (e.g., "0.2", "1.0")
        
    Returns:
        Dict containing complete schema structure:
        - `properties`: Field definitions with types, constraints, annotations
        - `required`: List of mandatory field names  
        - `additional_properties`: Whether custom fields are allowed
        - `type`: Schema type (typically "object")
        - `schema`: JSON Schema URL reference
        
    **Usage Context:** Use this before any resource configuration to understand the organization's
    specific abstractions and avoid assumptions based on standard infrastructure formats.
    
    **Workflow Integration:** Schema exploration → Template examination → Configuration building
    """
    try:
        # Create an API instance for public APIs
        api_instance = swagger_client.PublicApIsApi(ClientUtils.get_client())
        
        # Call the public API to get module schema
        schema_response = api_instance.get_module_schema(
            intent=intent,
            flavor=flavor,
            version=version
        )
        
        # Convert the response to a dictionary for easier consumption
        result = {
            "intent": intent,
            "flavor": flavor,
            "version": version,
            "type": schema_response.type,
            "required": schema_response.required or [],
            "properties": schema_response.properties or {},
            "additional_properties": schema_response.additional_properties,
            "schema": schema_response.schema
        }
        
        return result
        
    except Exception as e:
        error_message = ClientUtils.extract_error_message(e)
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Failed to get schema for resource with intent '{intent}', flavor '{flavor}', version '{version}': {error_message}"
            )
        )
