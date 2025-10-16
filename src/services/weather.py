from __future__ import annotations

import httpx
from dataclasses import dataclass


@dataclass
class Weather:
	temp_c: float
	description: str
	icon: str | None = None


class WeatherService:
	def __init__(self, base_url: str, api_key: str | None) -> None:
		self.base_url = base_url.rstrip("/")
		self.api_key = api_key

	async def get_current_by_city(self, city: str, lang: str = "ru", units: str = "metric") -> Weather | None:
		if not self.api_key:
			return None
			
		params = {"q": city, "appid": self.api_key, "lang": lang, "units": units}
		async with httpx.AsyncClient(timeout=10) as client:
			resp = await client.get(f"{self.base_url}/weather", params=params)
			resp.raise_for_status()
			data = resp.json()
			return Weather(
				temp_c=float(data["main"]["temp"]),
				description=str(data["weather"][0]["description"]).capitalize(),
				icon=data["weather"][0].get("icon"),
			)
