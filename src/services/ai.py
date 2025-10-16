from __future__ import annotations

from dataclasses import dataclass
import httpx


@dataclass
class AIResponse:
	text: str


class OpenRouterClient:
	def __init__(self, base_url: str, api_key: str | None, model: str) -> None:
		self.base_url = base_url.rstrip("/")
		self.api_key = api_key
		self.model = model

	async def chat(self, system_prompt: str, user_prompt: str) -> AIResponse | None:
		if not self.api_key:
			return None
		headers = {
			"Authorization": f"Bearer {self.api_key}",
			"Content-Type": "application/json",
			"HTTP-Referer": "https://happy-girls.onrender.com",
			"X-Title": "Womens Moment TG Bot",
		}
		payload = {
			"model": self.model,
			"messages": [
				{"role": "system", "content": system_prompt},
				{"role": "user", "content": user_prompt},
			],
		}
		async with httpx.AsyncClient(timeout=30) as client:
			resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
			resp.raise_for_status()
			data = resp.json()
			text = data["choices"][0]["message"]["content"].strip()
			return AIResponse(text=text)
