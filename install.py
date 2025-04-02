#!/usr/bin/env python
"""
Installation script to easily install the server with Claude Desktop.
Usage: python install.py --api-url=http://your-api-url --token=your-token
"""

import argparse
import subprocess
import os
import sys


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Install the control plane MCP server with Claude Desktop")
    parser.add_argument(
        "--api-url", 
        help="Base URL of the control plane API", 
        default=os.environ.get("CONTROL_PLANE_API_URL", "http://localhost:8080")
    )
    parser.add_argument(
        "--username", 
        help="Username for Basic authentication", 
        default=os.environ.get("CONTROL_PLANE_AUTH_USERNAME", "")
    )
    parser.add_argument(
        "--token", 
        help="Password for Basic authentication", 
        default=os.environ.get("CONTROL_PLANE_AUTH_TOKEN", "")
    )
    parser.add_argument(
        "--name",
        help="Name to use for the server in Claude Desktop",
        default="ControlPlaneServer"
    )
    return parser.parse_args()


def main():
    """Install the server with Claude Desktop."""
    args = parse_args()
    
    # Determine the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Build the command
    cmd = ["uv", "run", "mcp", "install", os.path.join(script_dir, "main.py")]
    
    # Add environment variables
    cmd.extend(["-v", f"CONTROL_PLANE_API_URL={args.api_url}"])
    if args.username:
        cmd.extend(["-v", f"CONTROL_PLANE_AUTH_USERNAME={args.username}"])
    if args.token:
        cmd.extend(["-v", f"CONTROL_PLANE_AUTH_TOKEN={args.token}"])
    
    # Add name if specified
    if args.name != "ControlPlaneServer":
        cmd.extend(["--name", args.name])
    
    # Run the installation command
    try:
        print(f"Running: {' '.join(cmd)}")
        print(f"API URL: {args.api_url}")
        print(f"Username: {'Set' if args.username else 'Not set'}")
        print(f"Token: {'Set' if args.token else 'Not set'}")
        subprocess.run(cmd, check=True)
        
        print("\nServer installed successfully!")
        print("Please restart Claude Desktop to use the new server.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
