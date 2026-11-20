"""
hardware/acquisition_worker.py
--------------------------------
Unico thread aggiuntivo dell'applicazione.
Legge continuamente dalla cella di carico ed emette il segnale `force_received`.

Tutto il resto dell'applicazione gira sul main thread.

-------------------------------------------------------------------------------
REGOLA FONDAMENTALE
-------------------------------------------------------------------------------
Questo worker NON chiama mai direttamente nessun widget Qt.
Comunica esclusivamente tramite segnali.
Il TestController riceve il segnale e aggiorna la GUI sul main thread.

Il worker è l'unico a usare la LoadCell: tara e calibrazione richieste dal
main thread (request_tare / request_calibration) vengono messe in coda ed
eseguite qui, tra una lettura e l'altra.
-------------------------------------------------------------------------------

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
import queue
import time

from PyQt5.QtCore import QThread, pyqtSignal

from hardware.loadcell import LoadCell, LoadCellError
from hardware.filters  import MovingAverageFilter, NullFilter
from config import Config
from core.i18n import _

logger = logging.getLogger(__name__)

# Pausa tra i tentativi quando la scheda non risponde
_RETRY_DELAY_S = 0.5

# Letture fallite per più di questo tempo → cella segnalata come guasta
_FAILURE_LIMIT_S = 1.0


class AcquisitionWorker(QThread):
    """
    Thread di acquisizione dati dalla cella di carico.

    Signals:
        force_received(float):             Campione di forza [mN] già filtrato.
        connected(bool):                   La cella risponde / non risponde più.
        error_occurred(str):               Messaggio di errore per l'operatore.
        tare_finished(bool):               Esito di una tara richiesta.
        calibration_finished(bool, float): Esito della calibrazione e nuovo fattore.
    """

    force_received       = pyqtSignal(float)
    connected            = pyqtSignal(bool)
    error_occurred       = pyqtSignal(str)
    tare_finished        = pyqtSignal(bool)
    calibration_finished = pyqtSignal(bool, float)

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

        # Richieste dal main thread: (comando, argomento)
        self._commands: queue.Queue = queue.Queue()

        # Stato della cella: None finché non è stato comunicato alla GUI
        self._healthy: bool | None = None
        self._last_ok = 0.0
        self._resume_error_reported = False

    # ─── Ciclo principale ────────────────────────────────────────────────────

    def run(self) -> None:
        """
        Loop di acquisizione. Gira finché stop() non viene chiamato.
        """
        logger.info("AcquisitionWorker avviato (rate=%d Hz)", self._rate)
        self._running = True

        # ── Connessione: ritenta finché la scheda non è pronta ───────────────
        if self._connect():
            # ── Taratura iniziale ────────────────────────────────────────────
            self._tare()

        # ── Loop di acquisizione ─────────────────────────────────────────────
        while self._running:
            t_start = time.monotonic()

            self._process_commands()
            self._acquire()

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

    def _connect(self) -> bool:
        """Ritenta la connessione finché la scheda non è pronta o stop()."""
        reported = False

        while self._running:
            if self._loadcell.connect():
                return True

            if not reported:
                msg = (
                    f"{_('Cella di carico non pronta: nuovo tentativo in corso...')} "
                    f"[{self._loadcell.last_error}]"
                )
                logger.error(msg)
                self.error_occurred.emit(msg)
                reported = True

            self._set_healthy(False)
            # Le richieste arrivate intanto falliscono subito, non restano appese
            self._process_commands()
            time.sleep(_RETRY_DELAY_S)

        return False

    def _acquire(self) -> None:
        """Legge un campione; le letture non valide vengono scartate."""
        try:
            raw_mn = self._loadcell.read()
        except LoadCellError as e:
            self._on_read_error(e)
            return

        if not self._healthy:
            self._resume()
            return  # il campione letto prima del ripristino non si usa

        self._last_ok = time.monotonic()
        filtered_mn = self._filter.process(raw_mn)
        self.force_received.emit(filtered_mn)

    def _on_read_error(self, error: LoadCellError) -> None:
        """Scarta la lettura; dopo _FAILURE_LIMIT_S di errori segnala il guasto."""
        if not self._healthy:
            time.sleep(_RETRY_DELAY_S)  # scheda ferma: niente tentativi a raffica
            return

        logger.debug("Lettura scartata: %s", error)

        if time.monotonic() - self._last_ok < _FAILURE_LIMIT_S:
            return

        msg = f"{_('La cella di carico non risponde')}: {error}"
        logger.error(msg)
        self.error_occurred.emit(msg)
        self._set_healthy(False)
        self._filter.reset()

    def _resume(self) -> None:
        """
        La scheda risponde (all'avvio o dopo un guasto, anche dopo un suo
        riavvio): reinvia il fattore di scala prima di usare le letture.
        """
        if not self._apply_scale_factor():
            time.sleep(_RETRY_DELAY_S)
            return

        logger.info("Cella di carico operativa")
        self._last_ok = time.monotonic()
        self._filter.reset()
        self._set_healthy(True)

    def _set_healthy(self, healthy: bool) -> None:
        """Aggiorna la spia solo quando lo stato cambia."""
        if healthy != self._healthy:
            self._healthy = healthy
            self.connected.emit(healthy)

    # ─── Comandi ─────────────────────────────────────────────────────────────

    def _process_commands(self) -> None:
        """Esegue le richieste arrivate dal main thread."""
        while True:
            try:
                command, argument = self._commands.get_nowait()
            except queue.Empty:
                return

            if command == "tare":
                self.tare_finished.emit(self._tare())
            elif command == "calibrate":
                self._calibrate(argument)

    def _tare(self) -> bool:
        try:
            self._loadcell.tare()
        except Exception as e:
            msg = f"{_('Taratura non riuscita')}: {e}"
            logger.error(msg)
            self.error_occurred.emit(msg)
            return False

        self._filter.reset()
        logger.info("Taratura completata")
        return True

    def _calibrate(self, reference_mn: float) -> None:
        try:
            factor = self._loadcell.calibrate(reference_mn)
        except Exception as e:
            msg = f"{_('Calibrazione non riuscita')}: {e}"
            logger.error(msg)
            self.error_occurred.emit(msg)
            self.calibration_finished.emit(False, 0.0)
            return

        self._filter.reset()
        logger.info(
            "Calibrazione completata: riferimento %.1f mN → fattore %.9g mN/conteggio",
            reference_mn, factor,
        )
        self.calibration_finished.emit(True, factor)

    def _apply_scale_factor(self) -> bool:
        """
        Invia alla scheda il fattore salvato in config.json dopo la calibrazione:
        lo sketch lo tiene solo in RAM e lo perde a ogni riavvio.
        """
        factor = Config.scale_factor
        if factor is None:
            logger.warning("Cella di carico non calibrata: resta il fattore dello sketch")
            return True

        try:
            self._loadcell.set_scale_factor(factor)
        except Exception as e:
            # Senza fattore le letture non sono in mN: meglio non usarle
            if not self._resume_error_reported:
                msg = f"{_('Fattore di calibrazione non inviato alla scheda')}: {e}"
                logger.error(msg)
                self.error_occurred.emit(msg)
                self._resume_error_reported = True
            return False

        self._resume_error_reported = False
        logger.info("Fattore di scala inviato alla scheda: %.9g mN/conteggio", factor)
        return True

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

    def request_tare(self) -> None:
        """Chiede una tara (attrezzatura vuota). Esito con tare_finished."""
        self._commands.put(("tare", None))

    def request_calibration(self, reference_mn: float) -> None:
        """Chiede una calibrazione col peso noto appoggiato. Esito con calibration_finished."""
        self._commands.put(("calibrate", reference_mn))

    # ─── Proprietà ───────────────────────────────────────────────────────────

    @property
    def sampling_rate(self) -> int:
        return self._rate
