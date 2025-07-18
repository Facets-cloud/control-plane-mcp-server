import os
from ..utils.client_utils import ClientUtils

mcp = ClientUtils.get_mcp_instance()


def _get_resource_management_guide_content() -> str:
    """
    Internal function to read the resource management guide content.
    
    Returns:
        The content of the resource management guide
    """
    try:
        # Get the absolute path to the docs directory
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        guide_path = os.path.join(current_dir, 'docs', 'resource_management_guide.md')

        # Read the guide from the file
        with open(guide_path, 'r') as file:
            guide = file.read()

        return guide
    except Exception as e:
        # Fallback message in case the file can't be read
        return f"Error reading resource management guide: {str(e)}. Please contact the administrator."


@mcp.tool()
def get_resource_management_guide() -> str:
    """
    Get comprehensive instructions for managing resources in the Control Plane.
    
    This tool returns detailed guidance on how to add, update, configure, and delete resources
    in a project/stack/blueprint. It covers the complete workflow for resource management,
    including handling dependencies, selecting compatible resources, and working with
    special annotations.
    
    Returns:
        A comprehensive guide with instructions for managing resources
    """
    return _get_resource_management_guide_content()


@mcp.resource("docs://resource-management-guide")
def resource_management_guide() -> str:
    """
    Resource containing comprehensive instructions for managing resources in the Control Plane.
    
    This resource provides detailed guidance on how to add, update, configure, and delete resources
    in a project/stack/blueprint. It covers the complete workflow for resource management,
    including handling dependencies, selecting compatible resources, and working with
    special annotations.
    
    Returns:
        A comprehensive guide with instructions for managing resources
    """
    return _get_resource_management_guide_content()
