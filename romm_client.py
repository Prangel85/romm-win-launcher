"""Client per le API RomM."""

import requests
from pathlib import Path
from typing import Optional
from urllib.parse import quote

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

    def download_rom(self, rom_id: int, filename: str, dest_path: Path) -> None:
        """Scarica una ROM."""
        safe_name = quote(filename, safe="")
        url = f"{self.base}/roms/{rom_id}/content/{safe_name}"
        resp = self.session.get(url, stream=True)
        resp.raise_for_status()
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    def download_file(self, url: str, dest_path: Path) -> None:
        """Scarica un file generico (cover, manuale, ecc.)."""
        # Se l'URL è relativo, lo rende assoluto
        if url.startswith("/"):
            base = self.base.replace("/api", "")
            url = base + url
        resp = self.session.get(url, stream=True)
        resp.raise_for_status()
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
