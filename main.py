# Initialize configuration and MCP instance

from tools.project_tools import *

from tools.configure_resource_tool import *

def _test_login() -> bool:
    """
    Test login using the ApplicationController.

    Returns:
        bool: True if login is successful, False otherwise.
    """
    try:
        api_instance = swagger_client.ApplicationControllerApi(ClientUtils.get_client())
        api_instance.me_using_get()
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