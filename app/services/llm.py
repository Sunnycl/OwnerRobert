import os
from typing import Any, Dict, List
from openai import AsyncOpenAI


class LLMService:
    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set in environment")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = os.getenv("MODEL", "gpt-4o-mini")

    async def generate_reply(
        self,
        system_prompt: str,
        history: List[Dict[str, str]],
        user_message: str,
        context_snippets: str = "",
    ) -> str:
        messages: List[Dict[str, Any]] = []
        messages.append({"role": "system", "content": system_prompt})
        if context_snippets:
            messages.append({
                "role": "system",
                "content": f"Additional context from web/search (may be noisy):\n{context_snippets}",
            })
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        completion = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.6,
        )
        return completion.choices[0].message.content or ""
