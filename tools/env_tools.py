from typing import List
import swagger_client
import mcp
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INVALID_REQUEST
from swagger_client.models.list_deployments_wrapper import ListDeploymentsWrapper
from swagger_client.models.deployment_log import DeploymentLog
from swagger_client.models.abstract_cluster import AbstractCluster
from swagger_client.models.deployment_request import DeploymentRequest
from utils.client_utils import ClientUtils
from pydantic_generated.deploymentrequestmodel import DeploymentRequestModel
from pydantic_generated.abstractclustermodel import AbstractClusterModel

mcp = ClientUtils.get_mcp_instance()

def _convert_swagger_cluster_to_pydantic(swagger_cluster) -> AbstractClusterModel:
    """
    Helper function to safely convert a swagger AbstractCluster to a Pydantic AbstractClusterModel.
    This handles None values properly to avoid validation errors.
    
    Args:
        swagger_cluster: Swagger AbstractCluster instance
        
    Returns:
        AbstractClusterModel: Properly converted Pydantic model
    """
    # Create a dictionary with default values for fields that could be None
    cluster_data = {}
    
    # Get all fields from the model
    model_fields = AbstractClusterModel.model_fields
    
    # Process each field
    for field_name, field_info in model_fields.items():
        # Get the swagger attribute name (using the alias if available)
        swagger_field = field_info.alias or field_name
        
        # Get the value from swagger model
        value = getattr(swagger_cluster, swagger_field, None)
        
        # Handle None values based on field type
        if value is None:
            # Check annotation type and provide appropriate default
            annotation = field_info.annotation
            
            # For string fields
            if annotation == str:
                cluster_data[field_name] = ""
            # For boolean fields
            elif annotation == bool:
                cluster_data[field_name] = False
            # For integer fields
            elif annotation == int:
                cluster_data[field_name] = 0
            # For float fields
            elif annotation == float:
                cluster_data[field_name] = 0.0
            else:
                # For other types, keep as None but it might cause validation issues
                cluster_data[field_name] = value
        else:
            cluster_data[field_name] = value
    
    return AbstractClusterModel.model_validate(cluster_data)

def _convert_pydantic_request_to_swagger(pydantic_request: DeploymentRequestModel) -> DeploymentRequest:
    """
    Helper function to safely convert a Pydantic DeploymentRequestModel to a Swagger DeploymentRequest.
    This handles the conversion properly to avoid attribute_map errors.
    
    Args:
        pydantic_request: Pydantic DeploymentRequestModel instance
        
    Returns:
        DeploymentRequest: Properly converted Swagger model
    """
    # Create a new DeploymentRequest instance directly with required fields
    # This ensures fields are set when the object is created
    req = DeploymentRequest()
    
    # Explicitly set fields that must not be None
    req.override_build_steps = []
    req.hotfix_resources = []
    
    # Set the release type
    if hasattr(pydantic_request, 'release_type') and pydantic_request.release_type:
        req.release_type = pydantic_request.release_type
    
    # Set force_release
    if hasattr(pydantic_request, 'force_release') and pydantic_request.force_release is not None:
        req.force_release = pydantic_request.force_release
    
    # Set allow_destroy
    if hasattr(pydantic_request, 'allow_destroy') and pydantic_request.allow_destroy is not None:
        req.allow_destroy = pydantic_request.allow_destroy
    
    # Set with_refresh
    if hasattr(pydantic_request, 'with_refresh') and pydantic_request.with_refresh is not None:
        req.with_refresh = pydantic_request.with_refresh
    
    # Set hotfix_resources if it's provided and not None
    if hasattr(pydantic_request, 'hotfix_resources') and pydantic_request.hotfix_resources is not None:
        req.hotfix_resources = pydantic_request.hotfix_resources
    
    # Set override_build_steps if it's provided and not None
    if hasattr(pydantic_request, 'override_build_steps') and pydantic_request.override_build_steps is not None:
        req.override_build_steps = pydantic_request.override_build_steps
    
    return req

@mcp.tool()
def get_all_clusters() -> List[AbstractClusterModel]:
    """
    Get all clusters in the current project. 🌐 
    This function retrieves all clusters that are available in the currently selected project. 📋 
    It provides a comprehensive list of all environments you can work with. ✨
    
    Inputs:
        None
        
    Returns:
        List[str]: A list of cluster names in the current project.
        
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
    environments = api_instance.get_clusters_using_get1(project.name)
    # Convert swagger models to Pydantic models
    return [_convert_swagger_cluster_to_pydantic(env) for env in environments]

@mcp.tool()
def use_cluster(cluster_name: str):
    """
    Set the current cluster in the utils configuration. 🔧 This allows you to work with a specific cluster environment. 🌐 
    The cluster must exist in the current project. 📋

    Args:
        cluster_name (str): The name of the cluster to set as current.

    Returns:
        str: A message indicating that the cluster has been set.
    
    Raises:
        ValueError: If no current project is set or if the cluster is not found in the project.

    example:
        use_cluster("cluster-name")
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
    
    # Get all clusters directly from the API to avoid conversion issues
    api_instance = swagger_client.UiStackControllerApi(ClientUtils.get_client())
    environments = api_instance.get_clusters_using_get1(project.name)
    
    # Find the cluster by name
    found_cluster = None
    for env in environments:
        if env.name == cluster_name:
            found_cluster = env
            break
    
    if not found_cluster:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Cluster \"{cluster_name}\" not found in project \"{project.name}\""
            )
        )
    
    # Set the current cluster directly with the swagger model
    ClientUtils.set_current_cluster(found_cluster)
    return f"Current cluster set to {cluster_name}"

@mcp.tool()
def get_current_cluster_details() -> AbstractClusterModel:
    """
    Get the current cluster details. 🔍 This requires the current project and cluster to be set. 🔄
    The function refreshes cluster information from the server to ensure data is not stale. ✨

    Returns:
        AbstractClusterModel: The refreshed current cluster object with the latest information.
    
    Raises:
        ValueError: If no current project or cluster is set.
    """
    if not ClientUtils.is_current_cluster_and_project_set():
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project or cluster is set. "
                "Please set a project using project_tools.use_project() and a cluster using env_tools.use_cluster()."
            )
        )
    
    project = ClientUtils.get_current_project()
    current_cluster = ClientUtils.get_current_cluster()
    
    # Create an instance of the API class to get fresh data
    api_instance = swagger_client.UiStackControllerApi(ClientUtils.get_client())
    # Fetch the latest cluster details
    environments = api_instance.get_clusters_using_get1(project.name)

    # get cluster metadata to fetch the running state of the cluster
    cluster_metadata = api_instance.get_cluster_metadata_by_stack_using_get(project.name)

    # Find the current cluster in the refreshed list
    refreshed_cluster = None
    for env in environments:
        if env.id == current_cluster.id:
            refreshed_cluster = env
            # Get the cluster state from metadata
            for metadata in cluster_metadata:
                if metadata.cluster_id == env.id:
                    refreshed_cluster.cluster_state = metadata.cluster_state
                    break
            # Update the current cluster in client utils
            ClientUtils.set_current_cluster(refreshed_cluster)
            break
    
    if not refreshed_cluster:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Cluster with ID {current_cluster.id} no longer exists in project {project.name}"
            )
        )
    
    return _convert_swagger_cluster_to_pydantic(refreshed_cluster)

@mcp.tool()
def get_deployments_of_current_cluster() -> ListDeploymentsWrapper:
    """
    This will return all the deployments for the set current cluster in the set current project. 📊
    This retrieves all deployments for the current cluster. 🚀

    Returns:
        ListDeploymentsWrapper: A list of deployments for the current cluster.
    
    Raises:
        ValueError: If no current project or cluster is set.
    """
    if not ClientUtils.is_current_cluster_and_project_set():
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project or cluster is set. "
                "Please set a project using project_tools.use_project() and a cluster using env_tools.use_cluster()."
            )
        )
    
    api_instance = swagger_client.UiDeploymentControllerApi(ClientUtils.get_client())
    deployments = api_instance.get_deployments_using_get1(ClientUtils.get_current_cluster().id)

    return deployments

@mcp.tool()
def get_deployment_details(deployment_id: str) -> DeploymentLog:
    """
    Get the details of a specific deployment. in the set current cluster. for the set current project. 📊
    This retrieves detailed information about a specific deployment. 🚀

    Returns:
        DeploymentLog: The details of the deployment.
    
    Raises:
        ValueError: If no current project or cluster is set.
    """
    if not ClientUtils.is_current_cluster_and_project_set():
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project or cluster is set. "
                "Please set a project using project_tools.use_project() and a cluster using env_tools.use_cluster()."
            )
        )
    
    api_instance = swagger_client.UiDeploymentControllerApi(ClientUtils.get_client())
    deployment = api_instance.get_deployment_using_get(ClientUtils.get_current_cluster().id, deployment_id)
    return deployment

@mcp.tool()
def get_deployment_logs_of_current_cluster(deployment_id: str) -> List[DeploymentLog]:
    """
    Get the logs for a specific deployment in the set current cluster. for the set current project. 📋
    This retrieves the logs for a specific deployment in the set current cluster. 🚀

    Returns:
        List[DeploymentLog]: A list of deployment logs.
    
    Raises:
        ValueError: If no current project or cluster is set.
    """
    if not ClientUtils.is_current_cluster_and_project_set():
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="No current project or cluster is set. "
                "Please set a project using project_tools.use_project() and a cluster using env_tools.use_cluster()."
            )
        )
    
    api_instance = swagger_client.UiDeploymentControllerApi(ClientUtils.get_client())
    deployment_logs = api_instance.get_deployment_logs_using_get(ClientUtils.get_current_cluster().id, deployment_id)
    return deployment_logs

@mcp.tool()
def get_active_deployments_of_current_cluster() -> List[DeploymentLog]:
    """
    Get the active deployments for the set current cluster. for the set current project. 🚀
    This retrieves all deployments that are currently in the "RUNNING" state. 🟢

    Returns:
        List[DeploymentLog]: A list of active deployments.
    
    Raises:
        ValueError: If no current project or cluster is set.

    """
    # first lets check if the cluster is in running state or not
    cluster = get_current_cluster_details()
    if cluster.cluster_state != "RUNNING":
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Cluster \"{cluster.name}\" is not in running state"
            )
        )

    deployments = get_deployments_of_current_cluster()
    active_deployments = [deployment for deployment in deployments.deployments if deployment.status == "RUNNING"]
    return active_deployments if len(active_deployments) > 0 else []

@mcp.tool()
def get_active_deployment_logs_of_current_cluster() -> List[DeploymentLog]:
    """
    Get the active deployment logs for the set current cluster for the set current project. 📋 
    This retrieves logs from all currently running deployments. 🚀

    Returns:    
        List[DeploymentLog]: A list of active deployment logs.
    
    Raises:
        ValueError: If no current project or cluster is set.
    """
    active_deployments = get_active_deployments_of_current_cluster()
    
    # Check if we have any active deployments
    if not active_deployments:
        return []
        
    active_deployment_logs = [get_deployment_logs_of_current_cluster(deployment.id) for deployment in active_deployments]
    return active_deployment_logs

@mcp.tool()
def get_latest_deployment_of_current_cluster() -> DeploymentLog:
    """
    Get the latest deployment for the set current cluster for the set current project. 📊 
    This retrieves the most recent deployment regardless of its status. ⏱️

    Returns:
        DeploymentLog: The latest deployment.
    
    Raises:
        ValueError: If no current project or cluster is set.
    """
    deployments = get_deployments_of_current_cluster()
    return deployments.deployments[-1]

def create_deployment_of_current_cluster(properties: DeploymentRequestModel) -> str:
    """
    Create a deployment for the set current cluster for the set current project. 🚀 
    This is the core function that handles all deployment types (launch, release, scale up/down, etc). 🛠️

    example:
        create_deployment_of_current_cluster(DeploymentRequestModel(release_type="LAUNCH"))

    JSON example:
        {
            "releaseType": "LAUNCH", 
            "forceRelease": true,
            "allowDestroy": true,
            "withRefresh": true,
        }

    Args:
        properties (DeploymentRequestModel): The properties of the deployment.

    Returns:
        str: The deployment id of the created deployment.
    
    Raises:
        ValueError: If no current project or cluster is set.
    """
    api_instance = swagger_client.UiDeploymentControllerApi(ClientUtils.get_client())
    
    # Create a new DeploymentRequest instance with empty list for required fields
    # Pass required fields directly in the constructor
    swagger_request = DeploymentRequest(override_build_steps=[])
    
    # Set override_build_steps from properties if available
    if hasattr(properties, 'override_build_steps') and properties.override_build_steps is not None:
        swagger_request.override_build_steps = properties.override_build_steps
    
    # Handle hotfix_resources
    if hasattr(properties, 'hotfix_resources') and properties.hotfix_resources is not None:
        swagger_request.hotfix_resources = properties.hotfix_resources
    
    # Basic fields
    swagger_request.release_type = properties.release_type
    swagger_request.force_release = properties.force_release if hasattr(properties, 'force_release') else False
    
    # Optional fields
    if hasattr(properties, 'allow_destroy') and properties.allow_destroy is not None:
        swagger_request.allow_destroy = properties.allow_destroy
    
    if hasattr(properties, 'with_refresh') and properties.with_refresh is not None:
        swagger_request.with_refresh = properties.with_refresh
    
    deployment = api_instance.create_deployment_using_post(ClientUtils.get_current_cluster().id, swagger_request)
    return deployment.id

@mcp.tool()
def launch_environment_of_current_cluster(properties: DeploymentRequestModel) -> str:
    """
    Launch the set current cluster for the set current project. 🚀 
    This will initialize and start up all resources in the cluster. ✨
    This should only be called if the cluster is not already in the "RUNNING" state. 🟢 or "SCALED_DOWN" ⚠️
    Always ask the user to confirm this action before proceeding! ✅
    

    example:
        launch_environment_of_current_cluster(DeploymentRequestModel(release_type="LAUNCH"))

    JSON example:
        {
            "releaseType": "LAUNCH", 
            "forceRelease": true,
            "allowDestroy": true,
            "withRefresh": true,
        }

    Args:
        properties (DeploymentRequestModel): The properties of the deployment.

    Returns:
        str: The deployment id of the created deployment.
    
    Raises:
        ValueError: If no current project or cluster is set.
    """
    if properties.release_type != "LAUNCH":
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="Release type must be LAUNCH"
            )
        )
    
    return create_deployment_of_current_cluster(properties)

@mcp.tool()
def destroy_environment_of_current_cluster(properties: DeploymentRequestModel) -> str:
    """
    Destroy the set current cluster for the set current project. 
    💥 This will permanently remove all resources in the cluster. ⚠️ Use with caution! 🚨
    Always before doing a destroy, make sure the cluster is not in the state "RUNNING" 🟢, and the cluster is not in the state "SCALED_DOWN" ⚠️
    And this is an irreversible action, so always ask the user to confirm this action ✅.
    And always ask the user to provide the reason for the destroy. 🔍
    

    example:
        destroy_environment_of_current_cluster(DeploymentRequestModel(release_type="DESTROY"))

    JSON example:
        {
            "releaseType": "DESTROY", 
            "forceRelease": true,
            "allowDestroy": true,
            "withRefresh": true,
        }

    Args:
        properties (DeploymentRequestModel): The properties of the deployment.

    Returns:
        str: The deployment id of the created deployment.
    Raises:
        ValueError: If no current project or cluster is set.
    """
    if properties.release_type != "DESTROY":
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="Release type must be DESTROY"
            )
        )
    properties.force_release = True
    return create_deployment_of_current_cluster(properties)

@mcp.tool()
def create_hotfix_plan_of_current_cluster(properties: DeploymentRequestModel) -> str:
    """
    Create a hotfix plan for the set current cluster. for the set current project. 🔍
    This should only be called if the cluster is in the state "RUNNING" 🟢, and the cluster is not in the state "SCALED_DOWN" ⚠️
    Always before doing a hotfix, make sure you run this tool to run the plan and ask the user to review the plan 🔍 before running the hotfix.
    And this only should be an explicit action, Always ask the user to confirm this action ✅.

    example:
        create_hotfix_plan_of_current_cluster(DeploymentRequestModel(release_type="HOTFIX_PLAN"))   

    JSON example:
        {   
            "releaseType": "HOTFIX_PLAN", 
            "forceRelease": true,
            "allowDestroy": true,
            "withRefresh": true,
            "hotfixResources": [
                {
                    "resourceType": "service",
                    "resourceName": "<name of the service>"
                }
            ]
        }
        
    Args:
        properties (DeploymentRequestModel): The properties of the deployment.

    Returns:
        str: The deployment id of the created deployment.
    Raises:
        ValueError: If no current project or cluster is set.
    """
    if properties.release_type != "HOTFIX_PLAN":
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="Release type must be HOTFIX_PLAN"
            )
        )
    if properties.hotfix_resources is None:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="Hotfix resources must be provided"
            )
        )   
    return create_deployment_of_current_cluster(properties)
@mcp.tool()
def create_hotfix_of_current_cluster(properties: DeploymentRequestModel) -> str:
    """
    Create a hotfix deployment for the set current cluster. for the set current project. 🔧 
    This allows for targeted fixes to specific resources without a full deployment. 🚀 
    Use this when you need to quickly update or fix a particular service. ⚡ 
    Always before doing a hotfix, make sure you run `create_hotfix_plan_of_current_cluster()` tool to run the plan and ask the user to review the plan 🔍 before running the hotfix.
    And this only should be an explicit action, Always ask the user to confirm this action ✅.

    If the user doesn't want to run the plan, override by running this tool with the release type as HOTFIX. 🔄
    Ask the user if they want to override the plan and run the hotfix. 🚦 This is a powerful operation that will update the specific resource! 💪

    example:
        create_hotfix_of_current_cluster(DeploymentRequestModel(release_type="HOTFIX"))

    JSON example:
        {
            "releaseType": "HOTFIX", 
            "forceRelease": true,
            "allowDestroy": true,
            "withRefresh": true,
            "hotfixResources": [
                {
                    "resourceType": "service",
                    "resourceName": "<name of the service>"
                }
            ]
        }

    Args:
        properties (DeploymentRequestModel): The properties of the deployment.

    Returns:
        str: The deployment id of the created deployment.
    Raises:
        ValueError: If no current project or cluster is set.
    """
    if properties.release_type != "HOTFIX":
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="Release type must be HOTFIX"
            )
        )
    if properties.hotfix_resources is None:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="Hotfix resources must be provided"
            )
        )
    return create_deployment_of_current_cluster(properties)

@mcp.tool()
def create_full_release_of_current_cluster(properties: DeploymentRequestModel) -> str:
    """
    Create a full release deployment for the set current cluster for the set current project. 🚀 
    This will deploy all resources in the cluster with the latest changes. ✨
    Always before doing a full release, make sure you run `create_full_release_plan_of_current_cluster()` tool to run the plan and ask the user to review the plan 🔍 before running the full release.
    And this only should be an explicit action, Always ask the user to confirm this action ✅.

    If the user doesn't want to run the plan, override by running this tool with the release type as RELEASE. 🔄
    Ask the user if they want to override the plan and run the full release. 🚦 This is a powerful operation that will update all cluster resources! 💪

    example:
        create_full_release_of_current_cluster(DeploymentRequestModel(release_type="RELEASE"))

    JSON example:
        {
            "releaseType": "RELEASE", 
            "forceRelease": true,
            "allowDestroy": true,
            "withRefresh": true,
        }

    Args:
        properties (DeploymentRequestModel): The properties of the deployment.

    Returns:
        str: The deployment id of the created deployment.
    Raises:
        ValueError: If no current project or cluster is set.
    """
    if properties.release_type != "RELEASE":
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="Release type must be RELEASE"
             )
        )
    return create_deployment_of_current_cluster(properties)

@mcp.tool()
def create_full_release_plan_of_current_cluster(properties: DeploymentRequestModel) -> str:
    """
    Create a full release plan for the set current cluster. for the set current project. 📋
    This should only be called if the cluster is in the state "RUNNING" 🟢, and the cluster is not in the state "SCALED_DOWN" ⚠️

    Always before doing a full release, make sure you run this tool to run the plan and ask the user to review the plan 🔍 before running the full release.
    And this only should be an explicit action, Always ask the user to confirm this action ✅.

    example:
        create_full_release_plan_of_current_cluster(DeploymentRequestModel(release_type="FULL_PLAN"))

    JSON example:
        {
            "releaseType": "FULL_PLAN", 
            "forceRelease": true,
            "allowDestroy": true,
            "withRefresh": true,
        }

    Args:
        properties (DeploymentRequestModel): The properties of the deployment.

    Returns:
        str: The deployment id of the created deployment.
    Raises:
        ValueError: If no current project or cluster is set.
    """
    if properties.release_type != "FULL_PLAN":
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="Release type must be FULL_PLAN"
            )
        )
    return create_deployment_of_current_cluster(properties)

@mcp.tool()
def create_custom_release_for_current_cluster(properties: DeploymentRequestModel) -> str:
    """
    Create a custom release for the set current cluster. for the set current project. 🛠️
    This is only required in special cases, where the user wants to do a custom release. ⚠️
    And this only should be an explicit action and only use if this is absolutely necessary, Always ask the user to confirm this action. ✅
    there should not be any malicious addition or removal commands that can harm the cluster. 🚫 Always decline if the user doesnt verify the commands or 
    if the commands are not safe. 🔒
    example:
        create_custom_release_for_current_cluster(DeploymentRequestModel(release_type="CUSTOM"))

    JSON example:
        {
            "releaseType": "CUSTOM", 
            "forceRelease": true,
            "allowDestroy": true,
            "withRefresh": true,
            "overrideBuildSteps": [
                "sleep 10", "print 'Hello, World!'"
            ]
        }

    Args:
        properties (DeploymentRequestModel): The properties of the deployment.

    Returns:
        str: The deployment id of the created deployment.
    Raises:
        ValueError: If no current project or cluster is set.
    """ 
    # check if release type is CUSTOM and override build steps are provided
    if properties.release_type != "CUSTOM" or properties.override_build_steps is None:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="Release type must be CUSTOM and override build steps must be provided"
            )
        )
    return create_deployment_of_current_cluster(properties)

@mcp.tool()
def unlock_state_of_current_cluster(properties: DeploymentRequestModel) -> str:
    """
    Unlock the state of the set current cluster for the set current project. 🔓 This is only required 
    if the cluster terraform state is locked. 🔒 We get to know this in the logs of the deployment that it is locked with a lockId. 📝
    We can then use this tool to unlock the state of the cluster. 🛠️
    And this only should be an explicit action! ⚠️ Always ask the user to confirm this action. ✅
    And always ask the user to provide the lockId. 🔍

    example:
        unlock_state_of_current_cluster(DeploymentRequestModel(release_type="UNLOCK_STATE", lock_id="lockId"))

    JSON example:
        {
            "releaseType": "UNLOCK_STATE", 
            "lockId": "lockId"
        }

    Args:
        properties (DeploymentRequestModel): The properties of the deployment.

    Returns:
        str: The deployment id of the created deployment.
    """
    if properties.release_type != "UNLOCK_STATE" or properties.lock_id is None:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="Release type must be UNLOCK_STATE and lockId must be provided"
            )
        )
    return create_deployment_of_current_cluster(properties)

@mcp.tool()
def scale_up_cluster_of_current_cluster(properties: DeploymentRequestModel) -> str:
    """
    Scale up the set current cluster for the set current project. 🚀
    This should only be called if the cluster is in the state "SCALED_DOWN" ⬇️
    And this only should be an explicit action! ⚠️ Always ask the user to confirm this action. ✅

    example:
        scale_up_cluster_of_current_cluster(DeploymentRequestModel(release_type="SCALE_UP"))

    JSON example:
        {
            "releaseType": "SCALE_UP", 
            "forceRelease": true,
            "allowDestroy": true,
            "withRefresh": true,
        }

    Returns:
        str: The deployment id of the created deployment.
    Raises:
        ValueError: If no current project or cluster is set.
    """
    if properties.release_type != "SCALE_UP":
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="Release type must be SCALE_UP"
            )
        )   
    return create_deployment_of_current_cluster(properties)

@mcp.tool() 
def scale_down_cluster_of_current_cluster(properties: DeploymentRequestModel) -> str:
    """
    Scale down the set current cluster for the set current project. ⬇️
    This should only be called if the cluster is in the state "RUNNING" 🟢 and the cluster is not in the state "SCALED_DOWN" 🔽
    And this only should be an explicit action! ⚠️ Always ask the user to confirm this action. ✅

    example:
        scale_down_cluster_of_current_cluster(DeploymentRequestModel(release_type="SCALE_DOWN"))

    JSON example:
        {
            "releaseType": "SCALE_DOWN", 
            "forceRelease": true,
            "allowDestroy": true,
            "withRefresh": true,
        }

    Returns:
        str: The deployment id of the created deployment.
    Raises:
        ValueError: If no current project or cluster is set.
    """
    if properties.release_type != "SCALE_DOWN":
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="Release type must be SCALE_DOWN"
            )
        )
    return create_deployment_of_current_cluster(properties)

@mcp.tool()
def check_if_cluster_is_running() -> bool:
    """
    Check if the set current cluster is running for the set current project. 🔍
    This tool helps verify if the cluster is in the "RUNNING" state 🟢 before performing operations that require an active cluster.

    Returns:
        bool: True if the cluster is running, False otherwise. 
    """
    cluster = get_current_cluster_details()
    return cluster.cluster_state == "RUNNING"
