import httpx
from mcp.server.fastmcp import FastMCP
from typing import List, Optional
import os
import json
from datetime import datetime

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
    if AUTH_USERNAME and AUTH_TOKEN:
        # Create Base64 encoded Basic Auth header
        import base64
        auth_string = f"{AUTH_USERNAME}:{AUTH_TOKEN}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        headers["Authorization"] = f"Basic {encoded_auth}"
    
    return httpx.AsyncClient(
        base_url=BASE_URL,
        headers={
            **headers,
            "Content-Type": "application/json"
        }
    )

#############################
# Release Stream API Operations
#############################

# Resource to get all release streams
@mcp.resource("release-streams://list")
async def list_release_streams() -> str:
    """Fetch all release streams from the control plane"""
    async with await get_client() as client:
        response = await client.get("/cc-ui/v1/release-stream")
        response.raise_for_status()
        streams = response.json()
        
        # Format the response into a readable string
        result = "## Release Streams\n\n"
        for stream in streams:
            result += f"### {stream['name']}\n"
            result += f"- Production: {'Yes' if stream.get('isProd') else 'No'}\n"
            result += f"- Description: {stream.get('description', 'N/A')}\n"
            result += f"- Created by: {stream.get('createdBy', 'N/A')}\n"
            
            # Format creation date if available
            if 'creationDate' in stream and stream['creationDate']:
                try:
                    creation_date = datetime.fromisoformat(stream['creationDate'].replace('Z', '+00:00'))
                    result += f"- Creation date: {creation_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
                except (ValueError, TypeError):
                    result += f"- Creation date: {stream.get('creationDate', 'N/A')}\n"
            
            result += f"- Built-in: {'Yes' if stream.get('isBuiltIn') else 'No'}\n"
            
            # Add mapped cluster names if available
            if 'mappedClusterNames' in stream and stream['mappedClusterNames']:
                result += "- Mapped clusters:\n"
                for cluster in stream['mappedClusterNames']:
                    result += f"  - {cluster}\n"
            
            result += "\n"
        
        return result

# Resource to get release streams filtered by stack name
@mcp.resource("release-streams://stack/{stack_name}")
async def get_release_streams_by_stack(stack_name: str) -> str:
    """Fetch release streams for a specific stack"""
    async with await get_client() as client:
        response = await client.get(f"/cc-ui/v1/release-stream?stackName={stack_name}")
        response.raise_for_status()
        streams = response.json()
        
        # Format the response into a readable string
        result = f"## Release Streams for Stack: {stack_name}\n\n"
        for stream in streams:
            result += f"### {stream['name']}\n"
            result += f"- Production: {'Yes' if stream.get('isProd') else 'No'}\n"
            result += f"- Description: {stream.get('description', 'N/A')}\n"
            # Include other details as in the list function
            result += "\n"
        
        return result

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
    payload = {
        "name": name,
        "isProd": is_prod,
        "description": description
    }
    
    async with await get_client() as client:
        response = await client.post("/cc-ui/v1/release-stream", json=payload)
        response.raise_for_status()
        new_stream = response.json()
        
        return f"""Release stream created successfully!

Name: {new_stream.get('name')}
Production: {'Yes' if new_stream.get('isProd') else 'No'}
Description: {new_stream.get('description', 'N/A')}
"""

# Tool to delete a release stream
@mcp.tool()
async def delete_release_stream(name: str) -> str:
    """
    Delete a release stream
    
    Args:
        name: Name of the release stream to delete
    """
    async with await get_client() as client:
        response = await client.delete(f"/cc-ui/v1/release-stream/{name}")
        response.raise_for_status()
        
        return f"Release stream '{name}' has been deleted successfully."

# Add some helpful prompts
@mcp.prompt()
def create_release_stream_prompt(is_prod: bool = False) -> str:
    """Guided prompt for creating a new release stream"""
    prod_status = "production" if is_prod else "non-production"
    return f"""I want to create a new {prod_status} release stream.

Please help me create it with a meaningful name and description. I need to know:
1. What naming conventions should I follow?
2. What information should I include in the description?
3. What happens after I create the release stream?"""

@mcp.prompt()
def delete_release_stream_prompt(stream_name: str) -> str:
    """Guided prompt for deleting a release stream"""
    return f"""I need to delete the release stream named '{stream_name}'.

Please help me understand:
1. What are the implications of deleting this release stream?
2. Are there any dependencies I should be aware of?
3. Is this action reversible?"""

# If this file is run directly
if __name__ == "__main__":
    mcp.run()
