"""Client per le API RomM."""

import requests
from pathlib import Path
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

    def download_rom(self, rom_id: int, dest_path: Path) -> None:
        """Scarica una ROM."""
        # L'endpoint per scaricare il contenuto della ROM
        resp = self.session.get(f"{self.base}/roms/{rom_id}/content", stream=True)
        resp.raise_for_status()
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
