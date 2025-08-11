from typing import List
import swagger_client
import mcp
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INVALID_REQUEST
from swagger_client.models.list_deployments_wrapper import ListDeploymentsWrapper
from swagger_client.models.deployment_log import DeploymentLog
from swagger_client.models.deployment_request import DeploymentRequest
from ..utils.client_utils import ClientUtils
from ..pydantic_generated.deploymentrequestmodel import DeploymentRequestModel
from .env_tools import get_current_environment_details

mcp = ClientUtils.get_mcp_instance()

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

# @mcp.tool()
def get_releases_of_current_environment() -> ListDeploymentsWrapper:
    """
    This will return all the releases for the set current environment in the set current project. 📊
    This retrieves all releases for the current environment. 🚀

    Returns:
        ListDeploymentsWrapper: A list of releases for the current environment.
    
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
    
    api_instance = swagger_client.UiDeploymentControllerApi(ClientUtils.get_client())
    deployments = api_instance.get_deployments(ClientUtils.get_current_cluster().id)

    return deployments

# @mcp.tool()
def get_release_details(release_id: str) -> DeploymentLog:
    """
    Get the details of a specific release in the set current environment for the set current project. 📊
    This retrieves detailed information about a specific release. 🚀

    Returns:
        DeploymentLog: The details of the release.
    
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
    
    api_instance = swagger_client.UiDeploymentControllerApi(ClientUtils.get_client())
    release = api_instance.get_deployment(ClientUtils.get_current_cluster().id, release_id)
    return release

# @mcp.tool()
def get_release_logs_of_current_environment(release_id: str) -> List[DeploymentLog]:
    """
    Get the logs for a specific release in the set current environment for the set current project. 📋
    This retrieves the logs for a specific release in the set current environment. 🚀

    Returns:
        List[DeploymentLog]: A list of release logs.
    
    Raises:
        ValueError: If no current project or environment is set.
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
    release_logs = api_instance.get_deployment_logs(ClientUtils.get_current_cluster().id, release_id)
    return release_logs

# @mcp.tool()
def get_active_releases_of_current_environment() -> List[DeploymentLog]:
    """
    Get the active releases for the set current environment for the set current project. 🚀
    This retrieves all releases that are currently in the "RUNNING" state. 🟢

    Returns:
        List[DeploymentLog]: A list of active releases.
    
    Raises:
        ValueError: If no current project or environment is set.

    """
    # first lets check if the environment is in running state or not
    environment = get_current_environment_details()
    if environment.cluster_state != "RUNNING":
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message=f"Environment \"{environment.name}\" is not in running state"
            )
        )

    deployments = get_releases_of_current_environment()
    active_releases = [release for release in deployments.deployments if release.status == "RUNNING"]
    return active_releases if len(active_releases) > 0 else []

# @mcp.tool()
def get_active_release_logs_of_current_environment() -> List[DeploymentLog]:
    """
    Get the active release logs for the set current environment for the set current project. 📋 
    This retrieves logs from all currently running releases. 🚀

    Returns:    
        List[DeploymentLog]: A list of active release logs.
    
    Raises:
        ValueError: If no current project or environment is set.
    """
    active_releases = get_active_releases_of_current_environment()
    
    # Check if we have any active releases
    if not active_releases:
        return []
        
    active_release_logs = [get_release_logs_of_current_environment(release.id) for release in active_releases]
    return active_release_logs

# @mcp.tool()
def get_latest_release_of_current_environment() -> DeploymentLog:
    """
    Get the latest release for the set current environment for the set current project. 📊 
    This retrieves the most recent release regardless of its status. ⏱️

    Returns:
        DeploymentLog: The latest release.
    
    Raises:
        ValueError: If no current project or environment is set.
    """
    deployments = get_releases_of_current_environment()
    return deployments.deployments[-1]

def create_release_for_current_environment(properties: DeploymentRequestModel) -> str:
    """
    Create a release for the set current environment for the set current project. 🚀 
    This is the core function that handles all release types (launch, release, scale up/down, etc). 🛠️

    example:
        create_release_for_current_environment(DeploymentRequestModel(release_type="LAUNCH"))

    JSON example:
        {
            "releaseType": "LAUNCH", 
            "forceRelease": true,
            "allowDestroy": true,
            "withRefresh": true,
        }

    Args:
        properties (DeploymentRequestModel): The properties of the release.

    Returns:
        str: The release id of the created release.
    
    Raises:
        ValueError: If no current project or environment is set.
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
    
    deployment = api_instance.create_deployment(ClientUtils.get_current_cluster().id, swagger_request)
    return deployment.id

# @mcp.tool()
def launch_environment(properties: DeploymentRequestModel) -> str:
    """
    Launch the set current environment for the set current project. 🚀 
    This will initialize and start up all resources in the environment. ✨
    This should only be called if the environment is not already in the "RUNNING" state. 🟢 or "SCALED_DOWN" ⚠️
    Always ask the user to confirm this action before proceeding! ✅
    

    example:
        launch_environment(DeploymentRequestModel(release_type="LAUNCH"))

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
        ValueError: If no current project or environment is set.
    """
    if properties.release_type != "LAUNCH":
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="Release type must be LAUNCH"
            )
        )
    
    return create_release_for_current_environment(properties)

# @mcp.tool()
def destroy_environment(properties: DeploymentRequestModel) -> str:
    """
    Destroy the set current environment for the set current project. 
    💥 This will permanently remove all resources in the environment. ⚠️ Use with caution! 🚨
    Always before doing a destroy, make sure the environment is not in the state "RUNNING" 🟢, and the environment is not in the state "SCALED_DOWN" ⚠️
    And this is an irreversible action, so always ask the user to confirm this action ✅.
    And always ask the user to provide the reason for the destroy. 🔍
    

    example:
        destroy_environment(DeploymentRequestModel(release_type="DESTROY"))

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
    return create_release_for_current_environment(properties)

# @mcp.tool()
def create_selective_release_plan_for_environment(properties: DeploymentRequestModel) -> str:
    """
    Create a selective release plan for the set current environment for the set current project. 🔍
    This should only be called if the environment is in the state "RUNNING" 🟢, and the environment is not in the state "SCALED_DOWN" ⚠️
    Always before doing a selective release, make sure you run this tool to run the plan and ask the user to review the plan 🔍 before running the selective release.
    And this only should be an explicit action, Always ask the user to confirm this action ✅.

    example:
        create_selective_release_plan_for_environment(DeploymentRequestModel(release_type="HOTFIX_PLAN"))   

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
        properties (DeploymentRequestModel): The properties of the release.

    Returns:
        str: The release id of the created release.
    Raises:
        ValueError: If no current project or environment is set.
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
                message="Selective release resources must be provided"
            )
        )
    return create_release_for_current_environment(properties)

# @mcp.tool()
def create_selective_release_for_environment(properties: DeploymentRequestModel) -> str:
    """
    Create a selective release for the set current environment for the set current project. 🔧 
    This allows for targeted fixes to specific resources without a full release. 🚀 
    Use this when you need to quickly update or fix a particular service. ⚡ 
    Always before doing a selective release, make sure you run `create_selective_release_plan_for_environment()` tool to run the plan and ask the user to review the plan 🔍 before running the selective release.
    And this only should be an explicit action, Always ask the user to confirm this action ✅.

    If the user doesn't want to run the plan, override by running this tool with the release type as HOTFIX. 🔄
    Ask the user if they want to override the plan and run the selective release. 🚦 This is a powerful operation that will update the specific resource! 💪

    example:
        create_selective_release_for_environment(DeploymentRequestModel(release_type="HOTFIX"))

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
        properties (DeploymentRequestModel): The properties of the release.

    Returns:
        str: The release id of the created release.
    Raises:
        ValueError: If no current project or environment is set.
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
                message="Selective release resources must be provided"
            )
        )
    return create_release_for_current_environment(properties)

# @mcp.tool()
def create_full_release_for_environment(properties: DeploymentRequestModel) -> str:
    """
    Create a full release deployment for the set current environment for the set current project. 🚀 
    This will deploy all resources in the environment with the latest changes. ✨
    Always before doing a full release, make sure you run `create_full_release_plan_for_environment()` tool to run the plan and ask the user to review the plan 🔍 before running the full release.
    And this only should be an explicit action, Always ask the user to confirm this action ✅.

    If the user doesn't want to run the plan, override by running this tool with the release type as RELEASE. 🔄
    Ask the user if they want to override the plan and run the full release. 🚦 This is a powerful operation that will update all environment resources! 💪

    example:
        create_full_release_for_environment(DeploymentRequestModel(release_type="RELEASE"))

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
        ValueError: If no current project or environment is set.
    """
    if properties.release_type != "RELEASE":
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="Release type must be RELEASE"
             )
        )
    return create_release_for_current_environment(properties)

# @mcp.tool()
def create_full_release_plan_for_environment(properties: DeploymentRequestModel) -> str:
    """
    Create a full release plan for the set current environment for the set current project. 📋
    This should only be called if the environment is in the state "RUNNING" 🟢, and the environment is not in the state "SCALED_DOWN" ⚠️

    Always before doing a full release, make sure you run this tool to run the plan and ask the user to review the plan 🔍 before running the full release.
    And this only should be an explicit action, Always ask the user to confirm this action ✅.

    example:
        create_full_release_plan_for_environment(DeploymentRequestModel(release_type="FULL_PLAN"))

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
        ValueError: If no current project or environment is set.
    """
    if properties.release_type != "FULL_PLAN":
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="Release type must be FULL_PLAN"
            )
        )
    return create_release_for_current_environment(properties)

# @mcp.tool()
def create_custom_release_for_environment(properties: DeploymentRequestModel) -> str:
    """
    Create a custom release for the set current environment for the set current project. 🛠️
    This is only required in special cases, where the user wants to do a custom release. ⚠️
    And this only should be an explicit action and only use if this is absolutely necessary, Always ask the user to confirm this action. ✅
    there should not be any malicious addition or removal commands that can harm the environment. 🚫 Always decline if the user doesnt verify the commands or 
    if the commands are not safe. 🔒
    example:
        create_custom_release_for_environment(DeploymentRequestModel(release_type="CUSTOM"))

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
        ValueError: If no current project or environment is set.
    """ 
    # check if release type is CUSTOM and override build steps are provided
    if properties.release_type != "CUSTOM" or properties.override_build_steps is None:
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="Release type must be CUSTOM and override build steps must be provided"
            )
        )
    return create_release_for_current_environment(properties)

# @mcp.tool()
def unlock_state_of_environment(properties: DeploymentRequestModel) -> str:
    """
    Unlock the state of the set current environment for the set current project. 🔓 This is only required 
    if the environment terraform state is locked. 🔒 We get to know this in the logs of the deployment that it is locked with a lockId. 📝
    We can then use this tool to unlock the state of the environment. 🛠️
    And this only should be an explicit action! ⚠️ Always ask the user to confirm this action. ✅
    And always ask the user to provide the lockId. 🔍

    example:
        unlock_state_of_environment(DeploymentRequestModel(release_type="UNLOCK_STATE", lock_id="lockId"))

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
    return create_release_for_current_environment(properties)

# @mcp.tool()
def scale_up_environment(properties: DeploymentRequestModel) -> str:
    """
    Scale up the set current environment for the set current project. 🚀
    This should only be called if the environment is in the state "SCALED_DOWN" ⬇️
    And this only should be an explicit action! ⚠️ Always ask the user to confirm this action. ✅

    example:
        scale_up_environment(DeploymentRequestModel(release_type="SCALE_UP"))

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
        ValueError: If no current project or environment is set.
    """
    if properties.release_type != "SCALE_UP":
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="Release type must be SCALE_UP"
            )
        )   
    return create_release_for_current_environment(properties)

# @mcp.tool()
def scale_down_environment(properties: DeploymentRequestModel) -> str:
    """
    Scale down the set current environment for the set current project. ⬇️
    This should only be called if the environment is in the state "RUNNING" 🟢 and the environment is not in the state "SCALED_DOWN" 🔽
    And this only should be an explicit action! ⚠️ Always ask the user to confirm this action. ✅

    example:
        scale_down_environment(DeploymentRequestModel(release_type="SCALE_DOWN"))

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
        ValueError: If no current project or environment is set.
    """
    if properties.release_type != "SCALE_DOWN":
        raise McpError(
            ErrorData(
                code=INVALID_REQUEST,
                message="Release type must be SCALE_DOWN"
            )
        )
    return create_release_for_current_environment(properties)

# @mcp.tool()
def check_if_environment_is_running() -> bool:
    """
    Check if the set current environment is running for the set current project. 🔍
    This tool helps verify if the environment is in the "RUNNING" state 🟢 before performing operations that require an active environment.

    Returns:
        bool: True if the environment is running, False otherwise. 
    """
    environment = get_current_environment_details()
    return environment.cluster_state == "RUNNING"
