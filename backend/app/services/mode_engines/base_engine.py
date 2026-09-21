"""Shared contract for mode engines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseModeEngine(ABC):
    """Process mode-specific context after routing and base data retrieval."""

    mode: str

    @abstractmethod
    async def process(
        self,
        *,
        request_message: str,
        query: dict[str, Any],
        base_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Return mode-specific structured context for the shared LLM layer."""
        raise NotImplementedError
