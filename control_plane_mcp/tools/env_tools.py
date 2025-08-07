from typing import List
import swagger_client
import mcp
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INVALID_REQUEST
from swagger_client.models.abstract_cluster import AbstractCluster
from ..utils.client_utils import ClientUtils
from ..pydantic_generated.abstractclustermodel import AbstractClusterModel

mcp = ClientUtils.get_mcp_instance()

def _convert_swagger_environment_to_pydantic(swagger_environment) -> AbstractClusterModel:
    """
    Helper function to safely convert a swagger AbstractCluster to a Pydantic AbstractClusterModel.
    This handles None values properly to avoid validation errors.
    
    Args:
        swagger_environment: Swagger AbstractCluster instance
        
    Returns:
        AbstractClusterModel: Properly converted Pydantic model
    """
    # Create a dictionary with default values for fields that could be None
    environment_data = {}
    
    # Get all fields from the model
    model_fields = AbstractClusterModel.model_fields
    
    # Process each field
    for field_name, field_info in model_fields.items():
        # Get the swagger attribute name (using the alias if available)
        swagger_field = field_info.alias or field_name
        
        # Get the value from swagger model
        value = getattr(swagger_environment, swagger_field, None)
        
        # Handle None values based on field type
        if value is None:
            # Check annotation type and provide appropriate default
            annotation = field_info.annotation
            
            # For string fields
            if annotation == str:
                environment_data[field_name] = ""
            # For boolean fields
            elif annotation == bool:
                environment_data[field_name] = False
            # For integer fields
            elif annotation == int:
                environment_data[field_name] = 0
            # For float fields
            elif annotation == float:
                environment_data[field_name] = 0.0
            else:
                # For other types, keep as None but it might cause validation issues
                environment_data[field_name] = value
        else:
            environment_data[field_name] = value
    
    return AbstractClusterModel.model_validate(environment_data)

@mcp.tool()
def get_all_environments() -> List[AbstractClusterModel]:
    """
    Get all environments in the current project. 🌐 
    This function retrieves all environments that are available in the currently selected project. 📋 
    It provides a comprehensive list of all environments you can work with. ✨
    
    Inputs:
        None
        
    Returns:
        List[str]: A list of environment names in the current project.
        
    Raises:
        ValueError: If no current project is set.
    """
    project = ClientUtils.get_current_project()
    if not project:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project is set. "
                "Please set a project using project_tools.use_project()."
            )
        )

    # Create an instance of the API class
    api_instance = swagger_client.UiStackControllerApi(ClientUtils.get_client())
    # Call the method on the instance
    environments = api_instance.get_clusters_overview(project.name)
    # Convert swagger models to Pydantic models
    return [_convert_swagger_environment_to_pydantic(env.cluster) for env in environments]

@mcp.tool()
def use_environment(environment_name: str):
    """
    Set the current environment in the utils configuration. 🔧 This allows you to work with a specific environment. 🌐 
    The environment must exist in the current project. 📋

    Args:
        environment_name (str): The name of the environment to set as current.

    Returns:
        str: A message indicating that the environment has been set.
    
    Raises:
        ValueError: If no current project is set or if the environment is not found in the project.

    example:
        use_environment("environment-name")
    """
    project = ClientUtils.get_current_project()
    if not project:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project is set. "
                "Please set a project using project_tools.use_project()."
            )
        )
    
    # Get all environments directly from the API to avoid conversion issues
    api_instance = swagger_client.UiStackControllerApi(ClientUtils.get_client())
    environments = api_instance.get_clusters(project.name)
    
    # Find the environment by name
    found_environment = None
    for env in environments:
        if env.name == environment_name:
            found_environment = env
            break
    
    if not found_environment:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Environment \"{environment_name}\" not found in project \"{project.name}\""
            )
        )
    
    # Set the current environment directly with the swagger model
    ClientUtils.set_current_cluster(found_environment)
    return f"Current environment set to {environment_name}"

@mcp.tool()
def get_current_environment_details() -> AbstractClusterModel:
    """
    Get the current environment details. 🔍 This requires the current project and environment to be set. 🔄
    The function refreshes environment information from the server to ensure data is not stale. ✨

    Returns:
        AbstractClusterModel: The refreshed current environment object with the latest information.
    
    Raises:
        ValueError: If no current project or environment is set.
    """
    if not ClientUtils.is_current_cluster_and_project_set():
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project or environment is set. "
                "Please set a project using project_tools.use_project() and an environment using env_tools.use_environment()."
            )
        )
    
    project = ClientUtils.get_current_project()
    current_environment = ClientUtils.get_current_cluster()
    
    # Create an instance of the API class to get fresh data
    api_instance = swagger_client.UiStackControllerApi(ClientUtils.get_client())
    # Fetch the latest environment details
    environments = api_instance.get_clusters(project.name)

    # get environment metadata to fetch the running state of the environment
    cluster_metadata = api_instance.get_cluster_metadata_by_stack(project.name)

    # Find the current environment in the refreshed list
    refreshed_environment = None
    for env in environments:
        if env.id == current_environment.id:
            refreshed_environment = env
            # Get the environment state from metadata
            for metadata in cluster_metadata:
                if metadata.cluster_id == env.id:
                    refreshed_environment.cluster_state = metadata.cluster_state
                    break
            # Update the current environment in client utils
            ClientUtils.set_current_cluster(refreshed_environment)
            break
    
    if not refreshed_environment:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Environment with ID {current_environment.id} no longer exists in project {project.name}"
            )
        )
    
    return _convert_swagger_environment_to_pydantic(refreshed_environment)
