"""RomM Win Launcher - Minimal skeleton."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from pathlib import Path

CONFIG_FILE = Path("config.json")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RomM Win Launcher")
        self.geometry("900x600")

        self.config = self.load_config()

        # --- Settings frame ---
        settings = ttk.LabelFrame(self, text="Connessione RomM")
        settings.pack(fill="x", padx=10, pady=5)

        ttk.Label(settings, text="URL RomM:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.url_var = tk.StringVar(value=self.config.get("url", ""))
        ttk.Entry(settings, textvariable=self.url_var, width=50).grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(settings, text="Client API Token:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.token_var = tk.StringVar(value=self.config.get("token", ""))
        ttk.Entry(settings, textvariable=self.token_var, width=50, show="*").grid(row=1, column=1, padx=5, pady=2)

        ttk.Button(settings, text="Salva impostazioni", command=self.save_settings).grid(row=2, column=1, sticky="e", padx=5, pady=5)

        # --- ROM list ---
        list_frame = ttk.LabelFrame(self, text="ROM")
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.rom_list = tk.Listbox(list_frame)
        self.rom_list.pack(fill="both", expand=True, padx=5, pady=5)

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

    def log(self, msg: str):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def load_config(self) -> dict:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return {}

    def save_settings(self):
        self.config["url"] = self.url_var.get().strip()
        self.config["token"] = self.token_var.get().strip()
        CONFIG_FILE.write_text(json.dumps(self.config, indent=2), encoding="utf-8")
        self.log("Impostazioni salvate.")

    def load_library(self):
        self.log("Caricamento libreria... (da implementare)")

    def download_selected(self):
        self.log("Download ROM... (da implementare)")

    def launch_selected(self):
        self.log("Avvio gioco... (da implementare)")

if __name__ == "__main__":
    app = App()
    app.mainloop()
