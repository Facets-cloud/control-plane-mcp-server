import os
from ..config import mcp


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
    Get the comprehensive Facets resource management guide with complete workflow instructions.
    
    **Purpose & Context:**
    This function returns the **MASTER REFERENCE GUIDE** for infrastructure resource management
    in Facets. It contains detailed workflows, best practices, troubleshooting guides, and
    comprehensive instructions that complement the individual MCP tool functions.
    
    **When to Use This Guide:**
    - **Getting Started**: New users learning Facets resource management
    - **Complex Workflows**: When combining multiple tools for advanced operations
    - **Troubleshooting**: When individual tools aren't working as expected
    - **Best Practices**: Understanding recommended approaches and patterns
    - **Reference**: Quick lookup for syntax, patterns, and workflows
    
    **What's Included:**
    - Complete resource creation workflows (with examples)
    - Resource configuration and update procedures
    - Environment override management
    - Dependency handling and input management
    - Special annotation explanations (x-ui-secret-ref, etc.)
    - Troubleshooting common issues
    - Best practices and security recommendations
    
    **Prerequisites:**
    - None - this is reference documentation
    - Use alongside other MCP tools for practical implementation
    
    **LLM-Friendly Tags:** [REFERENCE] [COMPREHENSIVE] [WORKFLOW-GUIDE] [BEST-PRACTICES]

    Returns:
        str: Complete markdown-formatted resource management guide
        
    **Integration with MCP Tools:**
    This guide provides the **conceptual framework** while MCP tools provide the **implementation**:
    - Guide explains workflows → MCP tools execute the steps
    - Guide shows examples → MCP tools provide the actual functionality
    - Guide troubleshoots issues → MCP tools resolve specific problems
    
    **Pro Tips for LLMs:**
    - Reference this guide when users ask complex "how do I..." questions
    - Use guide examples to explain workflows before executing MCP tools
    - Consult troubleshooting sections when MCP tools return errors
    - Extract relevant sections to answer specific user questions
    
    **See Also:**
    - All MCP tools implement the workflows described in this guide
    - `list_available_resources()` - Start resource creation workflows
    - `use_project()` and `use_environment()` - Set required contexts
    - `get_resource_schema_public()` - Explore resource properties
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
