import httpx
from mcp.server.fastmcp import FastMCP
from typing import List, Optional
import os
import json
from datetime import datetime
import swagger_client

# Create an MCP server
mcp = FastMCP("ControlPlaneServer")

# Base URL for the control plane API
BASE_URL = os.environ.get("CONTROL_PLANE_API_URL", "http://localhost:8080")
# Authentication credentials
AUTH_USERNAME = os.environ.get("CONTROL_PLANE_AUTH_USERNAME", "")
AUTH_TOKEN = os.environ.get("CONTROL_PLANE_AUTH_TOKEN", "")


# Create a shared HTTP client function for all operations
async def get_client():
    headers = {}

    configuration = swagger_client.Configuration()
    configuration.username = AUTH_USERNAME
    configuration.password = AUTH_TOKEN
    configuration.host = BASE_URL
    return swagger_client.ApiClient(configuration)


#############################
# Release Stream API Operations
#############################

# Resource to get all release streams


# Resource to get release streams filtered by stack name

# Tool to create a new release stream
@mcp.tool()
async def create_release_stream(name: str, is_prod: bool = False, description: str = "") -> str:
    """
    Create a new release stream
    
    Args:
        name: Name for the new release stream
        is_prod: Whether this is a production release stream
        description: Optional description of the release stream
    """
    api_instance = swagger_client.UiReleaseStreamControllerApi(get_client())
    swagger_client.ReleaseStreamRequest
    return api_instance.add_using_post(
        swagger_client.ReleaseStreamRequest(name=name, description=description, is_prod=is_prod))


# If this file is run directly
if __name__ == "__main__":
    mcp.run()
