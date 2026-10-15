"""RomM Win Launcher - Minimal version."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import logging
import re
from pathlib import Path
from datetime import datetime

from romm_client import RommClient

CONFIG_FILE = Path("config.json")
LOG_FILE = Path("launcher.log")

# Mappatura nomi piattaforma → codice Batocera
# Fonte: https://wiki.batocera.org/systems
PLATFORM_FOLDERS = {
    "game boy": "gb",
    "game boy color": "gbc",
    "game boy advance": "gba",
    "nes": "nes",
    "famicom": "nes",
    "nintendo entertainment system": "nes",
    "super nintendo": "snes",
    "snes": "snes",
    "super famicom": "snes",
    "nintendo 64": "n64",
    "n64": "n64",
    "gamecube": "gc",
    "nintendo gamecube": "gc",
    "wii": "wii",
    "nintendo ds": "nds",
    "nds": "nds",
    "nintendo 3ds": "3ds",
    "playstation": "psx",
    "ps1": "psx",
    "psx": "psx",
    "playstation 2": "ps2",
    "ps2": "ps2",
    "playstation portable": "psp",
    "psp": "psp",
    "sega genesis": "md",
    "mega drive": "md",
    "genesis": "md",
    "sega master system": "sms",
    "master system": "sms",
    "game gear": "gg",
    "dreamcast": "dc",
    "arcade": "arcade",
    "mame": "arcade",
    "atari 2600": "atari2600",
    "atari 7800": "atari7800",
    "neo geo": "neogeo",
    "neo-geo": "neogeo",
}

def sanitize_name(name: str) -> str:
    """Rimuove i caratteri non validi nei nomi di cartella Windows."""
    return re.sub(r'[\\/:*?"<>|]', "-", name).strip()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RomM Win Launcher")
        self.geometry("1000x700")

        self.config = self.load_config()
        self.client = None
        self.roms = []

        self.setup_logging()

        # --- Settings frame ---
        settings = ttk.LabelFrame(self, text="Impostazioni")
        settings.pack(fill="x", padx=10, pady=5)

        ttk.Label(settings, text="URL RomM:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.url_var = tk.StringVar(value=self.config.get("url", ""))
        ttk.Entry(settings, textvariable=self.url_var, width=45).grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(settings, text="Client API Token:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.token_var = tk.StringVar(value=self.config.get("token", ""))
        ttk.Entry(settings, textvariable=self.token_var, width=45, show="*").grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(settings, text="Cartella RetroArch:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.ra_var = tk.StringVar(value=self.config.get("retroarch_path", ""))
        ttk.Entry(settings, textvariable=self.ra_var, width=45).grid(row=2, column=1, padx=5, pady=2)
        ttk.Button(settings, text="Sfoglia...", command=lambda: self.browse_folder(self.ra_var)).grid(row=2, column=2, padx=5)

        ttk.Label(settings, text="Cartella ROM:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.rom_dir_var = tk.StringVar(value=self.config.get("rom_path", ""))
        ttk.Entry(settings, textvariable=self.rom_dir_var, width=45).grid(row=3, column=1, padx=5, pady=2)
        ttk.Button(settings, text="Sfoglia...", command=lambda: self.browse_folder(self.rom_dir_var)).grid(row=3, column=2, padx=5)

        ttk.Label(settings, text="Log su file:").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        self.log_level_var = tk.StringVar(value=self.config.get("log_level", "No"))
        ttk.Combobox(settings, textvariable=self.log_level_var, values=["No", "Info", "Debug", "Errori"], state="readonly", width=15).grid(row=4, column=1, sticky="w", padx=5, pady=2)

        ttk.Button(settings, text="Salva impostazioni", command=self.save_settings).grid(row=5, column=1, sticky="e", padx=5, pady=5)

        # --- ROM list ---
        list_frame = ttk.LabelFrame(self, text="ROM")
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(list_frame, columns=("downloaded",), show="tree headings")
        self.tree.heading("#0", text="Sistema / Nome")
        self.tree.heading("downloaded", text="Scaricato?")
        self.tree.column("#0", width=600)
        self.tree.column("downloaded", width=100, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(btn_frame, text="Carica libreria", command=self.load_library).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Scarica selezionata", command=self.download_selected).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Avvia selezionata", command=self.launch_selected).pack(side="left", padx=5)

        # --- Log ---
        log_frame = ttk.LabelFrame(self, text="Log")
        log_frame.pack(fill="both", expand=False, padx=10, pady=5)
        self.log_text = tk.Text(log_frame, height=8, state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

        self.log("Avvio applicazione.")

    def setup_logging(self):
        if LOG_FILE.exists():
            LOG_FILE.unlink()
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler(LOG_FILE, encoding="utf-8"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("launcher")

    def browse_folder(self, var: tk.StringVar):
        path = filedialog.askdirectory()
        if path:
            var.set(path)

    def log(self, msg: str, level: str = "info"):
        level = level.lower()
        setting = self.log_level_var.get().lower()

        if level in ("info", "warning", "error"):
            self.log_text.configure(state="normal")
            self.log_text.insert("end", f"{datetime.now():%H:%M:%S} {msg}\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")

        if setting == "no":
            return
        if setting == "errori" and level != "error":
            return
        if setting == "info" and level == "debug":
            return

        if level == "debug":
            self.logger.debug(msg)
        elif level == "info":
            self.logger.info(msg)
        elif level == "warning":
            self.logger.warning(msg)
        elif level == "error":
            self.logger.error(msg)

    def load_config(self) -> dict:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return {}

    def save_settings(self):
        self.config["url"] = self.url_var.get().strip()
        self.config["token"] = self.token_var.get().strip()
        self.config["retroarch_path"] = self.ra_var.get().strip()
        self.config["rom_path"] = self.rom_dir_var.get().strip()
        self.config["log_level"] = self.log_level_var.get()
        CONFIG_FILE.write_text(json.dumps(self.config, indent=2), encoding="utf-8")
        self.log("Impostazioni salvate.")

    def get_client(self) -> RommClient | None:
        url = self.url_var.get().strip()
        token = self.token_var.get().strip()
        if not url or not token:
            self.log("URL o token mancanti.", "error")
            return None
        return RommClient(url, token)

    def get_platform_folder(self, platform_name: str) -> str:
        key = platform_name.lower().strip()
        return PLATFORM_FOLDERS.get(key, key.replace(" ", "_"))

    def get_rom_folder(self, rom: dict) -> Path:
        """Restituisce il percorso della sottocartella della ROM: sistema/(id) - nome"""
        rom_dir = self.rom_dir_var.get().strip()
        if not rom_dir:
            return Path()
        plat_name = rom.get("platform_display_name") or rom.get("platform_slug") or "unknown"
        folder = self.get_platform_folder(plat_name)
        rom_id = rom.get("id", "0")
        rom_name = sanitize_name(rom.get("name", "unknown"))
        rom_folder_name = f"{rom_id} - {rom_name}"
        return Path(rom_dir) / folder / rom_folder_name

    def is_rom_downloaded(self, rom: dict) -> str:
        rom_folder = self.get_rom_folder(rom)
        if not rom_folder or not rom_folder.exists():
            return "No"
        fs_name = rom.get("fs_name") or rom.get("name", "") + ".rom"
        dest = rom_folder / fs_name
        return "Sì" if dest.exists() else "No"

    def load_library(self):
        self.log("Caricamento libreria da RomM...")
        client = self.get_client()
        if not client:
            return
        try:
            self.roms = client.get_roms()
            self.populate_tree()
            self.log(f"Caricati {len(self.roms)} ROM.")
        except Exception as e:
            self.log(f"Errore caricamento libreria: {e}", "error")

    def populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        by_platform = {}
        for rom in self.roms:
            plat = rom.get("platform_display_name") or rom.get("platform_slug") or "Sconosciuto"
            by_platform.setdefault(plat, []).append(rom)

        for plat, roms in sorted(by_platform.items()):
            parent = self.tree.insert("", "end", text=plat, open=False)
            for rom in sorted(roms, key=lambda r: r.get("name", "")):
                downloaded = self.is_rom_downloaded(rom)
                self.tree.insert(parent, "end", text=rom.get("name", ""), values=(downloaded,))

    def download_selected(self):
        selection = self.tree.selection()
        if not selection:
            self.log("Nessuna ROM selezionata.", "warning")
            return

        item = selection[0]
        parent = self.tree.parent(item)
        if not parent:
            self.log("Seleziona una ROM, non una piattaforma.", "warning")
            return

        # Trova la ROM corrispondente
        plat_name = self.tree.item(parent, "text")
        rom_name = self.tree.item(item, "text")
        rom = next((r for r in self.roms if r.get("name") == rom_name and (r.get("platform_display_name") or r.get("platform_slug")) == plat_name), None)
        if not rom:
            self.log("ROM non trovata.", "error")
            return

        self.log(f"Download di '{rom_name}'...")
        client = self.get_client()
        if not client:
            return

        try:
            rom_folder = self.get_rom_folder(rom)
            if not rom_folder:
                self.log("Cartella ROM non impostata.", "error")
                return
            rom_folder.mkdir(parents=True, exist_ok=True)

            fs_name = rom.get("fs_name") or rom_name + ".rom"
            dest = rom_folder / fs_name

            client.download_rom(rom["id"], fs_name, dest)
            self.log(f"Download completato: {dest}")
            # Aggiorna lo stato nella lista
            self.tree.item(item, values=("Sì",))
        except Exception as e:
            self.log(f"Errore download: {e}", "error")

    def launch_selected(self):
        self.log("Avvio gioco... (da implementare)")

if __name__ == "__main__":
    app = App()
    app.mainloop()
