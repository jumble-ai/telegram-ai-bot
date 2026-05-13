from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


class SearchError(RuntimeError):
    """Raised when web search cannot return usable results."""


@dataclass(frozen=True, slots=True)
class SearchResponse:
    """Tavily search response."""

    raw_data: dict[str, Any]


@dataclass(frozen=True, slots=True)
class TavilySearchClient:
    """Minimal async client for Tavily web search."""

    api_key: str
    max_results: int = 3
    base_url: str = "https://api.tavily.com/search"

    async def search(self, query: str) -> SearchResponse:
        """Search the web and return a compact response."""
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "topic": "general",
            "max_results": self.max_results,
            "include_answer": "basic",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(self.base_url, json=payload)

        if response.status_code >= 400:
            raise SearchError(
                f"Tavily request failed with status {response.status_code}."
            )

        return self._parse_response(response.json())

    @staticmethod
    def _parse_response(data: dict[str, Any]) -> SearchResponse:
        raw_results = data.get("results")
        if not isinstance(raw_results, list):
            raise SearchError("Tavily response does not contain results.")

        if not raw_results:
            raise SearchError("Tavily response contains no usable results.")

        return SearchResponse(raw_data=data)
