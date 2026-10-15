    def guess_platform_from_core(self, core_name: str) -> str:
        """Prova a indovinare la piattaforma dal nome del core (matching più flessibile)."""
        key = core_name.replace("_libretro.dll", "").lower()

        # Matching esatto
        if key in LIBRETRO_CORE_MAP:
            return LIBRETRO_CORE_MAP[key]

        # Matching parziale (es. bsnes2014_balanced → snes)
        for core_key, plat in LIBRETRO_CORE_MAP.items():
            if core_key in key or key in core_key:
                return plat

        # Fallback: usa il nome del core
        return key