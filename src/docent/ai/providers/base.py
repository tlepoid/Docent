"""Abstract AI provider interface.

All provider adapters implement this interface. The orchestration layer
only ever speaks AIMessage / AIResponse — never provider-specific types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AIMessage:
    """A single message in a conversation, normalised across all providers."""

    role: str  # "system" | "user" | "assistant" | "tool"
    content: Optional[str] = None
    tool_calls: Optional[list[dict]] = None  # [{id, name, arguments}]
    tool_call_id: Optional[str] = None       # for role="tool" responses
    name: Optional[str] = None               # tool name for role="tool"


@dataclass
class AIResponse:
    """Normalised response from an AI provider."""

    message: AIMessage
    tool_calls: list[dict] = field(default_factory=list)  # [{id, name, arguments: dict}]
    finish_reason: str = "stop"


class AIProvider(ABC):
    """
    Abstract base for AI provider adapters.

    Each concrete implementation is responsible for translating to and from
    its provider's wire format. The orchestration layer must never contain
    provider-specific code.
    """

    @abstractmethod
    def chat(
        self,
        messages: list[AIMessage],
        tools: list[dict],
        system: Optional[str] = None,
    ) -> AIResponse:
        """
        Send a conversation to the provider and return a normalised response.

        Args:
            messages: Conversation history in normalised AIMessage format.
            tools: Tool definitions in OpenAI function-calling JSON schema format.
            system: Optional system prompt (passed separately, not as a message).

        Returns:
            Normalised AIResponse. Check finish_reason and tool_calls to determine
            whether the model wants to invoke a tool or has finished responding.
        """
