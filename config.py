"""
config.py
---------
Configurazione dell'applicazione.

Regole:
  - Tutti i PERCORSI sono assoluti e risolti rispetto a APP_ROOT.
  - I valori raw (stringhe relative) arrivano da config.json.
  - Le proprietà "cooked" (Path risolte) si chiamano con il suffisso _path.
  - Compatibile Windows e Linux senza modifiche al codice.

Struttura config.json:
  Vedi _DEFAULTS per i valori di default.
  Il file viene letto da APP_ROOT/config.json.
"""

import json
import sys
import platform
import logging
from pathlib import Path

log = logging.getLogger(__name__)

# ── Radice del progetto (directory che contiene questo file) ──────────────────
APP_ROOT = Path(__file__).resolve().parent

# ── Percorso del file di configurazione ──────────────────────────────────────
_CONFIG_FILE = APP_ROOT / "config.json"

# ── Sistema operativo ─────────────────────────────────────────────────────────
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX   = platform.system() == "Linux"

# ── Valori di default ─────────────────────────────────────────────────────────
_DEFAULTS: dict = {
    # ── Parametri di collaudo ─────────────────────────────────────────────────
    "sampling_rate":  200,
    "test_time":      4.0,
    "trigger_force":  200.0,
    "lower_limit":    1060.0,
    "upper_limit":    1350.0,

    # ── Hardware ──────────────────────────────────────────────────────────────
    "filter_window":  5,            # campioni per la media mobile

    # ── Percorsi (relativi a APP_ROOT, separatore sempre '/') ─────────────────
    "database":       "database/database.db",
    "reports":        "reports/",
    "logs":           "logs/",

    # ── Sicurezza ─────────────────────────────────────────────────────────────
    # (La password è ora salvata nel database)

    # ── Branding ──────────────────────────────────────────────────────────────
    "company_name":   "Industrie Borla srl",
    "part_number":    "PF0924",

    # ── Logging ───────────────────────────────────────────────────────────────
    "log_level_console": "INFO",
    "log_level_file":    "DEBUG",
    
    # ── Localizzazione ────────────────────────────────────────────────────────
    "language":          "it",
}


class _Config:
    """
    Singleton di configurazione.

    Accesso ai valori:
        Config.lower_limit          → float (raw da JSON)
        Config.database_path        → Path  (assoluto, risolto)
        Config.reports_path         → Path  (assoluto, risolto)
        Config.logs_path            → Path  (assoluto, risolto)
    """

    def __init__(self):
        self._data: dict = dict(_DEFAULTS)
        self._load()

    # ─── I/O ────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if _CONFIG_FILE.exists():
            try:
                with _CONFIG_FILE.open("r", encoding="utf-8") as f:
                    self._data.update(json.load(f))
                log.debug("config.json caricato da %s", _CONFIG_FILE)
            except Exception as e:
                log.warning("Errore lettura config.json: %s — uso default", e)
        else:
            log.info("config.json non trovato — uso valori di default")

    def save(self) -> None:
        """Salva la configurazione corrente su config.json."""
        try:
            with _CONFIG_FILE.open("w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=4, ensure_ascii=False)
            log.info("config.json salvato in %s", _CONFIG_FILE)
        except Exception as e:
            log.error("Errore scrittura config.json: %s", e)

    # ─── Accesso raw ────────────────────────────────────────────────────────

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"Config: campo sconosciuto '{name}'")

    def set(self, key: str, value) -> None:
        """Aggiorna un valore in memoria (usa save() per persistere)."""
        self._data[key] = value

    # ─── Percorsi risolti (sempre assoluti) ─────────────────────────────────

    @property
    def database_path(self) -> Path:
        """Percorso assoluto del file SQLite."""
        p = APP_ROOT / self._data["database"]
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def reports_path(self) -> Path:
        """Percorso assoluto della cartella dei PDF."""
        p = APP_ROOT / self._data["reports"]
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def logs_path(self) -> Path:
        """Percorso assoluto della cartella dei log."""
        p = APP_ROOT / self._data["logs"]
        p.mkdir(parents=True, exist_ok=True)
        return p

    # ─── Info piattaforma ────────────────────────────────────────────────────

    @property
    def platform_info(self) -> str:
        """Stringa leggibile della piattaforma corrente."""
        return f"{platform.system()} {platform.release()} ({platform.machine()})"


# ── Singleton ─────────────────────────────────────────────────────────────────
Config = _Config()
