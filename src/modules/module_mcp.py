"""
module_mcp.py

Safe MCP (Model Context Protocol) client implementation for TARS.
Includes verification layer for secure execution of MCP server capabilities.
"""

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import Dict, Any, Optional, List, Tuple
import asyncio
import json
from dataclasses import dataclass
from modules.module_messageQue import queue_message
from modules.module_config import load_config
from modules.module_llm import raw_complete_llm

@dataclass
class MCPServerConfig:
    """Configuration for an MCP server"""
    name: str
    command: str
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    working_dir: Optional[str] = None
    risk_level: str = "medium"  # low, medium, high
    requires_confirmation: bool = True

class SafetyVerifier:
    """Handles safety verification for MCP operations"""

    RISK_LEVELS = {
        "low": ["read", "list", "get", "query"],
        "medium": ["write", "update", "modify", "send"],
        "high": ["delete", "remove", "execute", "run", "system"]
    }

    @staticmethod
    def analyze_risk(operation: str, params: Dict[str, Any]) -> Tuple[str, str]:
        """
        Analyze the risk level of an operation and generate a safety message.
        
        Returns:
            Tuple[risk_level, safety_message]
        """
        risk_level = "low"
        for level, keywords in SafetyVerifier.RISK_LEVELS.items():
            if any(kw in operation.lower() for kw in keywords):
                risk_level = level
                break

        safety_message = f"""
SAFETY CHECK - MCP Operation Request
Operation: {operation}
Risk Level: {risk_level.upper()}
Parameters: {json.dumps(params, indent=2)}

Would you like to:
1. Proceed with the operation
2. Modify parameters
3. Cancel operation

Please respond with the number of your choice (1-3):"""

        return risk_level, safety_message

    @staticmethod
    async def verify_operation(operation: str, params: Dict[str, Any], risk_level: str) -> bool:
        """Verify if an operation should proceed based on its risk level"""
        risk, message = SafetyVerifier.analyze_risk(operation, params)
        
        # Always allow low-risk operations from low-risk servers
        if risk == "low" and risk_level == "low":
            return True

        queue_message(message)
        
        # Get user confirmation before performing further actions
        response = raw_complete_llm("Based on the safety check above, what is your choice (1-3)?")
        
        try:
            choice = int(response.strip())
            return choice == 1
        except (ValueError, TypeError):
            queue_message("Invalid choice. Operation cancelled for safety.")
            return False

class MCPCapabilityManager:
    """Manages MCP server capabilities with safety verification"""
    
    def __init__(self):
        self.servers: Dict[str, Dict[str, Any]] = {}
        self.safety_verifier = SafetyVerifier()
        
    def register_server_capabilities(self, server_name: str, capabilities: Dict[str, Any], risk_level: str):
        """Register server capabilities with risk level"""
        self.servers[server_name] = {
            "capabilities": capabilities,
            "risk_level": risk_level
        }
        
    def find_capability(self, query: str) -> Optional[Tuple[str, str, str, str]]:
        """
        Find a capability across all servers that matches the query.
        Returns (server_name, capability_type, capability_name, risk_level) if found.
        """
        for server_name, server_info in self.servers.items():
            capabilities = server_info["capabilities"]
            risk_level = server_info["risk_level"]
            
            for cap_type in ['tools', 'resources', 'prompts']:
                if cap_type not in capabilities:
                    continue
                    
                for cap in capabilities[cap_type]:
                    if (query.lower() in cap.name.lower() or 
                        (hasattr(cap, 'description') and 
                         query.lower() in cap.description.lower())):
                        return (server_name, cap_type, cap.name, risk_level)
        return None

class TARSMCPClient:
    """MCP client with safety verification"""
    
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.capability_manager = MCPCapabilityManager()
        
    async def connect_to_servers(self, config: Dict[str, Any]):
        """Connect to configured MCP servers"""
        if not config.get('MCP', {}).get('enabled'):
            return
            
        servers = json.loads(config['MCP']['servers'])
        for server_cfg in servers:
            await self.connect_to_server(MCPServerConfig(**server_cfg))
    
    async def connect_to_server(self, config: MCPServerConfig):
        """Connect to an MCP server and discover its capabilities"""
        try:
            params = StdioServerParameters(
                command=config.command,
                args=config.args or [],
                env=config.env,
                cwd=config.working_dir
            )
            
            read_stream, write_stream = await stdio_client(params)
            session = ClientSession(read_stream, write_stream)
            await session.initialize()
            
            self.sessions[config.name] = session
            
            # Discover capabilities
            capabilities = {
                'tools': await session.list_tools(),
                'resources': await session.list_resources(),
                'prompts': await session.list_prompts()
            }
            
            self.capability_manager.register_server_capabilities(
                config.name, 
                capabilities,
                config.risk_level
            )
            
            queue_message(f"Connected to MCP server '{config.name}' with capabilities:")
            for cap_type, caps in capabilities.items():
                queue_message(f"- {cap_type}: {[c.name for c in caps]}")
                
        except Exception as e:
            queue_message(f"Error connecting to MCP server '{config.name}': {e}")

    async def execute_capability(self, query: str, **kwargs) -> Any:
        """Execute a capability with safety verification"""
        capability = self.capability_manager.find_capability(query)
        if not capability:
            return f"No matching capability found for: {query}"
            
        server_name, cap_type, cap_name, risk_level = capability
        session = self.sessions.get(server_name)
        if not session:
            return f"Server '{server_name}' not connected"
            
        try:
            # Verify operation safety before proceeding
            verified = await SafetyVerifier.verify_operation(
                f"{cap_type}:{cap_name}", 
                kwargs,
                risk_level
            )
            
            if not verified:
                return "Operation cancelled by user."
                
            if cap_type == 'tools':
                return await session.call_tool(cap_name, arguments=kwargs)
            elif cap_type == 'resources':
                return await session.read_resource(cap_name.format(**kwargs))
            elif cap_type == 'prompts':
                return await session.get_prompt(cap_name, arguments=kwargs)
                
        except Exception as e:
            return f"Error executing {cap_type} '{cap_name}' on server '{server_name}': {e}"

    async def close(self):
        """Close all server connections"""
        for name, session in self.sessions.items():
            try:
                await session.close()
            except Exception as e:
                queue_message(f"Error closing connection to '{name}': {e}")

# Global MCP client instance
_mcp_client: Optional[TARSMCPClient] = None

async def initialize_mcp():
    """Initialize the global MCP client"""
    global _mcp_client
    config = load_config()
    _mcp_client = TARSMCPClient()
    await _mcp_client.connect_to_servers(config)

def handle_mcp_request(user_input: str, config: Dict[str, Any]) -> str:
    """Handle MCP requests with safety verification"""
    try:
        return asyncio.run(execute_mcp_command(user_input))
    except Exception as e:
        return f"Error processing MCP request: {e}"

async def execute_mcp_command(query: str, **kwargs) -> Any:
    """Execute an MCP command with safety checks"""
    if not _mcp_client:
        return "MCP client not initialized"
    return await _mcp_client.execute_capability(query, **kwargs)