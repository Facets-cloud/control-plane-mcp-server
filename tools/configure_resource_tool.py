from utils.client_utils import ClientUtils
import swagger_client
from swagger_client.models import ResourceFileRequest
from typing import List, Dict, Any, Tuple, Optional
import json
from tools import project_tools

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
            # Check if resource should be excluded
            should_exclude = False

            # Safely check if resource.info.ui.base_resource exists and is True
            try:
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
                    "filename": resource.filename
                }
                result.append(resource_data)

        return result

    except Exception as e:
        raise ValueError(f"Failed to get resources for project '{project_name}': {str(e)}")


@mcp.tool()
def get_resource_by_project(project_name: str, resource_type: str, resource_name: str) -> Dict[str, Any]:
    """
        Get a specific resource by type and name for a project.

        This returns the current configuration of the resource. The "content" field contains
        the resource's actual configuration that would be validated against the schema from
        get_spec_for_resource() when making updates.

        Args:
            project_name: The name of the project to retrieve the resource from
            resource_type: The type of resource to retrieve (e.g., service, ingress, postgres, redis)
            resource_name: The name of the specific resource to retrieve

        Returns:
            Resource details including name, type, and current configuration in the "content" field
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
        raise ValueError(
            f"Failed to get resource '{resource_name}' of type '{resource_type}' for project '{project_name}': {str(e)}")


@mcp.tool()
def get_spec_for_resource(project_name: str, resource_type: str, resource_name: str) -> Dict[str, Any]:
    """
        Get specification details for a specific resource in a project.

        This returns the schema that defines valid fields, allowed values, and validation rules
        ONLY for the "spec" part of the resource JSON. A complete resource JSON has other fields 
        such as kind, metadata, flavor, version, etc., which are not covered by this schema.
        
        To understand the complete resource structure, refer to the sample JSON from 
        get_sample_for_module() which shows all required fields including those outside the "spec" section.
        
        Use this spec before updating resources to understand the available configuration options 
        and requirements for the "spec" section specifically.

        Args:
            project_name: The name of the project the resource belongs to
            resource_type: The type of resource (e.g., service, ingress, postgres, redis)
            resource_name: The name of the specific resource

        Returns:
            A schema specification that describes valid fields and values for the "spec" section of this resource type
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
        raise ValueError(
            f"Failed to get specification for resource '{resource_name}' of type '{resource_type}' in project '{project_name}': {str(e)}")


@mcp.tool()
def update_resource(project_name: str, resource_type: str, resource_name: str, content: Dict[str, Any]) -> None:
    """
    Update a specific resource in a project.

    Before using this tool, it's recommended to first call get_spec_for_resource() to
    understand the valid fields and values for this resource type. The content provided
    must conform to the specification schema for the update to succeed.

    Args:
        project_name: The name of the project containing the resource
        resource_type: The type of resource to update (e.g., service, ingress, postgres)
        resource_name: The name of the specific resource to update
        content: The updated content for the resource as a dictionary. This must conform
                to the schema returned by get_spec_for_resource().

    Raises:
        ValueError: If the resource doesn't exist, update fails, or content doesn't match the required schema
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

        # Get project branch
        api_stack = swagger_client.UiStackControllerApi(ClientUtils.get_client())
        stack = api_stack.get_stack_using_get(project_name)
        branch = stack.branch if hasattr(stack, 'branch') and stack.branch else None

        # Create an API instance and update the resource
        api_instance = swagger_client.UiBlueprintDesignerControllerApi(ClientUtils.get_client())
        result = api_instance.update_resources_using_put(branch, [resource_request], project_name)

        return result

    except Exception as e:
        raise ValueError(
            f"Failed to update resource '{resource_name}' of type '{resource_type}' in project '{project_name}': {str(e)}")


@mcp.tool()
def add_resource(project_name: str, resource_type: str, resource_name: str, flavor: str = None, version: str = None,
                 content: Dict[str, Any] = None) -> None:
    """
    Add a new resource to a project.

    This function creates a new resource in the specified project. Follow these steps for resource creation:
    
    Step-by-step resource creation flow:
    1. Call list_available_resources(project_name) to see available resources
    2. From the results, select a resource_type/intent (e.g., 'service', 'postgres') and note the flavor and version
    3. Call get_spec_for_module(project_name, resource_type, flavor, version) to understand the schema
    4. Call get_sample_for_module(project_name, resource_type, flavor, version) to get a sample template
    5. Customize the template from step 4 according to user requirements
    6. Call add_resource() with all the parameters including the customized content

    Args:
        project_name: The name of the project to add the resource to
        resource_type: The type of resource to create (e.g., service, ingress, postgres, redis) - this is the same as 'intent'
        resource_name: The name for the new resource
        flavor: The flavor of the resource - must be one of the flavors available for the chosen resource_type
        version: The version of the resource - must match the version from list_available_resources
        content: The content/configuration for the resource as a dictionary. This must conform
                to the schema for the specified resource type and flavor.

    Raises:
        ValueError: If the resource already exists, creation fails, or required parameters are missing
    """
    try:
        # If flavor is not provided, prompt the user
        if not flavor:
            raise ValueError(f"Flavor must be specified for creating a new resource of type '{resource_type}'. "
                             "Please provide a flavor parameter.")

        # If version is not provided, prompt the user
        if not version:
            raise ValueError(f"Version must be specified for creating a new resource of type '{resource_type}'. "
                             "Please provide a version parameter.")

        # Check if content is provided
        if not content:
            raise ValueError(f"Content must be specified for creating a new resource of type '{resource_type}'. "
                             "First use get_sample_for_module() to get a template, then customize it.")

        # Create a ResourceFileRequest instance with the resource details
        resource_request = ResourceFileRequest()
        resource_request.content = content
        resource_request.resource_name = resource_name
        resource_request.resource_type = resource_type
        resource_request.flavor = flavor
        resource_request.version = version
        # Directory and filename will be determined by the server

        # Get project branch
        api_stack = swagger_client.UiStackControllerApi(ClientUtils.get_client())
        stack = api_stack.get_stack_using_get(project_name)
        branch = stack.branch if hasattr(stack, 'branch') and stack.branch else None

        # Create an API instance and create the resource
        api_instance = swagger_client.UiBlueprintDesignerControllerApi(ClientUtils.get_client())
        result = api_instance.create_resources_using_post(branch, [resource_request], project_name)

        return result

    except Exception as e:
        raise ValueError(
            f"Failed to add resource '{resource_name}' of type '{resource_type}' to project '{project_name}': {str(e)}")


@mcp.tool()
def delete_resource(project_name: str, resource_type: str, resource_name: str) -> None:
    """
    Delete a specific resource from a project.

    This function permanently removes a resource from the specified project.
    
    Args:
        project_name: The name of the project containing the resource
        resource_type: The type of resource to delete (e.g., service, ingress, postgres)
        resource_name: The name of the specific resource to delete

    Raises:
        ValueError: If the resource doesn't exist or deletion fails
    """
    try:
        # First, check if the resource exists
        try:
            get_resource_by_project(project_name, resource_type, resource_name)
        except ValueError:
            raise ValueError(
                f"Resource '{resource_name}' of type '{resource_type}' not found in project '{project_name}'")

        # Create a ResourceFileRequest instance for the resource to delete
        resource_request = ResourceFileRequest()
        resource_request.resource_name = resource_name
        resource_request.resource_type = resource_type

        # Get project branch
        api_stack = swagger_client.UiStackControllerApi(ClientUtils.get_client())
        stack = api_stack.get_stack_using_get(project_name)
        branch = stack.branch if hasattr(stack, 'branch') and stack.branch else None

        # Create an API instance and delete the resource
        api_instance = swagger_client.UiBlueprintDesignerControllerApi(ClientUtils.get_client())
        result = api_instance.delete_resources_using_delete(branch, [resource_request], project_name)

        return result

    except Exception as e:
        raise ValueError(
            f"Failed to delete resource '{resource_name}' of type '{resource_type}' from project '{project_name}': {str(e)}")


@mcp.tool()
def get_spec_for_module(project_name: str, intent: str, flavor: str, version: str) -> Dict[str, Any]:
    """
    Get specification details for a module based on intent, flavor, and version.
    
    This returns the schema that defines valid fields, allowed values, and validation rules
    ONLY for the "spec" part of the resource JSON. A complete resource JSON has other fields 
    such as kind, metadata, flavor, version, etc., which are not covered by this schema.
    
    These other fields can be understood from the sample returned by get_sample_for_module(),
    which shows all required fields including those outside the "spec" section.
    
    Use this spec before creating or updating resources to understand the available 
    configuration options and requirements for the "spec" section specifically.
    
    Args:
        project_name: The name of the project to get the module specification for
        intent: The intent/resource type (e.g., service, ingress, postgres, redis)
        flavor: The flavor of the resource
        version: The version of the resource
        
    Returns:
        A schema specification that describes valid fields and values for the "spec" section of this resource type
    """
    try:
        # Call the TF Module API to get the spec
        api_instance = swagger_client.UiTfModuleControllerApi(ClientUtils.get_client())
        module_response = api_instance.get_module_for_ifv_and_stack_using_get(
            flavor=flavor,
            intent=intent,
            stack_name=project_name,
            version=version
        )

        # Extract and parse the spec from the response
        if not module_response.spec:
            raise ValueError(
                f"No specification found for module with intent '{intent}', flavor '{flavor}', version '{version}'")

        # Return the spec as a JSON object
        return json.loads(module_response.spec)

    except Exception as e:
        raise ValueError(
            f"Failed to get specification for module with intent '{intent}', flavor '{flavor}', version '{version}' in project '{project_name}': {str(e)}")


@mcp.tool()
def get_sample_for_module(project_name: str, intent: str, flavor: str, version: str) -> Dict[str, Any]:
    """
    Get a sample JSON template for creating a new resource of a specific type.
    
    This returns a complete sample configuration that can be used as a starting point when creating
    a new resource. The sample includes ALL required fields such as kind, metadata,
    flavor, version, as well as the "spec" section. This provides a complete resource structure
    with typical values to demonstrate the expected format.
    
    Unlike get_spec_for_module() which only covers the "spec" section schema, this returns
    a complete resource template with all necessary fields populated with sample values.
    
    Args:
        project_name: The name of the project to get the sample for
        intent: The intent/resource type (e.g., service, ingress, postgres, redis)
        flavor: The flavor of the resource
        version: The version of the resource
        
    Returns:
        A complete sample JSON configuration that can be used as a template for creating a new resource
    """
    try:
        # Call the TF Module API to get the module
        api_instance = swagger_client.UiTfModuleControllerApi(ClientUtils.get_client())
        module_response = api_instance.get_module_for_ifv_and_stack_using_get(
            flavor=flavor,
            intent=intent,
            stack_name=project_name,
            version=version
        )

        # Extract and parse the sample JSON from the response
        if not module_response.sample_json:
            raise ValueError(
                f"No sample JSON found for module with intent '{intent}', flavor '{flavor}', version '{version}'")

        # Return the sample JSON as a JSON object
        return json.loads(module_response.sample_json)

    except Exception as e:
        raise ValueError(
            f"Failed to get sample JSON for module with intent '{intent}', flavor '{flavor}', version '{version}' in project '{project_name}': {str(e)}")


@mcp.tool()
def list_available_resources(project_name: str) -> List[Dict[str, Any]]:
    """
    List all available resources that can be added to a project.

    This is the first step in the resource creation workflow. This function returns all
    resource types (also called 'intents') and their available flavors that can be added
    to the specified project.

    When adding a new resource with add_resource(), you'll need to select:
    1. A resource_type/intent (e.g., 'service', 'ingress', 'postgres', 'redis')
    2. A specific flavor for that resource_type

    The response contains both these required parameters, so review the results carefully
    before proceeding to add_resource().

    Args:
        project_name: The name of the project to list available resources for

    Returns:
        A list of dictionaries with resource_type (same as intent), flavor, version,
        description, and display_name for each available resource
    """
    try:
        # Create an API instance
        api_instance = swagger_client.UiTfModuleControllerApi(ClientUtils.get_client())

        # Get grouped modules for the specified project
        response = api_instance.get_grouped_modules_for_stack_using_get(project_name)

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
        raise ValueError(f"Failed to list available resources for project '{project_name}': {str(e)}")
