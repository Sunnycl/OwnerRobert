import os
from typing import List
import httpx
from duckduckgo_search import DDGS


class SearchService:
    def __init__(self) -> None:
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")

    async def quick_snippets(self, query: str, k: int = 5) -> List[str]:
        if self.tavily_api_key:
            try:
                return await self._tavily_search(query, k)
            except Exception:
                pass
        return self._duckduckgo_search(query, k)

    async def _tavily_search(self, query: str, k: int) -> List[str]:
        url = "https://api.tavily.com/search"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.tavily_api_key}"}
        payload = {"query": query, "max_results": k}
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
        results = data.get("results") or data.get("organic_results") or []
        snippets: List[str] = []
        for item in results[:k]:
            title = item.get("title") or item.get("source") or ""
            snippet = item.get("content") or item.get("snippet") or ""
            url_item = item.get("url") or item.get("link") or ""
            if snippet:
                snippets.append(f"{title}: {snippet}\nSource: {url_item}")
        return snippets

    def _duckduckgo_search(self, query: str, k: int) -> List[str]:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=k):
                title = r.get("title") or ""
                snippet = r.get("body") or r.get("snippet") or ""
                link = r.get("href") or r.get("link") or ""
                if snippet:
                    results.append(f"{title}: {snippet}\nSource: {link}")
        return results
