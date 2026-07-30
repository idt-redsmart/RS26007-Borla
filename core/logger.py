"""
core/logger.py
--------------
Configurazione centralizzata del logging.
Da chiamare UNA SOLA VOLTA all'avvio in main.py, prima di qualsiasi import
che usi logging.getLogger().

Caratteristiche:
  - Dual handler: console (INFO) + file rotante (DEBUG)
  - File di log nella cartella logs/ relativa alla root del progetto
  - Rotazione automatica: 5 MB per file, 3 backup → max ~15 MB su disco
  - Formato compatto su console, formato esteso su file
  - Compatibile Windows e Linux senza modifiche

Usage:
    from core.logger import setup_logging
    setup_logging()          # oppure: setup_logging(level_console="DEBUG")
"""

import logging
import logging.handlers
import sys
from pathlib import Path

# ── Root del progetto (due livelli sopra questo file: core/ → root) ───────────
_APP_ROOT  = Path(__file__).resolve().parent.parent
_LOG_DIR   = _APP_ROOT / "logs"
_LOG_FILE  = _LOG_DIR / "application.log"

# ── Formati ───────────────────────────────────────────────────────────────────
_FMT_CONSOLE = "%(levelname)-8s  %(name)s — %(message)s"
_FMT_FILE    = "%(asctime)s  %(levelname)-8s  %(name)s:%(lineno)d — %(message)s"
_DATE_FMT    = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level_console: str = "INFO",
    level_file:    str = "DEBUG",
    max_bytes:     int = 5 * 1024 * 1024,   # 5 MB
    backup_count:  int = 3,
) -> None:
    """
    Configura il logging dell'applicazione.

    Crea due handler:
      1. StreamHandler  → console, livello `level_console`
      2. RotatingFileHandler → file logs/application.log, livello `level_file`

    Args:
        level_console:  Livello minimo per la console ("DEBUG", "INFO", "WARNING", ...).
        level_file:     Livello minimo per il file di log.
        max_bytes:      Dimensione massima di ogni file prima della rotazione.
        backup_count:   Numero di file di backup da mantenere.
    """
    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)   # il root accetta tutto, filtrano gli handler

    # ── Evita di aggiungere handler duplicati se chiamata più volte ───────────
    if root_logger.handlers:
        return

    # ── Handler 1: console ────────────────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level_console.upper(), logging.INFO))
    console_handler.setFormatter(logging.Formatter(_FMT_CONSOLE))

    # ── Handler 2: file rotante ───────────────────────────────────────────────
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            filename    = _LOG_FILE,
            maxBytes    = max_bytes,
            backupCount = backup_count,
            encoding    = "utf-8",
        )
        file_handler.setLevel(getattr(logging, level_file.upper(), logging.DEBUG))
        file_handler.setFormatter(
            logging.Formatter(_FMT_FILE, datefmt=_DATE_FMT)
        )
        root_logger.addHandler(file_handler)
    except OSError as e:
        # Non blocca l'avvio se il file di log non è scrivibile
        print(f"[logger] Impossibile creare il file di log: {e}", file=sys.stderr)

    root_logger.addHandler(console_handler)

    logging.getLogger(__name__).info(
        "Logging avviato — file: %s  (console: %s, file: %s)",
        _LOG_FILE, level_console.upper(), level_file.upper(),
    )


def get_log_path() -> Path:
    """Restituisce il percorso assoluto del file di log corrente."""
    return _LOG_FILE
