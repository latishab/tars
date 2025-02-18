# Model Context Protocol (MCP) for TARS

This directory contains MCP servers that enable TARS to interact with various systems and services through a standardized protocol.

## Directory Structure

src/
├── mcp/
│   ├── servers/ # put your servers in this file
│   │   ├── filesystem/
│   │   │   ├── fs-mcp-server.js
│   │   │   ├── package.json     
│   │   └── └── README.md
└── └── README.md

## Configuring MCP Servers

### 1. Configuration in TARS

Add your MCP server configuration to `config.ini`:

```ini
[MCP]
enabled = True
servers = [
    {
        "name": "filesystem",
        "command": "node",
        "args": ["src/mcp/servers/filesystem/fs-mcp-server.js", "src/memory", "src/character"],
        "script_type": "node",
        "risk_level": "high",
        "requires_confirmation": true,
        "allowed_directories": [
            "src/memory",
            "src/character"
        ]
    }
]

### 2. Server Parameters
Each server configuration requires:

name: Unique identifier for the server
command: Command to run the server (e.g., "node", "python")
args: List of arguments passed to the server
script_type: Type of server ("node" or "python")
risk_level: Security level ("low", "medium", "high")
requires_confirmation: Whether operations need user confirmation
Additional server-specific parameters (e.g., allowed_directories)

3. Setting Up a New Server
Create a new directory in src/mcp/servers/
Implement the server following the MCP protocol
Add server configuration to config.ini
Install dependencies if required
Example for Node.js server:

bash
mkdir -p src/mcp/servers/myserver
cd src/mcp/servers/myserver
npm init
npm install @modelcontextprotocol/sdk
4. Security Considerations
Always validate inputs and paths
Implement proper access controls
Use risk_level appropriately
Enable confirmations for dangerous operations
Limit server capabilities to necessary functions
Available Servers
Filesystem Server
Provides secure file system access:

Read/write files
List directories
Search files
Move/rename files
Get file metadata
Setup:

bash
cd src/mcp/servers/filesystem
npm install
chmod +x fs-mcp-server.js
Creating a New MCP Server
Create server directory:
bash
mkdir -p src/mcp/servers/myserver
Create basic files:
bash
touch src/mcp/servers/myserver/server.js
touch src/mcp/servers/myserver/package.json
touch src/mcp/servers/myserver/README.md
Implement required MCP handlers:
JavaScript
// Basic MCP server template
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new Server(
  {
    name: "my-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Implement tool handlers
server.setRequestHandler("ListTools", async () => {
  return {
    tools: [
      {
        name: "my_tool",
        description: "Tool description",
        inputSchema: {
          type: "object",
          properties: {
            param: { type: "string" }
          },
          required: ["param"]
        }
      }
    ]
  };
});

server.setRequestHandler("CallTool", async (request) => {
  // Implement tool functionality
});

// Start server
async function runServer() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Server running on stdio");
}

runServer().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
Add to config.ini:
INI
[MCP]
enabled = True
servers = [
    {
        "name": "myserver",
        "command": "node",
        "args": ["src/mcp/servers/myserver/server.js"],
        "script_type": "node",
        "risk_level": "medium",
        "requires_confirmation": true
    }
]
Troubleshooting
Server not starting:

Check file permissions
Verify dependencies are installed
Check server configuration in config.ini
Permission errors:

Verify allowed directories/resources
Check risk level settings
Ensure proper file permissions
Communication errors:

Verify MCP protocol implementation
Check server process is running
Review server logs
Contributing
Fork the repository
Create a new server directory
Implement the MCP protocol
Add documentation
Submit a pull request
Resources
MCP Protocol Documentation
SDK Reference
Server Examples