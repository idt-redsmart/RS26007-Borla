"""
hardware/acquisition_worker.py
--------------------------------
Unico thread aggiuntivo dell'applicazione.
Legge continuamente dalla cella di carico ed emette il segnale `force_received`.

Tutto il resto dell'applicazione gira sul main thread.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  REGOLA FONDAMENTALE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Questo worker NON chiama mai direttamente nessun widget Qt.
  Comunica esclusivamente tramite il segnale `force_received(float)`.
  Il TestController riceve il segnale e aggiorna la GUI sul main thread.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Usage (in MainWindow o main.py):
    worker = AcquisitionWorker(loadcell, sampling_rate=200)
    worker.force_received.connect(controller.on_force_received)
    worker.error_occurred.connect(handle_error)
    worker.start()
    ...
    worker.stop()
    worker.wait()
"""

import logging
import time

from PyQt5.QtCore import QThread, pyqtSignal

from hardware.loadcell import LoadCell
from hardware.filters  import MovingAverageFilter, NullFilter
from config import Config

logger = logging.getLogger(__name__)


class AcquisitionWorker(QThread):
    """
    Thread di acquisizione dati dalla cella di carico.

    Signals:
        force_received(float):  Campione di forza [mN] già filtrato.
        connected(bool):        Emesso quando la connessione cambia stato.
        error_occurred(str):    Messaggio di errore non recuperabile.
    """

    force_received = pyqtSignal(float)
    connected      = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        loadcell:      LoadCell,
        sampling_rate: int  = None,
        filter_window: int  = 5,
        parent=None,
    ):
        """
        Args:
            loadcell:      Istanza di LoadCell già costruita (non ancora connessa).
            sampling_rate: Campioni al secondo. Se None legge da Config.
            filter_window: Finestra della media mobile. 1 = filtro disabilitato.
        """
        super().__init__(parent)
        self._loadcell  = loadcell
        self._rate      = sampling_rate or Config.sampling_rate
        self._running   = False

        # Filtro applicato ad ogni campione grezzo
        if filter_window > 1:
            self._filter = MovingAverageFilter(window=filter_window)
        else:
            self._filter = NullFilter()

        # Periodo di campionamento in secondi
        self._period = 1.0 / self._rate

    # ─── Ciclo principale ────────────────────────────────────────────────────

    def run(self) -> None:
        """
        Loop di acquisizione. Gira finché stop() non viene chiamato.

        ┌─────────────────────────────┐
        │  connect()                  │
        │  tare()                     │
        │                             │
        │  while running:             │
        │      raw  = loadcell.read() │
        │      filt = filter(raw)     │
        │      emit force_received    │
        │      sleep(period)          │
        │                             │
        │  disconnect()               │
        └─────────────────────────────┘
        """
        logger.info("AcquisitionWorker avviato (rate=%d Hz)", self._rate)

        # ── Connessione ──────────────────────────────────────────────────────
        ok = self._loadcell.connect()
        if not ok:
            msg = "Impossibile connettersi alla cella di carico."
            logger.error(msg)
            self.error_occurred.emit(msg)
            self.connected.emit(False)
            return

        self.connected.emit(True)
        self._filter.reset()

        # ── Taratura iniziale ────────────────────────────────────────────────
        try:
            self._loadcell.tare()
            logger.info("Taratura completata")
        except Exception as e:
            logger.warning("Taratura fallita: %s — proseguo senza tara", e)

        # ── Loop di acquisizione ─────────────────────────────────────────────
        self._running = True
        while self._running:
            t_start = time.monotonic()

            try:
                raw_mn      = self._loadcell.read()
                filtered_mn = self._filter.process(raw_mn)
                self.force_received.emit(filtered_mn)
            except Exception as e:
                logger.error("Errore lettura cella di carico: %s", e)
                self.error_occurred.emit(f"Errore lettura sensore: {e}")
                break

            # ── Rispetta il sampling rate ────────────────────────────────────
            elapsed = time.monotonic() - t_start
            sleep_s = self._period - elapsed
            if sleep_s > 0:
                time.sleep(sleep_s)

        # ── Disconnessione ───────────────────────────────────────────────────
        try:
            self._loadcell.disconnect()
        except Exception as e:
            logger.warning("Errore disconnessione: %s", e)

        self.connected.emit(False)
        logger.info("AcquisitionWorker terminato")

    # ─── Controllo ───────────────────────────────────────────────────────────

    def stop(self) -> None:
        """
        Segnala al loop di terminare.
        Dopo questa chiamata attendere il completamento con wait().

        Esempio:
            worker.stop()
            worker.wait(timeout_ms=2000)
        """
        self._running = False
        logger.debug("AcquisitionWorker: stop richiesto")

    # ─── Proprietà ───────────────────────────────────────────────────────────

    @property
    def sampling_rate(self) -> int:
        return self._rate
