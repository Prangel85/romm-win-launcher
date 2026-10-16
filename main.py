"""RomM Win Launcher - Minimal version."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import logging
import re
import subprocess
from pathlib import Path
from datetime import datetime

from romm_client import RommClient

CONFIG_FILE = Path("config.json")
LOG_FILE = Path("launcher.log")

# Mappatura nomi piattaforma → codice Batocera
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

# Mappatura semplificata core → piattaforma
LIBRETRO_CORE_MAP = {
    "gambatte": "gb",
    "mgba": "gba",
    "mesen": "nes",
    "fceumm": "nes",
    "nestopia": "nes",
    "snes9x": "snes",
    "bsnes": "snes",
    "mupen64plus_next": "n64",
    "parallel_n64": "n64",
    "dolphin": "gc",
    "melonds": "nds",
    "desmume": "nds",
    "pcsx_rearmed": "psx",
    "beetle_psx": "psx",
    "pcsx2": "ps2",
    "ppsspp": "psp",
    "genesis_plus_gx": "md",
    "picodrive": "md",
    "flycast": "dc",
    "fbneo": "arcade",
    "mame": "arcade",
    "handy": "lynx",
    "mednafen_pce": "pce",
    "mednafen_saturn": "saturn",
    "citra": "3ds",
    "azahar": "3ds",
    "gearboy": "gb",
}

def sanitize_name(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "-", name).strip()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RomM Win Launcher")
        self.geometry("1100x750")

        self.config = self.load_config()
        self.client = None
        self.roms = []

        self.setup_logging()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # --- Scheda Impostazioni ---
        settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(settings_tab, text="Impostazioni")

        settings = ttk.LabelFrame(settings_tab, text="Connessione e percorsi")
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

        # Sezione Core
        cores_frame = ttk.LabelFrame(settings_tab, text="Core RetroArch")
        cores_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.cores_tree = ttk.Treeview(cores_frame, columns=("platform", "core"), show="headings", height=8)
        self.cores_tree.heading("platform", text="Piattaforma")
        self.cores_tree.heading("core", text="Core")
        self.cores_tree.column("platform", width=200)
        self.cores_tree.column("core", width=350)
        self.cores_tree.pack(fill="both", expand=True, padx=5, pady=5)

        core_btn_frame = ttk.Frame(cores_frame)
        core_btn_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(core_btn_frame, text="Aggiungi / Modifica", command=self.edit_core).pack(side="left", padx=5)
        ttk.Button(core_btn_frame, text="Rimuovi", command=self.remove_core).pack(side="left", padx=5)
        ttk.Button(core_btn_frame, text="Scansiona core RetroArch", command=self.scan_retroarch_cores).pack(side="left", padx=5)

        # --- Scheda ROM ---
        roms_tab = ttk.Frame(self.notebook)
        self.notebook.add(roms_tab, text="ROM")

        list_frame = ttk.LabelFrame(roms_tab, text="Libreria")
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
        ttk.Button(btn_frame, text="Scarica ROM", command=self.download_selected).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Scarica media", command=self.download_media).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Scarica tutto", command=self.download_all).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Avvia selezionata", command=self.launch_selected).pack(side="left", padx=5)

        # --- Scheda Save e States ---
        saves_tab = ttk.Frame(self.notebook)
        self.notebook.add(saves_tab, text="Save e States")

        saves_frame = ttk.LabelFrame(saves_tab, text="Salvataggi e Stati")
        saves_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.saves_tree = ttk.Treeview(saves_frame, columns=("type", "locale", "cloud"), show="tree headings")
        self.saves_tree.heading("#0", text="Piattaforma / Gioco / File")
        self.saves_tree.heading("type", text="Tipo")
        self.saves_tree.heading("locale", text="Locale")
        self.saves_tree.heading("cloud", text="Cloud")
        self.saves_tree.column("#0", width=400)
        self.saves_tree.column("type", width=70, anchor="center")
        self.saves_tree.column("locale", width=140)
        self.saves_tree.column("cloud", width=140)
        self.saves_tree.pack(fill="both", expand=True, padx=5, pady=5)

        saves_btn_frame = ttk.Frame(saves_frame)
        saves_btn_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(saves_btn_frame, text="Leggi salvataggi", command=self.read_all_saves).pack(side="left", padx=5)
        ttk.Button(saves_btn_frame, text="Scarica mancanti", command=self.download_missing_saves).pack(side="left", padx=5)
        ttk.Button(saves_btn_frame, text="Carica mancanti", command=self.upload_missing_saves).pack(side="left", padx=5)
        ttk.Button(saves_btn_frame, text="Sincronizza", command=self.sync_saves).pack(side="left", padx=5)

        # --- Log ---
        log_frame = ttk.LabelFrame(self, text="Log")
        log_frame.pack(fill="x", padx=10, pady=5)
        self.log_text = tk.Text(log_frame, height=5, state="disabled")
        self.log_text.pack(fill="x", padx=5, pady=5)

        self.load_cores_into_tree()
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
        cores = {}
        for item in self.cores_tree.get_children():
            plat, core = self.cores_tree.item(item, "values")
            cores[plat] = core
        self.config["cores"] = cores
        CONFIG_FILE.write_text(json.dumps(self.config, indent=2), encoding="utf-8")
        self.log("Impostazioni salvate.")

    def load_cores_into_tree(self):
        self.cores_tree.delete(*self.cores_tree.get_children())
        cores = self.config.get("cores", {})
        for plat, core in sorted(cores.items()):
            self.cores_tree.insert("", "end", values=(plat, core))

    def guess_platform_from_core(self, core_name: str) -> str:
        key = core_name.replace("_libretro.dll", "").lower()
        if key in LIBRETRO_CORE_MAP:
            return LIBRETRO_CORE_MAP[key]
        for core_key, plat in LIBRETRO_CORE_MAP.items():
            if core_key in key or key.startswith(core_key):
                return plat
        return key

    def scan_retroarch_cores(self):
        ra_path = self.ra_var.get().strip()
        if not ra_path:
            self.log("Cartella RetroArch non impostata.", "error")
            return
        cores_dir = Path(ra_path) / "cores"
        if not cores_dir.exists():
            self.log(f"Cartella cores non trovata: {cores_dir}", "error")
            return
        dlls = list(cores_dir.glob("*_libretro.dll"))
        if not dlls:
            self.log("Nessun core trovato.", "warning")
            return
        self.log(f"Trovati {len(dlls)} core in {cores_dir}")
        self.show_cores_dialog(dlls)

    def show_cores_dialog(self, dlls):
        dialog = tk.Toplevel(self)
        dialog.title("Core trovati")
        dialog.geometry("500x400")
        dialog.transient(self)
        dialog.grab_set()
        listbox = tk.Listbox(dialog, selectmode="multiple")
        listbox.pack(fill="both", expand=True, padx=10, pady=10)
        for dll in sorted(dlls):
            listbox.insert("end", dll.name)
        def add_selected():
            selected = [listbox.get(i) for i in listbox.curselection()]
            for name in selected:
                plat = self.guess_platform_from_core(name)
                exists = False
                for item in self.cores_tree.get_children():
                    if self.cores_tree.item(item, "values")[1] == name:
                        exists = True
                        break
                if not exists:
                    self.cores_tree.insert("", "end", values=(plat, name))
            dialog.destroy()
            self.log(f"Aggiunti {len(selected)} core.")
        ttk.Button(dialog, text="Aggiungi selezionati", command=add_selected).pack(pady=5)

    def edit_core(self):
        selection = self.cores_tree.selection()
        plat = ""
        core = ""
        if selection:
            plat, core = self.cores_tree.item(selection[0], "values")
        dialog = tk.Toplevel(self)
        dialog.title("Configura core")
        dialog.geometry("400x150")
        dialog.transient(self)
        dialog.grab_set()
        ttk.Label(dialog, text="Piattaforma (es. gba, snes, gc):").pack(pady=5)
        plat_var = tk.StringVar(value=plat)
        ttk.Entry(dialog, textvariable=plat_var, width=40).pack(pady=2)
        ttk.Label(dialog, text="Core (.dll):").pack(pady=5)
        core_var = tk.StringVar(value=core)
        ttk.Entry(dialog, textvariable=core_var, width=40).pack(pady=2)
        def save():
            p = plat_var.get().strip().lower()
            c = core_var.get().strip()
            if not p or not c:
                return
            for item in self.cores_tree.get_children():
                if self.cores_tree.item(item, "values")[0] == p:
                    self.cores_tree.delete(item)
                    break
            self.cores_tree.insert("", "end", values=(p, c))
            dialog.destroy()
        ttk.Button(dialog, text="Salva", command=save).pack(pady=10)

    def remove_core(self):
        selection = self.cores_tree.selection()
        if selection:
            self.cores_tree.delete(selection[0])

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

    def get_selected_rom(self):
        selection = self.tree.selection()
        if not selection:
            self.log("Nessuna ROM selezionata.", "warning")
            return None
        item = selection[0]
        parent = self.tree.parent(item)
        if not parent:
            self.log("Seleziona una ROM, non una piattaforma.", "warning")
            return None
        plat_name = self.tree.item(parent, "text")
        rom_name = self.tree.item(item, "text")
        rom = next((r for r in self.roms if r.get("name") == rom_name and (r.get("platform_display_name") or r.get("platform_slug")) == plat_name), None)
        if not rom:
            self.log("ROM non trovata.", "error")
            return None
        return rom, item

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
        result = self.get_selected_rom()
        if not result:
            return
        rom, item = result
        self.log(f"Download ROM di '{rom.get('name')}'...")
        client = self.get_client()
        if not client:
            return
        try:
            rom_folder = self.get_rom_folder(rom)
            rom_folder.mkdir(parents=True, exist_ok=True)
            fs_name = rom.get("fs_name") or rom.get("name", "") + ".rom"
            dest = rom_folder / fs_name
            client.download_rom(rom["id"], fs_name, dest)
            self.log(f"Download completato: {dest}")
            self.tree.item(item, values=("Sì",))
        except Exception as e:
            self.log(f"Errore download: {e}", "error")

    def download_media(self):
        result = self.get_selected_rom()
        if not result:
            return
        rom, item = result
        if self.is_rom_downloaded(rom) != "Sì":
            self.log("Scarica prima la ROM.", "warning")
            return
        self.log(f"Download media per '{rom.get('name')}'...")
        client = self.get_client()
        if not client:
            return
        try:
            rom_folder = self.get_rom_folder(rom)
            if rom.get("url_cover"):
                cover_path = rom_folder / "cover.jpg"
                client.download_file(rom["url_cover"], cover_path)
                self.log(f"Cover scaricata: {cover_path.name}")
            if rom.get("has_manual") and rom.get("url_manual"):
                manual_path = rom_folder / "manual.pdf"
                client.download_file(rom["url_manual"], manual_path)
                self.log(f"Manuale scaricato: {manual_path.name}")
            meta_path = rom_folder / "metadata.json"
            meta_path.write_text(json.dumps(rom, indent=2, ensure_ascii=False), encoding="utf-8")
            self.log(f"Metadati salvati: {meta_path.name}")
            self.log("Media scaricati.")
        except Exception as e:
            self.log(f"Errore download media: {e}", "error")

    def download_all(self):
        result = self.get_selected_rom()
        if not result:
            return
        rom, item = result
        self.log(f"Download completo di '{rom.get('name')}'...")
        self.download_selected()
        self.download_media()

    def launch_selected(self):
        result = self.get_selected_rom()
        if not result:
            return
        rom, item = result
        if self.is_rom_downloaded(rom) != "Sì":
            self.log("La ROM non è stata scaricata.", "warning")
            return
        ra_path = self.ra_var.get().strip()
        if not ra_path:
            self.log("Cartella RetroArch non impostata.", "error")
            return
        plat_code = self.get_platform_folder(rom.get("platform_display_name") or "")
        cores = {}
        for item in self.cores_tree.get_children():
            p, c = self.cores_tree.item(item, "values")
            cores[p] = c
        core_dll = cores.get(plat_code)
        if not core_dll:
            self.log(f"Nessun core configurato per '{plat_code}'.", "error")
            return
        rom_folder = self.get_rom_folder(rom)
        fs_name = rom.get("fs_name") or rom.get("name", "") + ".rom"
        rom_file = rom_folder / fs_name
        retroarch_exe = Path(ra_path) / "retroarch.exe"
        if not retroarch_exe.exists():
            self.log(f"retroarch.exe non trovato in {ra_path}", "error")
            return
        core_path = Path(ra_path) / "cores" / core_dll
        if not core_path.exists():
            self.log(f"Core non trovato: {core_path}", "error")
            return
        cmd = [str(retroarch_exe), "-L", str(core_path), str(rom_file)]
        self.log(f"Avvio: {' '.join(cmd)}")
        try:
            subprocess.Popen(cmd)
            self.log("Gioco avviato.")
        except Exception as e:
            self.log(f"Errore avvio: {e}", "error")

# --- Metodi Save e States ---
    def _get_rom_by_id(self, rom_id):
        return next((r for r in self.roms if r.get("id") == rom_id), None)

    def read_all_saves(self):
        self.log("Lettura salvataggi Cloud e Locale...")
        if not self.roms:
            self.load_library()
        client = self.get_client()
        cloud_saves, cloud_states = [], []
        if client:
            try:
                cloud_saves = client.get_saves()
                cloud_states = client.get_states()
                self.log(f"Cloud: {len(cloud_saves)} save, {len(cloud_states)} state")
            except Exception as e:
                self.log(f"Errore cloud: {e}", "error")

        local_items = []
        ra_path = self.ra_var.get().strip()
        if ra_path:
            saves_dir = Path(ra_path) / "saves"
            states_dir = Path(ra_path) / "states"
            if saves_dir.exists():
                for f in saves_dir.rglob("*"):
                    if f.is_file() and f.suffix.lower() in (".srm", ".sav", ".gci", ".eep", ".fla"):
                        local_items.append({"name": f.name, "type": "Save", "mtime": datetime.fromtimestamp(f.stat().st_mtime)})
            if states_dir.exists():
                for f in states_dir.rglob("*"):
                    if f.is_file() and ".state" in f.name.lower():
                        local_items.append({"name": f.name, "type": "State", "mtime": datetime.fromtimestamp(f.stat().st_mtime)})
            self.log(f"Locale: {len(local_items)} file")

        self.populate_combined_tree(cloud_saves, cloud_states, local_items)

    def populate_combined_tree(self, cloud_saves, cloud_states, local_items):
        self.saves_tree.delete(*self.saves_tree.get_children())
        
        # Dizionario cloud per nome normalizzato
        cloud_by_name = {}
        for s in cloud_saves:
            fname = s.get("file_name") or s.get("name") or ""
            norm = self._normalize_filename(fname)
            cloud_by_name[norm] = {"type": "Save", "data": s, "rom_id": s.get("rom_id")}
        for st in cloud_states:
            fname = st.get("file_name") or st.get("name") or ""
            norm = self._normalize_filename(fname)
            cloud_by_name[norm] = {"type": "State", "data": st, "rom_id": st.get("rom_id")}

        # Raggruppa per piattaforma e poi per ROM
        by_platform = {}
        for norm, info in cloud_by_name.items():
            rid = info["rom_id"]
            rom = self._get_rom_by_id(rid)
            plat = rom.get("platform_display_name", "Sconosciuto") if rom else "Sconosciuto"
            by_platform.setdefault(plat, {})
            by_platform[plat].setdefault(rid, {"files": [], "local": []})
            by_platform[plat][rid]["files"].append(info)

        # Associa i file locali
        unmatched = []
        for item in local_items:
            norm = self._normalize_filename(item["name"])
            if norm in cloud_by_name:
                rid = cloud_by_name[norm]["rom_id"]
                rom = self._get_rom_by_id(rid)
                plat = rom.get("platform_display_name", "Sconosciuto") if rom else "Sconosciuto"
                by_platform.setdefault(plat, {})
                by_platform[plat].setdefault(rid, {"files": [], "local": []})
                by_platform[plat][rid]["local"].append(item)
            else:
                unmatched.append(item)

        # Popola l'albero
        for plat, roms in sorted(by_platform.items()):
            parent = self.saves_tree.insert("", "end", text=plat, open=False)
            for rid, data in roms.items():
                rom = self._get_rom_by_id(rid)
                rom_name = rom.get("name", f"ROM {rid}") if rom else f"ROM {rid}"
                game = self.saves_tree.insert(parent, "end", text=rom_name, open=False)
                # Cloud
                for info in data["files"]:
                    fname = info["data"].get("file_name") or info["data"].get("name") or ""
                    date = (info["data"].get("updated_at") or info["data"].get("created_at") or "")[:16].replace("T", " ")
                    self.saves_tree.insert(game, "end", text=fname, values=(info["type"], "", date))
                # Locale
                for item in data["local"]:
                    date = item["mtime"].strftime("%Y-%m-%d %H:%M")
                    self.saves_tree.insert(game, "end", text=item["name"], values=(item["type"], date, ""))

        # Non associati
        if unmatched:
            parent = self.saves_tree.insert("", "end", text="Non associati", open=False)
            for item in unmatched:
                date = item["mtime"].strftime("%Y-%m-%d %H:%M")
                self.saves_tree.insert(parent, "end", text=item["name"], values=(item["type"], date, ""))A

    def _normalize_filename(self, name: str) -> str:
        """Rimuove timestamp e estensioni per il matching."""
        import re
        # Rimuove qualsiasi cosa tra parentesi quadre (timestamp)
        name = re.sub(r'\[[^\]]*\]', '', name)
        # Rimuove estensioni comuni
        for ext in [".srm", ".sav", ".state", ".auto", ".png", ".gci", ".state.auto", ".state.png"]:
            while name.lower().endswith(ext):
                name = name[:-len(ext)]
        return name.strip().lower()

    def download_missing_saves(self):
        self.log("Download salvataggi mancanti (base)")

    def upload_missing_saves(self):
        self.log("Upload salvataggi mancanti (base)")

    def sync_saves(self):
        self.log("Sincronizzazione: confronta Cloud e Locale...")
        self.read_all_saves()

if __name__ == "__main__":
    app = App()
    app.mainloop()
