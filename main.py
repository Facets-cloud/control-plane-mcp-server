import os
import sys
from mcp.server.fastmcp import FastMCP
import swagger_client
import configparser

def initialize():
    """
    Initialize configuration from environment variables or a credentials file.

    Returns:
        tuple: containing cp_url, username, token, and profile.

    Raises:
        ValueError: If profile is not specified or if required credentials are missing.
    """
    profile = os.getenv("FACETS_PROFILE", "")
    cp_url = os.getenv("CONTROL_PLANE_URL", "")
    username = os.getenv("FACETS_USERNAME", "")
    token = os.getenv("FACETS_TOKEN", "")

    if profile and not (cp_url and username and token):
        # Assume credentials exist in ~/.facets/credentials
        config = configparser.ConfigParser()
        config.read(os.path.expanduser("~/.facets/credentials"))

        if config.has_section(profile):
            cp_url = config.get(profile, "control_plane_url", fallback=cp_url)
            username = config.get(profile, "username", fallback=username)
            token = config.get(profile, "token", fallback=token)
        else:
            raise ValueError(f"Profile '{profile}' not found in credentials file.")

    if not (cp_url and username and token):
        raise ValueError("Control plane URL, username, and token are required.")

    print(f"Running MCP server at: {cp_url} using profile {profile}")
    return cp_url, username, token, profile

# Initialize configuration
cp_url, username, token, profile = initialize()

# Create an MCP server
mcp = FastMCP(f"FacetCPGenie for {cp_url}")

# Create a shared HTTP client function for all operations
def get_client():
    configuration = swagger_client.Configuration()
    configuration.username = username
    configuration.password = token
    configuration.host = cp_url
    return swagger_client.ApiClient(configuration)

# Private method to test login using the ApplicationController
def _test_login() -> bool:
    """
    Test login using the ApplicationController.

    Returns:
        bool: True if login is successful, False otherwise.
    """
    try:
        api_instance = swagger_client.ApplicationControllerApi(get_client())
        # Assuming there's a method in ApplicationControllerApi to test the connection or login status.
        response = api_instance.me_using_get()  # Example method that requires login
        print("Login test successful.")
        return True
    except Exception as e:
        print(f"Login test failed: {e}")
        return False

#############################
# Release Stream API Operations
#############################

# Resource to get all release streams


# Resource to get release streams filtered by stack name

# Tool to create a new release stream
@mcp.tool()
def create_release_stream(name: str, is_prod: bool = False, description: str = "") -> str:
    """
    Create a new release stream
    
    Args:
        name: Name for the new release stream
        is_prod: Whether this is a production release stream
        description: Optional description of the release stream
    """
    api_instance = swagger_client.UiReleaseStreamControllerApi(get_client())
    return api_instance.add_using_post(swagger_client.ReleaseStreamRequest(name=name, description=description, prod=is_prod))


# If this file is run directly
if __name__ == "__main__":
    print("Server is initializing...")
    if _test_login():
        print("Login was successful.")
    create_release_stream("test", True, "Ddd")
    mcp.run()
