"""Client per le API RomM."""

import requests
from typing import Optional

class RommClient:
    def __init__(self, base_url: str, token: str):
        self.base = base_url.rstrip("/") + "/api"
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def get_roms(self, limit: int = 2000) -> list:
        """Restituisce la lista dei ROM."""
        resp = self.session.get(f"{self.base}/roms", params={"limit": limit})
        resp.raise_for_status()
        data = resp.json()
        return data.get("items", data) if isinstance(data, dict) else data
