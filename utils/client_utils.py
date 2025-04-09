import swagger_client
from mcp.server.fastmcp import FastMCP
from swagger_client.models.stack import Stack
import os
import configparser
from pydantic import BaseModel, Field, create_model
from typing import Any

class ClientUtils:
    cp_url = None
    username = None
    token = None
    _current_project: Stack = None  # Use a private variable for the current project
    mcp = None
    initialized = False

    @staticmethod
    def set_client_config(url: str, user: str, tok: str):
        ClientUtils.cp_url = url
        ClientUtils.username = user
        ClientUtils.token = tok

    @staticmethod
    def get_client():
        if ClientUtils.cp_url is None or ClientUtils.username is None or ClientUtils.token is None:
            raise ValueError("Client configuration not set. Call set_client_config first.")

        configuration = swagger_client.Configuration()
        configuration.username = ClientUtils.username
        configuration.password = ClientUtils.token
        configuration.host = ClientUtils.cp_url
        return swagger_client.ApiClient(configuration)

    @staticmethod
    def get_mcp_instance():
        if not ClientUtils.initialized:
            cp_url, username, token, profile = ClientUtils.initialize()
            ClientUtils.mcp = FastMCP(f"FacetCPGenie for {cp_url}")
            ClientUtils.initialized = True
        return ClientUtils.mcp

    @staticmethod
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

        # print(f"Running MCP server at: {cp_url} using profile {profile}")
        ClientUtils.set_client_config(cp_url, username, token)
        return cp_url, username, token, profile

    @staticmethod
    def set_current_project(project: Stack):
        """
        Set the current project in the utils configuration.

        Args:
            project (Stack): The complete project object to set as current.
        """
        ClientUtils._current_project = project

    @staticmethod
    def get_current_project() -> Stack:
        """
        Get the current project object.

        Returns:
            Stack: The current project object.
        """
        return ClientUtils._current_project

    @staticmethod
    def pydantic_instance_to_swagger_instance(pydantic_instance, swagger_class):
        swagger_kwargs = {}
        alias_map = swagger_class.attribute_map
        reverse_alias_map = {v: k for k, v in alias_map.items()}

        for field_name, value in pydantic_instance.dict(by_alias=True, exclude_unset=True).items():
            # Map alias (JSON key) back to swagger attribute name
            swagger_field = reverse_alias_map.get(field_name, field_name)

            # Fix for internal naming like _global
            if swagger_field.startswith("_") or swagger_field in swagger_class.swagger_types:
                swagger_kwargs[swagger_field] = value
            else:
                # Handle renamed fields like global_ → _global
                if swagger_field + "_" in swagger_class.swagger_types:
                    swagger_kwargs[swagger_field + "_"] = value
                else:
                    swagger_kwargs[swagger_field] = value

        return swagger_class(**swagger_kwargs)
