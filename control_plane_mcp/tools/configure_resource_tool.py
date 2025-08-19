from ..utils.client_utils import ClientUtils
import swagger_client
from swagger_client.models import ResourceFileRequest
from typing import List, Dict, Any
import json
from ..utils.validation_utils import validate_resource
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INVALID_REQUEST

mcp = ClientUtils.get_mcp_instance()


@mcp.tool()
def get_all_resources_by_project() -> List[Dict[str, Any]]:
    """
    Get all resources for the current project.
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
        result = []
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
                result.append(resource_data)
        return result
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
    Update a specific resource in the current project.
    
    IMPORTANT: This is a potentially irreversible operation that modifies resources.
    Always run with `dry_run=True` first to preview changes before committing them.
    
    Steps for safe resource updates:
    1. Always run with `dry_run=True` first to preview changes.
    2. Review the differences between current and proposed configuration.
    3. ASK THE USER EXPLICITLY if they want to proceed with these changes.
    4. Only if user confirms, run again with `dry_run=False` to commit changes.

    Before using this tool, it's recommended to first call get_spec_for_resource() to
    understand the valid fields and values for this resource type. The content provided
    must conform to the specification schema for the update to succeed.

    Args:
        resource_type: The type of resource to update (e.g., service, ingress, postgres)
        resource_name: The name of the specific resource to update
        content: The updated content for the resource as a dictionary. This must conform
                to the schema returned by get_spec_for_resource().
        dry_run: If True, only preview changes without making them. Default is True.

    Returns:
        Preview of changes (if dry_run=True) or confirmation of update (if dry_run=False)

    Raises:
        ValueError: If the resource doesn't exist, update fails, or content doesn't match the required schema
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

        # validate the resource content with spec schema
        resource_data = {
            "name": resource_name,
            "type": resource_type,
            "content": content
        }

        # get the spec schema for the resource. if no spec exists, set as empty dict {}
        try:
            resource_spec_schema = get_spec_for_resource(resource_type, resource_name)
        except:
            resource_spec_schema = {}
        
        # validate the resource data configuration with the spec schema. validation error will be automatically raised if validation fails
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
            api_instance.update_resources([resource_request], project_name, branch)
            
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
def get_module_inputs(resource_type: str, flavor: str) -> Dict[str, Dict[str, Any]]:
    """
    Get required inputs for a module before adding a resource.
    
    IMPORTANT: This tool MUST be called before attempting to add a resource using add_resource().
    It checks what inputs are required for a specific module and what existing resources are compatible
    with each input.
    
    Each module input will have:
    - 'optional': Boolean indicating if this input is required
    - 'compatible_resources': List of resources that can be used for this input
    
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
        A dictionary of input names to their details, including compatible resources
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

        # Format the response for easier consumption
        result = {}
        for input_name, input_data in module_inputs.items():
            # Extract compatible resources
            compatible_resources = []
            if input_data.compatible_resources:
                for resource in input_data.compatible_resources:
                    compatible_resources.append({
                        "output_name": resource.output_name,
                        "resource_name": resource.resource_name,
                        "resource_type": resource.resource_type
                    })

            # Format input data
            result[input_name] = {
                "display_name": input_data.display_name,
                "description": input_data.description,
                "optional": input_data.optional,
                "type": input_data.type,
                "compatible_resources": compatible_resources
            }

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
                 content: Dict[str, Any] = None, inputs: Dict[str, Dict[str, str]] = None,
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

    This function creates a new resource in the current project. It's critical to follow the
    complete resource creation workflow to ensure all required inputs are provided.
    
    IMPORTANT: Before calling this tool, you MUST call get_module_inputs() to check what inputs
    are required for the resource you want to create. If there are non-optional inputs with compatible
    resources, you must ASK THE USER to select one for each input and provide them in the 'inputs' parameter.
    Never select resources for inputs automatically, unless there is just one - always ask the user for their preference.
    
    Step-by-step resource creation flow:
    1. Call list_available_resources() to see available resources
    2. From the results, select a resource_type/intent (e.g., 'service', 'postgres') and note the flavor and version
    3. Call get_module_inputs(resource_type, flavor) to check required inputs and compatible resources
       - For each required input with multiple compatible resources, ASK THE USER which one to use
       - Present the options clearly: "For the 'database' input, I see these compatible resources: X, Y, Z. Which would you like to use?"
       - If a required input has no compatible resources, you must create those dependencies first
    4. Call get_spec_for_module(resource_type, flavor, version) to understand the schema
    5. Call get_sample_for_module(resource_type, flavor, version) to get a sample template
    6. Customize the template from step 5 according to user requirements
    7. Call add_resource() with all the parameters including:
       - The customized content
       - A map of inputs where each key is an input name and each value is a dict with:
         * resource_name: The name of the selected resource
         * resource_type: The type of the selected resource
         * output_name: The output name of the selected resource

    Example inputs parameter:
    {
        "database": {
            "resource_name": "my-postgres",
            "resource_type": "postgres",
            "output_name": "postgres_connection"
        }
    }

    Args:
        resource_type: The type of resource to create (e.g., service, ingress, postgres, redis) - this is the same as 'intent'
        resource_name: The name for the new resource
        flavor: The flavor of the resource - must be one of the flavors available for the chosen resource_type
        version: The version of the resource - must match the version from list_available_resources
        content: The content/configuration for the resource as a dictionary. This must conform
                to the schema for the specified resource type and flavor.
        inputs: A dictionary mapping input names to selected resources. Each value should be a dictionary with
               'resource_name', 'resource_type', and 'output_name' keys.
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

        # Check if inputs should be validated
        if inputs is None:
            # Get the module inputs to check if there are any required inputs
            module_inputs = get_module_inputs(resource_type, flavor)
            required_inputs = [input_name for input_name, input_data in module_inputs.items()
                               if not input_data.get("optional", False) and input_data.get("compatible_resources")]

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

        # Create a ResourceFileRequest instance with the resource details
        resource_request = ResourceFileRequest(
            resource_name=resource_name,
            resource_type=resource_type,
            content=content,
            flavor=flavor
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
                    "resource_name": input_value.get('resource_name'),
                    "resource_type": input_value.get('resource_type')
                }

                # Only add output_name if it's not 'default'
                output_name = input_value.get('output_name')
                if output_name and output_name != 'default':
                    input_entry["output_name"] = output_name

                formatted_inputs[input_name] = input_entry

            # Add the inputs to the content dictionary
            content["inputs"] = formatted_inputs

        # Directory and filename will be determined by the server

        # validate the resource content with spec schema
        resource_data = {
            "name": resource_name,
            "type": resource_type,
            "content": content
        }

        # get the spec schema for the module. if no spec exists, set as empty dict {}
        try:
            resource_spec_schema = get_spec_for_module(resource_type, flavor, version)
        except:
            resource_spec_schema = {}
        
        # validate the resource data configuration with the spec schema. validation error will be automatically raised if validation fails
        validate_resource(resource_data, resource_spec_schema)

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
                    input_resource = f"{input_data.get('resource_type')}/{input_data.get('resource_name')}"
                    output_name = input_data.get('output_name', 'default')
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
            api_instance.delete_resources([resource_request], branch,  project_name)
            
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
    
    Returns the full module metadata for the selected module (intent/flavor/version), not just the spec.
    The response includes fields like id, intent, flavor, version, display_name, description,
    spec (JSON schema, parsed to object if it is a JSON string), sample_json (parsed if JSON),
    and other metadata provided by the control-plane API.
    
    Previously this tool returned only the "spec" schema. It now returns the complete payload.
    If you only need the schema, extract response["spec"].
        
    Note: If you find fields with annotations starting with "x-ui-" (e.g., x-ui-secret-ref, x-ui-output-type),
    call explain_ui_annotation() with the annotation name to understand how to handle them properly.
    
    Args:
        intent: The intent/resource type (e.g., service, ingress, postgres, redis)
        flavor: The flavor of the resource
        version: The version of the resource
        
    Returns:
        Full module metadata as a dictionary (including 'spec' and other fields). Extract response["spec"] if schema-only is needed.
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

        # Build and return full module metadata (not just spec)
        # Ensure at least spec exists
        if not getattr(module_response, 'spec', None):
            raise McpError(
                ErrorData(
                    code=INVALID_REQUEST,
                    message=f"No specification found for module with intent '{intent}', flavor '{flavor}', version '{version}'"
                )
            )

        # Convert to a dictionary (swagger models provide to_dict)
        full_meta = module_response.to_dict() if hasattr(module_response, 'to_dict') else {}

        # If conversion failed, fall back to returning just spec
        if not full_meta:
            try:
                return {"spec": json.loads(module_response.spec)}
            except Exception:
                return {"spec": module_response.spec}

        # Parse JSON-string fields for convenience
        try:
            if isinstance(full_meta.get('spec'), str):
                full_meta['spec'] = json.loads(full_meta['spec'])
        except Exception:
            pass
        try:
            if isinstance(full_meta.get('sample_json'), str):
                full_meta['sample_json'] = json.loads(full_meta['sample_json'])
        except Exception:
            pass

        return full_meta

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
    Get a sample JSON template for creating a new resource of a specific type.
    
    This returns a complete sample configuration that can be used as a starting point when creating
    a new resource. The sample includes ALL required fields such as kind, metadata,
    flavor, version, as well as the "spec" section. This provides a complete resource structure
    with typical values to demonstrate the expected format.
    
    Unlike get_spec_for_module() which only covers the "spec" section schema, this returns
    a complete resource template with all necessary fields populated with sample values.
    
    Args:
        intent: The intent/resource type (e.g., service, ingress, postgres, redis)
        flavor: The flavor of the resource
        version: The version of the resource
        
    Returns:
        A complete sample JSON configuration that can be used as a template for creating a new resource
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
        references = api_instance.get_output_references(output_type, project_name)

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


@mcp.tool()
def list_available_resources() -> List[Dict[str, Any]]:
    """
    List all available resources that can be added to the current project.

    This is the first step in the resource creation workflow. This function returns all
    resource types (also called 'intents') and their available flavors that can be added
    to the current project.

    When adding a new resource with add_resource(), you'll need to select:
    1. A resource_type/intent (e.g., 'service', 'ingress', 'postgres', 'redis')
    2. A specific flavor for that resource_type

    Complete resource creation workflow:
    1. Call list_available_resources() to find available resource types and flavors
    2. Call get_module_inputs() to check what inputs are required for the chosen resource
    3. Call get_spec_for_module() to understand the configuration schema
    4. Call get_sample_for_module() to get a template
    5. Call add_resource() with the customized content and required inputs

    Returns:
        A list of dictionaries with resource_type (same as intent), flavor, version,
        description, and display_name for each available resource
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
