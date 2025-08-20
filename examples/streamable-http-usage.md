# Streamable HTTP Transport Examples - Control Plane MCP Server

This document provides examples of using the Facets Control Plane MCP server with streamable HTTP transport.

## Starting the Server

### Basic HTTP Server

Start the server on the default port (3000):

```bash
uv run facets-cp-mcp-server --transport streamable-http
```

The server will be available at: `http://localhost:3000/mcp`

### Custom Port and Host

To run on a different port or bind to all interfaces:

```bash
# Run on port 8080
uv run facets-cp-mcp-server --transport streamable-http --port 8080

# Bind to all interfaces (for network access)
uv run facets-cp-mcp-server --transport streamable-http --host 0.0.0.0

# Both custom port and host
uv run facets-cp-mcp-server --transport streamable-http --port 8080 --host 0.0.0.0
```

### Stateless Mode

For better scalability without session persistence:

```bash
uv run facets-cp-mcp-server --transport streamable-http --stateless
```

### JSON Responses

Use JSON instead of Server-Sent Events (SSE):

```bash
uv run facets-cp-mcp-server --transport streamable-http --json-response
```

### Debug Logging

Enable detailed logging for troubleshooting:

```bash
uv run facets-cp-mcp-server --transport streamable-http --log-level DEBUG
```

## Testing the Server

### Using curl

Test if the server is running:

```bash
# Basic connectivity test
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"0.1.0","capabilities":{},"clientInfo":{"name":"curl-test","version":"1.0.0"}}}'
```

### Using an MCP Client

Configure your MCP client to connect via HTTP:

```json
{
  "url": "http://localhost:3000/mcp",
  "transport": "streamable-http"
}
```

## Environment Variables

Set authentication environment variables before starting:

```bash
export FACETS_PROFILE="default"
export FACETS_USERNAME="your-username"
export FACETS_TOKEN="your-token"
export CONTROL_PLANE_URL="https://your-control-plane.facets.cloud"

uv run facets-cp-mcp-server --transport streamable-http
```

## Production Deployment

### Using systemd Service

Create a systemd service file at `/etc/systemd/system/facets-cp-mcp.service`:

```ini
[Unit]
Description=Facets Control Plane MCP Server
After=network.target

[Service]
Type=simple
User=mcp
WorkingDirectory=/opt/facets-cp-mcp
Environment="FACETS_PROFILE=default"
Environment="FACETS_USERNAME=service-user"
Environment="FACETS_TOKEN=service-token"
Environment="CONTROL_PLANE_URL=https://control-plane.facets.cloud"
ExecStart=/usr/local/bin/uv run facets-cp-mcp-server --transport streamable-http --host 0.0.0.0 --port 8080
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable facets-cp-mcp
sudo systemctl start facets-cp-mcp
sudo systemctl status facets-cp-mcp
```

### Using Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.12-slim

# Install uv
RUN pip install uv

# Copy the application
WORKDIR /app
COPY . .

# Install dependencies
RUN uv pip install -e .

# Expose port
EXPOSE 8080

# Set entrypoint
ENTRYPOINT ["uv", "run", "facets-cp-mcp-server"]
CMD ["--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8080"]
```

Build and run:

```bash
docker build -t facets-cp-mcp .
docker run -p 8080:8080 \
  -e FACETS_PROFILE=default \
  -e FACETS_USERNAME=your-username \
  -e FACETS_TOKEN=your-token \
  -e CONTROL_PLANE_URL=https://control-plane.facets.cloud \
  facets-cp-mcp
```

### Using Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  facets-cp-mcp:
    build: .
    ports:
      - "8080:8080"
    environment:
      - FACETS_PROFILE=default
      - FACETS_USERNAME=${FACETS_USERNAME}
      - FACETS_TOKEN=${FACETS_TOKEN}
      - CONTROL_PLANE_URL=${CONTROL_PLANE_URL}
    command: ["--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8080", "--log-level", "INFO"]
    restart: unless-stopped
```

Run with:

```bash
docker-compose up -d
```

## Reverse Proxy with nginx

For production deployments behind nginx:

```nginx
server {
    listen 443 ssl http2;
    server_name cp-mcp.example.com;

    ssl_certificate /etc/ssl/certs/cp-mcp.crt;
    ssl_certificate_key /etc/ssl/private/cp-mcp.key;

    location /mcp {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        
        # For SSE support
        proxy_set_header Connection '';
        proxy_set_header Cache-Control 'no-cache';
        proxy_set_header X-Accel-Buffering 'no';
        
        # Standard headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running operations
        proxy_read_timeout 3600;
        proxy_connect_timeout 3600;
        proxy_send_timeout 3600;
    }
}
```

## Monitoring

### Health Check Endpoint

The streamable-http transport automatically provides a health check:

```bash
curl http://localhost:3000/mcp
```

### Logging

Monitor server logs:

```bash
# If running directly
uv run facets-cp-mcp-server --transport streamable-http --log-level INFO

# If using systemd
journalctl -u facets-cp-mcp -f

# If using Docker
docker logs -f facets-cp-mcp
```

## Troubleshooting

### Authentication Errors

If authentication fails:

1. Verify environment variables are set correctly
2. Check token expiration and regenerate if needed
3. Verify CONTROL_PLANE_URL is accessible
4. Test API connectivity manually

### Connection Refused

If you get "connection refused" errors:

1. Check the server is running: `ps aux | grep facets-cp-mcp-server`
2. Verify the port is listening: `netstat -tlnp | grep 3000`
3. Check firewall rules: `sudo ufw status`

### Performance Issues

For better performance:

1. Use stateless mode: `--stateless`
2. Enable JSON responses for non-streaming: `--json-response`
3. Run multiple workers behind a load balancer
4. Monitor resource usage and scale appropriately

## Comparison: stdio vs streamable-http

| Feature | stdio | streamable-http |
|---------|-------|-----------------|
| Protocol | Process pipes | HTTP/SSE |
| Deployment | Local only | Local or remote |
| Concurrency | Single client | Multiple clients |
| Session Management | Process-based | Configurable |
| Streaming | Built-in | SSE or JSON |
| Authentication | Environment-based | HTTP headers |
| Scalability | Limited | Horizontal scaling |
| Use Case | Development | Production |

## Advantages for Remote Deployment

The Control Plane MCP server is particularly well-suited for remote deployment because:

1. **No file system dependencies** - All operations are API-based
2. **Stateless operations** - Most tools work without persistent state
3. **API authentication** - Clean separation of auth from transport
4. **Resource efficiency** - Minimal memory and CPU footprint
5. **Horizontal scaling** - Can run multiple instances behind load balancer

This makes it ideal for:
- **Team collaboration** - Multiple developers accessing shared control plane
- **CI/CD integration** - Automated infrastructure operations
- **Remote management** - Managing infrastructure from anywhere
- **Multi-tenant scenarios** - Different teams with isolated credentials