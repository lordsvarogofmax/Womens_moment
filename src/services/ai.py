from __future__ import annotations

from dataclasses import dataclass
import logging
import httpx


logger = logging.getLogger(__name__)


@dataclass
class AIResponse:
	text: str


class OpenRouterClient:
	def __init__(self, base_url: str, api_key: str | None, model: str, *, referer: str | None = None, title: str = "Womens Moment TG Bot") -> None:
		self.base_url = base_url.rstrip("/")
		self.api_key = api_key
		self.model = model
		self.referer = referer
		self.title = title

	async def chat(self, system_prompt: str, user_prompt: str) -> AIResponse | None:
		if not self.api_key:
			logger.warning("OpenRouter API key is not set; skipping AI call")
			return None
		headers = {
			"Authorization": f"Bearer {self.api_key}",
			"Content-Type": "application/json",
		}
		if self.referer:
			headers["HTTP-Referer"] = self.referer
		headers["X-Title"] = self.title
		payload = {
			"model": self.model,
			"messages": [
				{"role": "system", "content": system_prompt},
				{"role": "user", "content": user_prompt},
			],
		}
		try:
			async with httpx.AsyncClient(timeout=30) as client:
				resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
				resp.raise_for_status()
				data = resp.json()
				text = data["choices"][0]["message"]["content"].strip()
				logger.info("AI response received (len=%d)", len(text))
				return AIResponse(text=text)
		except httpx.HTTPError:
			logger.exception("OpenRouter call failed")
			return None

