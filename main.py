import os
import sys
import swagger_client
from utils.client_utils import ClientUtils

# Initialize configuration and MCP instance

from tools.release_stream_tool import create_release_stream

def _test_login() -> bool:
    """
    Test login using the ApplicationController.

    Returns:
        bool: True if login is successful, False otherwise.
    """
    try:
        api_instance = swagger_client.ApplicationControllerApi(ClientUtils.get_client())
        # Assuming there's a method in ApplicationControllerApi to test the connection or login status.
        response = api_instance.me_using_get()  # Example method that requires login
        # print("Login test successful.")
        return True
    except Exception as e:
        print(f"Login test failed: {e}")
        return False


if __name__ == "__main__":
    print("Server is initializing...")
    mcp = ClientUtils.get_mcp_instance()
    if _test_login():
        print("Login was successful.")
        mcp.run()
