"""
module_mcp.py
Core MCP implementation with safety protocols, feedback support, and resource management.
"""

import asyncio
import json
import sys
from typing import Dict, Any, Optional, List, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import AsyncExitStack
from asyncio.subprocess import Process
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from modules.module_messageQue import queue_message
from modules.module_config import load_config
from modules.module_llm import raw_complete_llm
from enum import Enum

# Define feedback types
class FeedbackType(Enum):
    VALIDATION = "validation"
    PROGRESS = "progress"
    ERROR = "error"
    SUCCESS = "success"
    WARNING = "warning"

@dataclass
class OperationFeedback:
    type: FeedbackType
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

@dataclass
class MCPServerConfig:
    name: str
    command: str
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    working_dir: Optional[str] = None
    script_type: str = "python"
    risk_level: str = "medium"
    requires_confirmation: bool = True
    allowed_directories: Optional[List[str]] = None

class SafetyVerifier:
    RISK_LEVELS = {
        "low": ["read", "list", "get", "query", "view"],
        "medium": ["write", "update", "modify", "send", "create"],
        "high": ["delete", "remove", "execute", "run", "system"]
    }

    @staticmethod
    async def verify_operation(
        operation: str,
        params: Dict[str, Any],
        risk_level: str,
        user: str = "unknown"
    ) -> Tuple[bool, str]:
        # Auto-approve low-risk operations on low-risk servers
        if risk_level == "low" and any(kw in operation.lower() for kw in SafetyVerifier.RISK_LEVELS["low"]):
            return True, "Auto-approved low-risk operation"

        # Determine operation risk
        operation_risk = "low"
        for level, keywords in SafetyVerifier.RISK_LEVELS.items():
            if any(kw in operation.lower() for kw in keywords):
                operation_risk = level
                break

        current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        safety_message = f"""
SAFETY CHECK - MCP Operation Request
Time: {current_time} UTC
User: {user}
Operation: {operation}
Risk Level: {operation_risk.upper()}
Server Risk Level: {risk_level.upper()}
Parameters: {json.dumps(params, indent=2)}

Would you like to:
1. Proceed with the operation
2. Show preview (if available)
3. Cancel operation

Please respond with the number of your choice (1-3): """

        queue_message(safety_message)
        response = raw_complete_llm("Based on the safety check above, what is your choice (1-3)?")

        try:
            choice = int(response.strip())
            if choice == 2:
                preview = await SafetyVerifier._generate_preview(operation, params)
                queue_message(f"Preview of operation:\n{preview}")
                queue_message("\nWould you like to proceed now? (1: Yes, 3: No): ")
                response = raw_complete_llm("Enter your choice (1 or 3): ")
                choice = int(response.strip())

            return (choice == 1, "User approved" if choice == 1 else "User cancelled")

        except (ValueError, TypeError):
            return False, "Invalid choice received"

    @staticmethod
    async def _generate_preview(operation: str, params: Dict[str, Any]) -> str:
        preview = ["Operation Preview:"]
        preview.append(f"- Operation: {operation}")
        preview.append("- Parameters:")
        for key, value in params.items():
            preview.append(f"  {key}: {value}")
        preview.append("\nPotential Effects:")

        if "write" in operation.lower() or "create" in operation.lower():
            preview.append("- Will create or modify existing content")
            if "content" in params:
                preview.append("- Content to be written:")
                preview.append(f"```\n{params['content']}\n```")
        elif "delete" in operation.lower():
            preview.append("- Will permanently remove content")
            preview.append("- This operation cannot be undone")
        elif "execute" in operation.lower():
            preview.append("- Will execute commands or code")
            preview.append("- May have system-level effects")

        return "\n".join(preview)

class MCPClient:
    def __init__(self):
        self.exit_stack = AsyncExitStack()
        self.sessions: Dict[str, ClientSession] = {}
        self.server_processes: Dict[str, Process] = {}
        self.conversation_context: Dict[str, List[Dict[str, str]]] = {}
        self.server_configs: Dict[str, MCPServerConfig] = {}
        self.feedback_handlers: Dict[FeedbackType, List[Callable]] = {
            feedback_type: [] for feedback_type in FeedbackType
        }

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()

    async def cleanup(self):
        try:
            for name, session in self.sessions.items():
                try:
                    await session.close()
                except Exception as e:
                    queue_message(f"Warning: Error closing session {name}: {e}")

            for name, process in self.server_processes.items():
                try:
                    process.terminate()
                    await process.wait()
                except Exception as e:
                    queue_message(f"Warning: Error terminating server {name}: {e}")

            await self.exit_stack.aclose()

        except Exception as e:
            queue_message(f"Error during cleanup: {e}")

    def register_feedback_handler(self, feedback_type: FeedbackType, handler: Callable):
        """Register a handler for a specific feedback type."""
        self.feedback_handlers[feedback_type].append(handler)

    async def _handle_feedback(self, feedback: OperationFeedback):
        """Process feedback through registered handlers."""
        handlers = self.feedback_handlers.get(feedback.type, [])
        for handler in handlers:
            try:
                await handler(feedback)
            except Exception as e:
                queue_message(f"Error in feedback handler: {e}")

    async def connect_to_server(self, config: MCPServerConfig) -> bool:
        try:
            params = StdioServerParameters(
                command=config.command,
                args=config.args or [],
                env=config.env,
                cwd=config.working_dir
            )

            read_stream, write_stream = await stdio_client(params)
            session = await self.exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
            await session.initialize()
            self.sessions[config.name] = session
            self.server_configs[config.name] = config

            capabilities = await self._get_server_capabilities(session)
            queue_message(f"Connected to MCP server '{config.name}' (Risk Level: {config.risk_level})")

            return True

        except Exception as e:
            queue_message(f"Error connecting to server {config.name}: {e}")
            return False

    async def _get_server_capabilities(self, session: ClientSession) -> Dict[str, Any]:
        try:
            return {
                'tools': await session.list_tools(),
                'resources': await session.list_resources(),
                'prompts': await session.list_prompts()
            }
        except Exception as e:
            queue_message(f"Error getting server capabilities: {e}")
            return {}

    async def process_query(self, query: str, server_name: str, **kwargs) -> Any:
        try:
            session = self.sessions.get(server_name)
            config = self.server_configs.get(server_name)
            if not session or not config:
                raise ValueError(f"No connection to server: {server_name}")

            # Validation feedback
            await self._handle_feedback(OperationFeedback(
                type=FeedbackType.VALIDATION,
                message=f"Validating operation: {query}",
                data={"query": query, "params": kwargs}
            ))

            # Safety verification using the SafetyVerifier
            approved, reason = await SafetyVerifier.verify_operation(query, kwargs, config.risk_level)

            if not approved:
                await self._handle_feedback(OperationFeedback(
                    type=FeedbackType.WARNING,
                    message=f"Operation not approved: {reason}",
                    data={"reason": reason}
                ))
                return f"Operation cancelled: {reason}"

            # Progress feedback before execution
            await self._handle_feedback(OperationFeedback(
                type=FeedbackType.PROGRESS,
                message="Starting operation execution",
                data={"status": "starting"}
            ))

            # Execute capability
            result = await self._execute_capability(session, query, **kwargs)

            # Success feedback after execution
            await self._handle_feedback(OperationFeedback(
                type=FeedbackType.SUCCESS,
                message="Operation completed successfully",
                data={"result": result}
            ))

            # Log to conversation context
            if server_name not in self.conversation_context:
                self.conversation_context[server_name] = []
            self.conversation_context[server_name].append({
                "query": query,
                "timestamp": datetime.utcnow().isoformat(),
                "parameters": kwargs,
                "result": result
            })

            return result

        except Exception as e:
            error_msg = f"Error processing query: {e}"
            await self._handle_feedback(OperationFeedback(
                type=FeedbackType.ERROR,
                message=error_msg,
                data={"error": str(e)}
            ))
            queue_message(error_msg)
            return error_msg

    async def _execute_capability(self, session: ClientSession, query: str, **kwargs) -> Any:
        try:
            capabilities = await self._get_server_capabilities(session)
            for cap_type in ['tools', 'resources', 'prompts']:
                for cap in capabilities.get(cap_type, []):
                    if self._matches_capability(query, cap):
                        if cap_type == 'tools':
                            return await session.call_tool(cap.name, arguments=kwargs)
                        elif cap_type == 'resources':
                            return await session.read_resource(cap.name.format(**kwargs))
                        elif cap_type == 'prompts':
                            return await session.get_prompt(cap.name, arguments=kwargs)

            raise ValueError(f"No matching capability found for query: {query}")

        except Exception as e:
            raise Exception(f"Error executing capability: {e}")

    def _matches_capability(self, query: str, capability: Any) -> bool:
        query = query.lower()
        return (
            query in capability.name.lower() or
            (hasattr(capability, 'description') and query in capability.description.lower())
        )

# Global client instance
_mcp_client: Optional[MCPClient] = None

async def initialize_mcp(username: str = "unknown"):
    global _mcp_client
    try:
        config = load_config()
        _mcp_client = MCPClient()
        await _mcp_client.__aenter__()
        servers = json.loads(config['MCP'].get('servers', '[]'))
        for server_cfg in servers:
            await _mcp_client.connect_to_server(MCPServerConfig(**server_cfg))
    except Exception as e:
        queue_message(f"Error initializing MCP: {e}")
        if _mcp_client:
            await _mcp_client.__aexit__(type(e), e, e.__traceback__)
        _mcp_client = None

async def cleanup_mcp():
    global _mcp_client
    if _mcp_client:
        await _mcp_client.__aexit__(None, None, None)
        _mcp_client = None

def handle_mcp_request(query: str, config: Dict[str, Any]) -> str:
    try:
        return asyncio.run(_process_mcp_request(query, config))
    except Exception as e:
        return f"Error handling MCP request: {e}"

async def _process_mcp_request(query: str, config: Dict[str, Any]) -> Any:
    if not _mcp_client:
        return "MCP client not initialized"
    try:
        for server_name in _mcp_client.sessions:
            result = await _mcp_client.process_query(query, server_name)
            if result and "Error" not in str(result):
                return result
        return "No server could handle the query"
    except Exception as e:
        return f"Error processing request: {e}"

import atexit
atexit.register(lambda: asyncio.run(cleanup_mcp()))