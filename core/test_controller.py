"""
core/test_controller.py
-----------------------
Cervello dell'applicazione. Gestisce la macchina a stati del collaudo.

STATI:
    IDLE             — nessun test in corso
    WAITING_TRIGGER  — in attesa che la forza superi la soglia trigger
    ACQUIRING        — finestra di acquisizione da test_time secondi
    PROCESSING       — calcola statistiche del pezzo appena acquisito
    SAVING           — salva su DB e genera PDF (al termine della sessione)
    DONE             — sessione completata

THREAD:
    Tutto gira sul main thread (riceve segnali dal worker via Qt signal/slot).
    Nessuna operazione bloccante qui — DB e PDF sono veloci su SQLite locale.

SEGNALI EMESSI verso la GUI:
    force_updated(float)              — forza corrente da visualizzare
    status_changed(str)               — messaggio di stato per la UI
    acquiring_started()               — inizia finestra da 4s
    acquiring_progress(int)           — percentuale completamento [0–100]
    piece_done(int, bool)             — pezzo N completato, PASS/FAIL
    stats_updated(dict)               — statistiche aggiornate
    session_done(TestResult)          — sessione terminata
    error_occurred(str)               — messaggio di errore
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum, auto

from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from config import Config
from model.sample import Sample
from model.test_result import TestResult
from core import statistics as stats_service
from core.database import Database
from core.i18n import _


# ─── Stati ──────────────────────────────────────────────────────────────────

class State(Enum):
    IDLE            = auto()
    WAITING_TRIGGER = auto()
    ACQUIRING       = auto()
    PROCESSING      = auto()
    SAVING          = auto()
    DONE            = auto()


# ─── Controller ─────────────────────────────────────────────────────────────

class TestController(QObject):
    """
    Macchina a stati del collaudo elastico.

    Viene istanziato una volta sola in MainWindow e collegato al worker
    e alle pagine UI tramite segnali.
    """

    # ── Segnali verso la GUI ─────────────────────────────────────────────────
    force_updated       = pyqtSignal(float)          # forza corrente [mN]
    status_changed      = pyqtSignal(str, str)        # (testo, colore hex)
    acquiring_started   = pyqtSignal()
    acquiring_progress  = pyqtSignal(int)             # 0–100 %
    piece_done          = pyqtSignal(int, bool)       # (piece_idx, pass)
    piece_data_ready    = pyqtSignal(list)            # list[float] forze dell'ultimo pezzo
    stats_updated       = pyqtSignal(dict)
    session_done        = pyqtSignal(object)          # TestResult
    error_occurred      = pyqtSignal(str)

    # ── Costruttore ──────────────────────────────────────────────────────────

    def __init__(self, db: Database, parent: QObject | None = None):
        super().__init__(parent)
        self._db    = db
        self._state = State.IDLE
        self._result: TestResult | None = None

        # Campioni del pezzo corrente (azzerati ad ogni nuovo pezzo)
        self._current_piece_samples: list[Sample] = []
        self._piece_idx: int = 0

        # Timer di acquisizione: scatta ogni 50 ms per aggiornare il progresso
        self._acq_timer   = QTimer(self)
        self._acq_timer.setInterval(50)                   # 50 ms → 20 tick/s
        self._acq_timer.timeout.connect(self._on_acq_tick)

        self._acq_elapsed_ms: int = 0
        self._acq_duration_ms: int = int(Config.test_time * 1000)

    # ─── API pubblica ────────────────────────────────────────────────────────

    def start_session(self, operator: str, mould: str,
                      production_lot: str, raw_material_lot: str) -> None:
        """
        Avvia una nuova sessione di collaudo.
        Chiamato dalla UI dopo che l'operatore ha premuto START TEST.
        """
        if self._state != State.IDLE:
            self.error_occurred.emit(_("Un collaudo è già in corso."))
            return

        self._result = TestResult(
            date             = datetime.now(),
            operator         = operator,
            mould            = mould,
            production_lot   = production_lot,
            raw_material_lot = raw_material_lot,
            lower_limit      = Config.lower_limit,
            upper_limit      = Config.upper_limit,
        )
        self._piece_idx = 0
        self._current_piece_samples = []

        self._set_state(State.WAITING_TRIGGER)

    def end_session(self) -> None:
        """
        Termina la sessione corrente su richiesta dell'operatore (pulsante END TEST).
        Elabora le statistiche finali, salva su DB e genera il PDF.
        Se nessun pezzo è stato acquisito, annulla senza salvare.
        """
        if self._state == State.IDLE:
            return

        self._acq_timer.stop()

        if not self._result or not self._result.samples:
            # Nessun pezzo acquisito — annulla silenziosamente
            self._reset()
            return

        self._set_state(State.SAVING)
        self._finalize_and_save()

    def on_force_received(self, force_mn: float) -> None:
        """
        Slot collegato al segnale `force_received(float)` dell'AcquisitionWorker.
        Viene chiamato ad ogni campione letto dalla cella di carico.
        """
        # Aggiorna sempre la GUI con la forza corrente
        self.force_updated.emit(force_mn)

        if self._state == State.WAITING_TRIGGER:
            self._check_trigger(force_mn)

        elif self._state == State.ACQUIRING:
            self._acquire_sample(force_mn)

    # ─── Macchina a stati ────────────────────────────────────────────────────

    def _check_trigger(self, force_mn: float) -> None:
        """Verifica se la forza supera la soglia trigger."""
        if force_mn >= Config.trigger_force:
            self._start_acquiring()

    def _start_acquiring(self) -> None:
        """Avvia la finestra di acquisizione."""
        self._current_piece_samples = []
        self._acq_elapsed_ms = 0
        self._acq_duration_ms = int(Config.test_time * 1000)
        self._set_state(State.ACQUIRING)
        self._acq_timer.start()
        self.acquiring_started.emit()
        self.status_changed.emit(
            f"{_('ACQUISIZIONE PEZZO')} #{self._piece_idx + 1}",
            "#00c8ff",
        )

    def _acquire_sample(self, force_mn: float) -> None:
        """Aggiunge un campione alla lista del pezzo corrente."""
        lsl = self._result.lower_limit
        usl = self._result.upper_limit
        sample = Sample(
            force_mn  = force_mn,
            timestamp = datetime.now(),
            piece_idx = self._piece_idx,
            in_range  = (lsl <= force_mn <= usl),
        )
        self._current_piece_samples.append(sample)

    def _on_acq_tick(self) -> None:
        """
        Chiamato ogni 50 ms dal QTimer durante l'acquisizione.
        Calcola la percentuale di avanzamento e termina al raggiungimento
        del tempo impostato.
        """
        self._acq_elapsed_ms += 50
        percent = min(100, int(self._acq_elapsed_ms / self._acq_duration_ms * 100))
        self.acquiring_progress.emit(percent)

        if self._acq_elapsed_ms >= self._acq_duration_ms:
            self._acq_timer.stop()
            self._set_state(State.PROCESSING)
            self._process_piece()

    def _process_piece(self) -> None:
        """
        Elabora i campioni del pezzo appena acquisito.
        Aggiunge i campioni al TestResult, aggiorna le statistiche di sessione
        e segnala la UI. Poi torna in WAITING_TRIGGER per il pezzo successivo.
        """
        if not self._current_piece_samples:
            self.error_occurred.emit(_("Nessun campione acquisito per questo pezzo."))
            self._set_state(State.WAITING_TRIGGER)
            return

        # Prende solo l'ultimo campione (quello al 4° secondo)
        final_sample = self._current_piece_samples[-1]
        
        # ── Valutazione pezzo ─────────────────────────────────────────────
        lsl       = self._result.lower_limit
        usl       = self._result.upper_limit
        piece_ok  = final_sample.in_range

        # ── Aggiunge il singolo campione finale alla sessione ─────────────────
        self._result.samples.append(final_sample)
        self._piece_idx += 1
        self._result.qty = self._piece_idx

        # ── Statistiche aggiornate sull'intera sessione ───────────────────
        session_stats = stats_service.compute(self._result.samples)
        self._result.min_mn   = session_stats["min"]
        self._result.mean_mn  = session_stats["mean"]
        self._result.max_mn   = session_stats["max"]
        self._result.std_mn   = session_stats["std"]
        self._result.range_mn = session_stats["range"]

        # ── Aggiorna esito provvisorio ─────────────────────────────────────
        all_ok = stats_service.is_pass(self._result.samples, lsl, usl)
        self._result.result = "PASS" if all_ok else "FAIL"

        # ── Segnala la GUI ────────────────────────────────────────────────
        self.piece_done.emit(self._piece_idx, piece_ok)
        self.stats_updated.emit({
            "qty":   self._result.qty,
            "min":   self._result.min_mn,
            "mean":  self._result.mean_mn,
            "max":   self._result.max_mn,
            "std":   self._result.std_mn,
            "range": self._result.range_mn,
        })
        
        # ── Invia l'elenco dei campioni finali al grafico di Trend ────────
        force_values = [s.force_mn for s in self._result.samples]
        self.piece_data_ready.emit(force_values)

        # ── Torna ad aspettare il prossimo pezzo ─────────────────────────
        self._set_state(State.WAITING_TRIGGER)
        self.status_changed.emit(
            f"Pezzo #{self._piece_idx} completato — "
            f"{'OK ✓' if piece_ok else 'FUORI LIMITE ✗'}  |  ATTESA TRIGGER",
            "#00e676" if piece_ok else "#ff3d57",
        )

    def _finalize_and_save(self) -> None:
        """
        Calcola l'esito definitivo, salva su DB e segnala la sessione completata.
        La generazione del PDF viene delegata a chi si connette al segnale `session_done`.
        """
        # Esito finale
        lsl = self._result.lower_limit
        usl = self._result.upper_limit
        all_ok = stats_service.is_pass(self._result.samples, lsl, usl)
        self._result.result = "PASS" if all_ok else "FAIL"

        # Salva su database
        try:
            assigned_id = self._db.save_test(self._result)
            self._result.id = assigned_id
            
            # ── Genera PDF ──
            try:
                from core.pdf_generator import generate_report
                from config import Config
                
                data_for_pdf = {
                    "id": assigned_id,
                    "date": self._result.date.isoformat(),
                    "operator": self._result.operator,
                    "mould": self._result.mould,
                    "production_lot": self._result.production_lot,
                    "raw_material_lot": self._result.raw_material_lot,
                    "qty": self._result.qty,
                    "lower_limit": self._result.lower_limit,
                    "upper_limit": self._result.upper_limit,
                    "min_mn": self._result.min_mn,
                    "mean_mn": self._result.mean_mn,
                    "max_mn": self._result.max_mn,
                    "range_mn": self._result.range_mn,
                    "std_mn": self._result.std_mn,
                    "result": self._result.result,
                    "samples": [{"force_mn": s.force_mn} for s in self._result.samples],
                    "part_number": Config.part_number
                }
                pdf_path = generate_report(data_for_pdf, Config.reports_path)
                self._result.pdf_path = pdf_path
                self._db.update_pdf_path(assigned_id, pdf_path)
                import logging
                log = logging.getLogger(__name__)
                log.info(f"Report PDF generato con successo in {pdf_path}")
            except Exception as e:
                import logging
                log = logging.getLogger(__name__)
                log.error(f"Errore generazione PDF: {e}", exc_info=True)
                
        except Exception as e:
            self.error_occurred.emit(f"Errore salvataggio database: {e}")
            self._reset()
            return

        self._set_state(State.DONE)
        self.status_changed.emit(
            f"Sessione completata — {self._result.result}",
            "#00e676" if self._result.result == "PASS" else "#ff3d57",
        )

        # Emette il risultato completo: chi è connesso genererà il PDF
        self.session_done.emit(self._result)
        self._reset()

    # ─── Helpers ────────────────────────────────────────────────────────────

    def _set_state(self, new_state: State) -> None:
        self._state = new_state

    def _reset(self) -> None:
        """Riporta il controller allo stato IDLE."""
        self._state = State.IDLE
        self._result = None
        self._current_piece_samples = []
        self._piece_idx = 0
        self._acq_elapsed_ms = 0

    # ─── Proprietà di sola lettura ───────────────────────────────────────────

    @property
    def state(self) -> State:
        return self._state

    @property
    def is_running(self) -> bool:
        return self._state not in (State.IDLE, State.DONE)
