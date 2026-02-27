"""Anthropic Claude provider adapter.

This is the only module in the codebase that imports `anthropic`.
All Claude-specific API details are encapsulated here.
"""

from __future__ import annotations

from typing import Any, Optional

from .base import AIMessage, AIProvider, AIResponse


class ClaudeProvider(AIProvider):
    """AI provider adapter for Anthropic's Claude API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-6",
    ) -> None:
        try:
            import anthropic
        except ImportError as exc:
            raise ImportError(
                "The 'anthropic' package is required for ClaudeProvider. "
                "Install it with: pip install 'docent[claude]'"
            ) from exc

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def chat(
        self,
        messages: list[AIMessage],
        tools: list[dict],
        system: Optional[str] = None,
    ) -> AIResponse:
        anthropic_messages = [self._to_anthropic_message(m) for m in messages]
        anthropic_tools = [self._to_anthropic_tool(t) for t in tools]

        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": 4096,
            "messages": anthropic_messages,
            "tools": anthropic_tools,
        }
        if system:
            kwargs["system"] = system

        response = self._client.messages.create(**kwargs)

        tool_calls: list[dict] = []
        text_content: Optional[str] = None

        for block in response.content:
            if block.type == "tool_use":
                tool_calls.append(
                    {"id": block.id, "name": block.name, "arguments": block.input}
                )
            elif block.type == "text":
                text_content = block.text

        finish_reason = "tool_calls" if tool_calls else "stop"

        return AIResponse(
            message=AIMessage(
                role="assistant",
                content=text_content,
                tool_calls=tool_calls or None,
            ),
            tool_calls=tool_calls,
            finish_reason=finish_reason,
        )

    @staticmethod
    def _to_anthropic_message(msg: AIMessage) -> dict:
        if msg.role == "tool":
            return {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": msg.tool_call_id,
                        "content": msg.content or "",
                    }
                ],
            }
        if msg.role == "assistant" and msg.tool_calls:
            content: list[dict] = []
            if msg.content:
                content.append({"type": "text", "text": msg.content})
            for tc in msg.tool_calls:
                content.append(
                    {
                        "type": "tool_use",
                        "id": tc["id"],
                        "name": tc["name"],
                        "input": tc["arguments"],
                    }
                )
            return {"role": "assistant", "content": content}
        return {"role": msg.role, "content": msg.content or ""}

    @staticmethod
    def _to_anthropic_tool(tool: dict) -> dict:
        fn = tool["function"]
        return {
            "name": fn["name"],
            "description": fn["description"],
            "input_schema": fn["parameters"],
        }
