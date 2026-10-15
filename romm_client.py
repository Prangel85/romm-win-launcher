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
        resp = self.session.get(f"{self.base}/roms", params={"limit": limit})
        resp.raise_for_status()
        data = resp.json()
        return data.get("items", data) if isinstance(data, dict) else data

    def download_rom(self, rom_id: int, filename: str, dest_path: Path) -> None:
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

    def get_saves(self, rom_id: Optional[int] = None) -> list:
        params = {"rom_id": rom_id} if rom_id else {}
        resp = self.session.get(f"{self.base}/saves", params=params)
        resp.raise_for_status()
        data = resp.json()
        return data.get("items", data) if isinstance(data, dict) else data

    def get_states(self, rom_id: Optional[int] = None) -> list:
        params = {"rom_id": rom_id} if rom_id else {}
        resp = self.session.get(f"{self.base}/states", params=params)
        resp.raise_for_status()
        data = resp.json()
        return data.get("items", data) if isinstance(data, dict) else data

    def download_save(self, save_id: int, dest_path: Path) -> None:
        resp = self.session.get(f"{self.base}/saves/{save_id}/content", stream=True)
        resp.raise_for_status()
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

    def download_state(self, state_id: int, dest_path: Path) -> None:
        resp = self.session.get(f"{self.base}/states/{state_id}/content", stream=True)
        resp.raise_for_status()
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

    def upload_save(self, rom_id: int, file_path: Path) -> dict:
        with open(file_path, "rb") as f:
            files = {"saveFile": (file_path.name, f)}
            resp = self.session.post(f"{self.base}/saves", params={"rom_id": rom_id}, files=files)
            resp.raise_for_status()
            return resp.json()

    def upload_state(self, rom_id: int, file_path: Path) -> dict:
        with open(file_path, "rb") as f:
            files = {"stateFile": (file_path.name, f)}
            resp = self.session.post(f"{self.base}/states", params={"rom_id": rom_id}, files=files)
            resp.raise_for_status()
            return resp.json()
