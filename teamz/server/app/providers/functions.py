"""Function calling shim for non-OpenAI models."""

from __future__ import annotations

import json
import re
from typing import Any, AsyncIterator, Dict, List, Optional, Callable

from ..models import FunctionCallingShimConfig
from .base import StreamEvent


class FunctionCall:
    """Represents a function call from the model."""
    def __init__(self, name: str, arguments: Dict[str, Any], call_id: Optional[str] = None):
        self.name = name
        self.arguments = arguments
        self.call_id = call_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "arguments": self.arguments,
            "call_id": self.call_id,
        }


class FunctionCallingShim:
    """Shim to enable function calling on models that don't natively support it."""

    def __init__(self, config: Optional[FunctionCallingShimConfig] = None) -> None:
        self.config = config or FunctionCallingShimConfig()
        self._functions: Dict[str, Dict[str, Any]] = {}
        self._handlers: Dict[str, Callable] = {}

    def register_function(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Optional[Callable] = None,
    ) -> None:
        """Register a function that can be called."""
        self._functions[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
        }
        if handler:
            self._handlers[name] = handler

    def get_function_definitions(self) -> List[Dict[str, Any]]:
        """Get function definitions in OpenAI format."""
        return [
            {
                "type": "function",
                "function": func,
            }
            for func in self._functions.values()
        ]

    def get_tools_format(self) -> List[Dict[str, Any]]:
        """Get tools format (OpenAI compatible)."""
        return self.get_function_definitions()

    def inject_functions_prompt(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Inject function definitions into system prompt for models without native support."""
        if not self._functions:
            return messages

        # Build function descriptions
        func_descriptions = []
        for func in self._functions.values():
            params = func["parameters"]
            param_desc = []
            for prop_name, prop_schema in params.get("properties", {}).items():
                prop_type = prop_schema.get("type", "string")
                prop_desc = prop_schema.get("description", "")
                required = prop_name in params.get("required", [])
                req_str = " (required)" if required else " (optional)"
                param_desc.append(f"  - {prop_name}: {prop_type}{req_str} - {prop_desc}")

            func_descriptions.append(
                f"Function: {func['name']}\n"
                f"Description: {func['description']}\n"
                f"Parameters:\n" + "\n".join(param_desc)
            )

        system_prompt = (
            "You have access to the following functions. To call a function, respond with a JSON object:\n"
            "```json\n"
            "{\n"
            '  "function_call": {\n'
            '    "name": "function_name",\n'
            '    "arguments": { ... }\n'
            "  }\n"
            "}\n"
            "```\n\n"
            "Available functions:\n\n" + "\n\n".join(func_descriptions)
        )

        # Find or create system message
        new_messages = []
        system_added = False
        for msg in messages:
            if msg.get("role") == "system":
                new_messages.append({
                    "role": "system",
                    "content": msg.get("content", "") + "\n\n" + system_prompt
                })
                system_added = True
            else:
                new_messages.append(msg)

        if not system_added:
            new_messages.insert(0, {"role": "system", "content": system_prompt})

        return new_messages

    def extract_function_calls(self, response_text: str) -> List[FunctionCall]:
        """Extract function calls from model response."""
        calls = []

        # Try to find JSON with function_call
        json_patterns = [
            r'```json\s*(\{.*?"function_call".*?\})\s*```',
            r'(\{"function_call"\s*:\s*\{.*?\}\})',
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, response_text, re.DOTALL)
            for match in matches:
                try:
                    data = json.loads(match)
                    fc = data.get("function_call")
                    if fc:
                        calls.append(FunctionCall(
                            name=fc.get("name", ""),
                            arguments=fc.get("arguments", {}),
                        ))
                except json.JSONDecodeError:
                    continue

        # Also try to find tool_calls format (OpenAI style)
        tool_calls_pattern = r'"tool_calls"\s*:\s*(\[.*?\])'
        matches = re.findall(tool_calls_pattern, response_text, re.DOTALL)
        for match in matches:
            try:
                tool_calls = json.loads(match)
                for tc in tool_calls:
                    if tc.get("type") == "function":
                        func = tc.get("function", {})
                        args = func.get("arguments", {})
                        if isinstance(args, str):
                            args = json.loads(args)
                        calls.append(FunctionCall(
                            name=func.get("name", ""),
                            arguments=args,
                            call_id=tc.get("id"),
                        ))
            except json.JSONDecodeError:
                continue

        return calls

    async def execute_function_calls(self, calls: List[FunctionCall]) -> List[Dict[str, Any]]:
        """Execute function calls and return results."""
        results = []
        for call in calls:
            handler = self._handlers.get(call.name)
            if handler:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(**call.arguments)
                    else:
                        result = handler(**call.arguments)
                    results.append({
                        "call_id": call.call_id,
                        "name": call.name,
                        "result": result,
                        "success": True,
                    })
                except Exception as e:
                    results.append({
                        "call_id": call.call_id,
                        "name": call.name,
                        "error": str(e),
                        "success": False,
                    })
            else:
                results.append({
                    "call_id": call.call_id,
                    "name": call.name,
                    "error": f"No handler for function: {call.name}",
                    "success": False,
                })
        return results

    def format_function_results(self, results: List[Dict[str, Any]]) -> str:
        """Format function results for model consumption."""
        if not results:
            return ""

        formatted = "Function results:\n"
        for r in results:
            if r["success"]:
                formatted += f'- {r["name"]}: {json.dumps(r["result"])})\n'
            else:
                formatted += f'- {r["name"]} ERROR: {r["error"]}\n'
        return formatted


async def process_with_functions(
    shim: FunctionCallingShim,
    provider_stream: AsyncIterator[StreamEvent],
    max_iterations: int = 5,
) -> AsyncIterator[StreamEvent]:
    """
    Process a stream with function calling support.
    Handles the loop of: model -> function calls -> results -> model.
    """
    iteration = 0
    accumulated_text = ""
    function_calls_made = False

    async for event in provider_stream:
        if event.type == "delta":
            accumulated_text += event.data.get("delta", "")
            yield event
        elif event.type == "done":
            # Check for function calls in the final response
            calls = shim.extract_function_calls(accumulated_text)
            if calls and iteration < max_iterations:
                function_calls_made = True
                iteration += 1

                # Execute function calls
                results = await shim.execute_function_calls(calls)

                # Yield function call events
                for call in calls:
                    yield StreamEvent("function_call", call.to_dict())

                # Yield function result events
                for result in results:
                    yield StreamEvent("function_result", result)

                # Format results for next iteration
                results_text = shim.format_function_results(results)

                # We can't actually continue the stream here without provider support
                # This would require re-sending to the provider with results
                # For now, yield a special event indicating function calls were made
                yield StreamEvent("function_loop", {
                    "calls": [c.to_dict() for c in calls],
                    "results": results,
                    "iteration": iteration,
                })
            else:
                yield event
        else:
            yield event


# Provider-specific function calling adapters
class OllamaFunctionAdapter:
    """Adapter for Ollama's function calling format."""

    @staticmethod
    def format_tools(functions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert to Ollama tools format."""
        return [
            {
                "type": "function",
                "function": f["function"],
            }
            for f in functions
        ]

    @staticmethod
    def extract_calls(response: Dict[str, Any]) -> List[FunctionCall]:
        """Extract function calls from Ollama response."""
        calls = []
        message = response.get("message", {})
        tool_calls = message.get("tool_calls", [])
        for tc in tool_calls:
            if tc.get("type") == "function":
                func = tc.get("function", {})
                args = func.get("arguments", {})
                if isinstance(args, str):
                    args = json.loads(args)
                calls.append(FunctionCall(
                    name=func.get("name", ""),
                    arguments=args,
                    call_id=tc.get("id"),
                ))
        return calls


class VLLMFunctionAdapter:
    """Adapter for vLLM's function calling format (OpenAI compatible)."""

    @staticmethod
    def format_tools(functions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """vLLM uses OpenAI-compatible format."""
        return functions

    @staticmethod
    def extract_calls(response: Dict[str, Any]) -> List[FunctionCall]:
        """Extract function calls from vLLM response."""
        calls = []
        choices = response.get("choices", [])
        for choice in choices:
            message = choice.get("message", {})
            tool_calls = message.get("tool_calls", [])
            for tc in tool_calls:
                if tc.get("type") == "function":
                    func = tc.get("function", {})
                    args = func.get("arguments", {})
                    if isinstance(args, str):
                        args = json.loads(args)
                    calls.append(FunctionCall(
                        name=func.get("name", ""),
                        arguments=args,
                        call_id=tc.get("id"),
                    ))
        return calls


class AnthropicFunctionAdapter:
    """Adapter for Anthropic's function calling format."""

    @staticmethod
    def format_tools(functions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert to Anthropic tools format."""
        return [
            {
                "name": f["function"]["name"],
                "description": f["function"]["description"],
                "input_schema": f["function"]["parameters"],
            }
            for f in functions
        ]

    @staticmethod
    def extract_calls(response: Dict[str, Any]) -> List[FunctionCall]:
        """Extract function calls from Anthropic response."""
        calls = []
        content = response.get("content", [])
        for block in content:
            if block.get("type") == "tool_use":
                calls.append(FunctionCall(
                    name=block.get("name", ""),
                    arguments=block.get("input", {}),
                    call_id=block.get("id"),
                ))
        return calls


def get_function_adapter(provider: str):
    """Get the appropriate function adapter for a provider."""
    adapters = {
        "ollama": OllamaFunctionAdapter,
        "vllm": VLLMFunctionAdapter,
        "anthropic": AnthropicFunctionAdapter,
    }
    return adapters.get(provider, VLLMFunctionAdapter)  # Default to OpenAI-compatible