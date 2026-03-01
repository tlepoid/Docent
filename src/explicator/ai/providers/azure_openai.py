"""Azure OpenAI provider adapter.

This is the only module in the codebase that imports `openai`.
All Azure OpenAI-specific API details are encapsulated here.
"""

from __future__ import annotations

import json

from explicator.ai.providers.base import AIMessage, AIProvider, AIResponse


class AzureOpenAIProvider(AIProvider):
    """AI provider adapter for Azure OpenAI."""

    def __init__(
        self,
        api_key: str,
        azure_endpoint: str,
        deployment_name: str,
        api_version: str = "2024-02-01",
    ) -> None:
        """Initialise the Azure OpenAI client with endpoint and deployment details."""
        try:
            from openai import AzureOpenAI
        except ImportError as exc:
            raise ImportError(
                "The 'openai' package is required for AzureOpenAIProvider. "
                "Install it with: pip install 'explicator[azure]'"
            ) from exc

        from openai import AzureOpenAI

        self._client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
        )
        self._deployment = deployment_name

    def chat(
        self,
        messages: list[AIMessage],
        tools: list[dict],
        system: str | None = None,
    ) -> AIResponse:
        """Send a conversation to Azure OpenAI and return a normalised response."""
        oai_messages = []
        if system:
            oai_messages.append({"role": "system", "content": system})
        oai_messages.extend([self._to_oai_message(m) for m in messages])

        response = self._client.chat.completions.create(
            model=self._deployment,
            messages=oai_messages,
            tools=tools,  # OpenAI format matches our definitions directly
            tool_choice="auto",
        )

        choice = response.choices[0]
        msg = choice.message

        tool_calls: list[dict] = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append(
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": json.loads(tc.function.arguments),
                    }
                )

        return AIResponse(
            message=AIMessage(
                role="assistant",
                content=msg.content,
                tool_calls=tool_calls or None,
            ),
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason or "stop",
        )

    @staticmethod
    def _to_oai_message(msg: AIMessage) -> dict:
        if msg.role == "tool":
            return {
                "role": "tool",
                "tool_call_id": msg.tool_call_id,
                "name": msg.name or "",
                "content": msg.content or "",
            }
        if msg.role == "assistant" and msg.tool_calls:
            oai_tool_calls = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc["arguments"]),
                    },
                }
                for tc in msg.tool_calls
            ]
            return {
                "role": "assistant",
                "content": msg.content,
                "tool_calls": oai_tool_calls,
            }
        return {"role": msg.role, "content": msg.content or ""}
