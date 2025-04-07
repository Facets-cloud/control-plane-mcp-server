from utils.client_utils import ClientUtils
import swagger_client

mcp = ClientUtils.get_mcp_instance()

@mcp.tool()
def create_release_stream(name: str, is_prod: bool = False, description: str = "") -> str:
    """
    Create a new release stream
    
    Args:
        name: Name for the new release stream
        is_prod: Whether this is a production release stream
        description: Optional description of the release stream
    """
    api_instance = swagger_client.UiReleaseStreamControllerApi(ClientUtils.get_client())
    return api_instance.add_using_post(swagger_client.ReleaseStreamRequest(name=name, description=description, prod=is_prod))
