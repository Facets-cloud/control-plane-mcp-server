#!/usr/bin/env python
"""
Development script to quickly run the server with the MCP Inspector.
Usage: python dev.py --api-url=http://your-api-url --token=your-token
"""

import argparse
import subprocess
import os
import sys


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the control plane MCP server in development mode")
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
    return parser.parse_args()


def main():
    """Run the server in development mode with the MCP Inspector."""
    args = parse_args()
    
    # Set environment variables
    env = os.environ.copy()
    env["CONTROL_PLANE_API_URL"] = args.api_url
    env["CONTROL_PLANE_AUTH_USERNAME"] = args.username
    env["CONTROL_PLANE_AUTH_TOKEN"] = args.token
    
    # Determine the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Run with MCP Inspector
    try:
        cmd = ["uv", "run", "mcp", "dev", os.path.join(script_dir, "main.py")]
        print(f"Running: {' '.join(cmd)}")
        print(f"API URL: {args.api_url}")
        print(f"Username: {'Set' if args.username else 'Not set'}")
        print(f"Token: {'Set' if args.token else 'Not set'}")
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        print("\nServer stopped")
    except subprocess.CalledProcessError as e:
        print(f"Error running server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
