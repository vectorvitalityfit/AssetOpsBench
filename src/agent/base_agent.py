"""Base Agent implementation for open-source agents."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from llm import LLMBackend
from workflow.executor import Executor
from workflow.models import PlanStep, StepResult

_log = logging.getLogger(__name__)


class BaseAgent:
    """A foundational class for standalone, open-source agents.

    This class uses composition to leverage the existing `Executor` for MCP stdio
    connections, tool discovery, and routing. Derived agents (e.g., ReAct, Claude)
    should inherit from this class and implement their specific reasoning loops.
    """

    def __init__(
        self,
        llm: LLMBackend,
        server_paths: dict[str, Path | str] | None = None,
    ) -> None:
        """Initialize the BaseAgent.

        Args:
            llm: The LLM backend to use for reasoning.
            server_paths: Optional dictionary overriding default MCP server specs.
        """
        self._llm = llm
        # Compose the Executor to handle complex MCP stdio connections cleanly
        self._executor = Executor(llm, server_paths)
        
        # Maintain local state for step-by-step tool execution context
        self._context: dict[int, StepResult] = {}
        self._step_counter = 0

    async def get_available_tools(self) -> dict[str, str]:
        """Discover and format available tools from all registered MCP servers.

        Returns:
            A dictionary mapping server names to their formatted tool signatures.
        """
        _log.info("Discovering tools via MCP Executor...")
        return await self._executor.get_agent_descriptions()

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        tool_args: dict[str, Any],
        task_description: str = "Standalone tool execution",
    ) -> StepResult:
        """Execute a specific tool on a target MCP server.

        Wraps the workflow Executor to safely route the tool call and manage state.

        Args:
            server_name: The name of the MCP server (e.g., 'IoTAgent').
            tool_name: The exact name of the tool to execute.
            tool_args: The arguments to pass to the tool.
            task_description: An optional description of the task for logging.

        Returns:
            A StepResult containing the tool's response or error.
        """
        self._step_counter += 1
        
        # Package the tool call into a PlanStep so the Executor can process it natively
        step = PlanStep(
            step_number=self._step_counter,
            task=task_description,
            agent=server_name,
            tool=tool_name,
            tool_args=tool_args,
            dependencies=[],
            expected_output="",
        )

        _log.info("BaseAgent routing tool call: %s.%s", server_name, tool_name)
        
        # Execute the step using the underlying executor
        result = await self._executor.execute_step(
            step=step,
            context=self._context,
            question="Agent execution loop"
        )
        
        # Store context for potential future reference in multi-step reasoning
        self._context[self._step_counter] = result
        return result

    async def run(self, prompt: str) -> str:
        """Core reasoning and execution loop.

        Must be implemented by derived classes (e.g., ClaudeAgent, ReActAgent).
        """
        raise NotImplementedError("Derived agents must implement the run() method.")