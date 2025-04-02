#!/usr/bin/env python
"""
Utility script to test the connection to the control plane API.
Usage: python test_connection.py --api-url=http://your-api-url --token=your-token
"""

import argparse
import asyncio
import httpx
import sys
import os


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test the connection to the control plane API")
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


async def test_connection(api_url, username, token):
    """Test the connection to the control plane API."""
    headers = {}
    if username and token:
        import base64
        auth_string = f"{username}:{token}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        headers["Authorization"] = f"Basic {encoded_auth}"
    
    headers["Content-Type"] = "application/json"
    
    try:
        # Create HTTP client
        async with httpx.AsyncClient(
            base_url=api_url,
            headers=headers,
            timeout=10.0
        ) as client:
            # Test release stream endpoint
            print(f"Testing connection to {api_url}/cc-ui/v1/release-stream...")
            response = await client.get("/cc-ui/v1/release-stream")
            response.raise_for_status()
            
            # Print response details
            print(f"✅ Connection successful! Status code: {response.status_code}")
            
            # Print release stream count
            streams = response.json()
            print(f"Found {len(streams)} release streams")
            
            # Print the names of the first few streams
            if streams:
                print("\nExample release streams:")
                for stream in streams[:5]:  # Show up to 5 streams
                    print(f"- {stream.get('name', 'Unnamed')}")
                
                if len(streams) > 5:
                    print(f"... and {len(streams) - 5} more")
            
            return True
    
    except httpx.HTTPStatusError as e:
        print(f"❌ API request failed: {e}")
        print(f"Status code: {e.response.status_code}")
        print(f"Response body: {e.response.text}")
    except httpx.ConnectError:
        print("❌ Connection error: Could not connect to the API server")
        print("Please check the API URL and ensure the server is running")
    except httpx.TimeoutException:
        print("❌ Timeout error: The API server took too long to respond")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    return False


def main():
    """Run the connection test."""
    args = parse_args()
    
    print(f"Testing connection to control plane API at {args.api_url}")
    print(f"Using Basic authentication: {'Yes' if args.username and args.token else 'No'}")
    
    success = asyncio.run(test_connection(args.api_url, args.username, args.token))
    
    if success:
        print("\nConnection test passed! The server should work correctly.")
        sys.exit(0)
    else:
        print("\nConnection test failed. Please check your API URL, token, and server status.")
        sys.exit(1)


if __name__ == "__main__":
    main()
