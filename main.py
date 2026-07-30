import sys
import logging
from pathlib import Path

# ── 1. Setup logging (prima di tutto il resto) ────────────────────────────────
#    Importiamo core.logger PRIMA di Config così i messaggi di Config._load()
#    vengono già catturati dal file handler.
from core.logger import setup_logging
setup_logging()

log = logging.getLogger(__name__)

# ── Aggiungi APP_ROOT a sys.path se non già presente ─────────────────────────
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QFontDatabase

from config import Config, IS_WINDOWS, IS_LINUX
from ui.main_window import MainWindow
from hardware.loadcell import LoadCell
from hardware.acquisition_worker import AcquisitionWorker


# ─── Font cross-platform ──────────────────────────────────────────────────────

_FONT_CANDIDATES_WIN   = ["Segoe UI", "Arial"]
_FONT_CANDIDATES_LINUX = ["Ubuntu", "Liberation Sans", "DejaVu Sans", "Arial"]


def _pick_font(candidates: list[str], fallback: str = "Sans Serif") -> str:
    """Restituisce il primo font disponibile nel sistema."""
    available = QFontDatabase().families()
    for name in candidates:
        if name in available:
            return name
    return fallback


def _setup_font(app: QApplication) -> None:
    candidates = _FONT_CANDIDATES_WIN if IS_WINDOWS else _FONT_CANDIDATES_LINUX
    font_name  = _pick_font(candidates)
    app.setFont(QFont(font_name, 10))
    log.info("Font UI: %s", font_name)


# ─── Stylesheet ───────────────────────────────────────────────────────────────

def _load_stylesheet(app: QApplication) -> None:
    qss = _ROOT / "ui" / "styles.qss"
    if qss.exists():
        app.setStyleSheet(qss.read_text(encoding="utf-8"))
        log.debug("Stylesheet caricato da %s", qss)
    else:
        log.warning("styles.qss non trovato: %s", qss)


# ─── Entry point ─────────────────────────────────────────────────────────────

def main() -> None:
    log.info("=== Avvio ElasticReactionTest === piattaforma: %s", Config.platform_info)

    app = QApplication(sys.argv)
    app.setApplicationName("ElasticReactionTest")
    app.setOrganizationName(Config.company_name)

    _setup_font(app)
    _load_stylesheet(app)

    # ── Finestra principale ───────────────────────────────────────────────────
    window = MainWindow()
    log.debug("MainWindow creata")

    # ── Hardware: cella di carico + worker ───────────────────────────────────
    loadcell = LoadCell()
    worker   = AcquisitionWorker(
        loadcell      = loadcell,
        sampling_rate = Config.sampling_rate,
        filter_window = Config.filter_window,
    )
    log.info("AcquisitionWorker: rate=%d Hz  filtro=%d campioni",
             Config.sampling_rate, Config.filter_window)

    # ── Collega segnali ───────────────────────────────────────────────────────
    worker.force_received.connect(window.controller.on_force_received)
    worker.connected.connect(window.set_loadcell_status)
    worker.error_occurred.connect(lambda msg: window.set_loadcell_status(False))

    # ── Avvio ─────────────────────────────────────────────────────────────────
    worker.start()
    window.show()
    log.info("Applicazione avviata")

    exit_code = app.exec_()

    # ── Shutdown pulito ───────────────────────────────────────────────────────
    log.info("Shutdown in corso...")
    worker.stop()
    if not worker.wait(2000):
        log.warning("AcquisitionWorker non ha risposto entro 2s — forzato")
        worker.terminate()

    log.info("=== Chiusura (exit code: %d) ===", exit_code)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
