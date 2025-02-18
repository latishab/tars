
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

 - name: Unique identifier for the server 
 - command: Command to run the server (e.g., "node", "python") 
 - args: List of arguments passed to the server 
 - script_type: Type of server ("node" or "python") 
 - risk_level: Security level ("low", "medium", "high") 
 - requires_confirmation: Whether operations need user confirmation 
 - additional server-specific parameters (e.g., allowed_directories)
 
### 3. Setting Up a New Server
 - Create a new directory in src/mcp/servers/ 
 - Implement the server following the MCP protocol 
 - Add server configuration to config.ini
   Install dependencies if required

Example for Node.js server:

    bash
    mkdir -p src/mcp/servers/myserver
    cd src/mcp/servers/myserver
    npm init
    npm install @modelcontextprotocol/sdk

### 4. Security Considerations
Always validate inputs and paths
Implement proper access controls
Use risk_level appropriately
Enable confirmations for dangerous operations
Limit server capabilities to necessary functions

### 5. Pre-built MCP Servers in TARS

**1. Filesystem Server**

The filesystem server provides secure access to the file system with the following capabilities:
 - Read/write files 
 - List directories 
 - Search files 
 - Move/rename files 
 - Get file metadata
