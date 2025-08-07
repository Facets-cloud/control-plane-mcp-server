"""Main server entry point for Facets Control Plane MCP Server."""

import swagger_client
from dotenv import load_dotenv
import os

load_dotenv()

# Import from the package structure
from .utils.client_utils import ClientUtils
from .tools import *


def _test_login() -> bool:
    """
    Test login using the ApplicationController.

    Returns:
        bool: True if login is successful, False otherwise.
    """
    try:
        api_instance = swagger_client.ApplicationControllerApi(ClientUtils.get_client())
        api_instance.me()
        return True
    except Exception as e:
        print(f"Login test failed: {e}")
        return False


def main():
    """Main entry point for the MCP server."""
    mcp = ClientUtils.get_mcp_instance()
    if _test_login():
        mcp.run(transport="stdio")
        print("🚀 MCP Server is running")
    else:
        print("❌ Login test failed. Server not started.")
        exit(1)


if __name__ == "__main__":
    main()
