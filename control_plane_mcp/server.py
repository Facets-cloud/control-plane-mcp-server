"""Main server entry point for Facets Control Plane MCP Server."""

import logging
import os

import click
import swagger_client
from dotenv import load_dotenv

load_dotenv()

# Import configuration and utilities
from .config import mcp
from .utils.client_utils import ClientUtils

# Now import tools - they will register with the MCP instance
from .tools import *

logger = logging.getLogger(__name__)


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
        logger.error(f"Login test failed: {e}")
        return False


@click.command()
@click.option(
    '--transport',
    type=click.Choice(['stdio', 'streamable-http'], case_sensitive=False),
    default='stdio',
    help='Transport protocol to use (default: stdio)'
)
@click.option(
    '--port',
    type=int,
    default=3000,
    help='Port to listen on for streamable-http transport (default: 3000)'
)
@click.option(
    '--host',
    type=str,
    default='localhost',
    help='Host to bind to for streamable-http transport (default: localhost)'
)
@click.option(
    '--stateless',
    is_flag=True,
    default=False,
    help='Run in stateless mode for streamable-http (no session persistence)'
)
@click.option(
    '--json-response',
    is_flag=True,
    default=False,
    help='Use JSON responses instead of SSE streams for streamable-http'
)
@click.option(
    '--log-level',
    type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR'], case_sensitive=False),
    default='INFO',
    help='Logging level (default: INFO)'
)
def main(
    transport: str,
    port: int,
    host: str,
    stateless: bool,
    json_response: bool,
    log_level: str
):
    """Run the Facets Control Plane MCP server."""
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Update MCP instance settings for transport configuration
    if transport == 'streamable-http':
        mcp.settings.host = host
        mcp.settings.port = port
        mcp.settings.stateless_http = stateless
        mcp.settings.json_response = json_response
    
    # Initialize client configuration from environment or credentials file
    try:
        ClientUtils.initialize()
        # Test authentication
        if not _test_login():
            logger.error("Authentication failed.")
            exit(1)
    except Exception as e:
        logger.error(f"Failed to initialize client configuration: {e}")
        exit(1)
    
    # Log startup information
    if transport == 'streamable-http':
        logger.info(f"Starting Facets Control Plane MCP server on http://{host}:{port}/mcp")
        logger.info(f"Mode: {'Stateless' if stateless else 'Stateful'}")
        logger.info(f"Response format: {'JSON' if json_response else 'SSE'}")
    else:
        logger.info("Starting Facets Control Plane MCP server with stdio transport")
    
    # Run the server with specified transport
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
