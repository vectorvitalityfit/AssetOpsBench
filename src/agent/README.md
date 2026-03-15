# AssetOpsBench Standalone Agents

This directory contains standalone, open-source agents that interface natively with the AssetOpsBench Model Context Protocol (MCP) environment.

## The `BaseAgent` Architecture

To avoid duplicating the complex `stdio` connection logic required by the MCP architecture, standalone agents in this directory inherit from the `BaseAgent` class. 

### Composition over Inheritance
The `BaseAgent` answers the architectural challenge of tool routing by using **composition**. Rather than inheriting from the `workflow.Executor` (which is tightly coupled to the DAG-based `PlanStep` generation), the `BaseAgent` instantiates an `Executor` under the hood. 

This allows the agent to:
1. Dynamically discover all tools using `get_available_tools()`.
2. Seamlessly route tool executions to the correct MCP servers using `call_tool()`.
3. Retain complete control over its own autonomous reasoning loop (e.g., ReAct, Tool-Calling, or custom heuristics).

## How to Add a New Open-Source Agent

To add a new agent (e.g., a Claude `claude_code.py` variant or a standard ReAct agent):

1. **Create your file** in `src/agent/` (e.g., `my_custom_agent.py`).
2. **Inherit** from `BaseAgent`.
3. **Implement the `run(self, prompt: str)` method**:
   - Call `await self.get_available_tools()` to inject the MCP tool schemas into your LLM's system prompt.
   - Parse your LLM's output to detect required tool calls.
   - Use `await self.call_tool(server_name, tool_name, args)` to execute the tools safely.
   - Feed the `StepResult.response` back into your LLM until it reaches a final answer.