"""
main_window.py
--------------
Finestra principale dell'applicazione.
Contiene un QStackedWidget con tutte le pagine.
Collega la UI al TestController tramite segnali — nessuna logica di business qui.
"""

import os

from PyQt5.QtWidgets import (
    QMainWindow, QStackedWidget, QWidget,
    QVBoxLayout, QHBoxLayout, QMessageBox, QLineEdit
)
from PyQt5.QtCore import Qt

from ui.pages.home_page       import HomePage
from ui.pages.new_test_page   import NewTestPage
from ui.pages.test_page       import TestPage
from ui.pages.settings_page   import SettingsPage
from ui.pages.history_page    import HistoryPage
from ui.pages.report_page     import ReportPage
from ui.widgets.status_widget    import StatusWidget
from ui.widgets.password_dialog  import PasswordDialog
from ui.widgets.logo_widget      import LogoWidget

from core.i18n import _

from core.test_controller import TestController
from core.database        import Database
from config import Config


class MainWindow(QMainWindow):
    """
    Finestra unica dell'applicazione.
    Espone show_page(name) per navigare tra le pagine.
    """

    PAGE_HOME     = "home"
    PAGE_NEW_TEST = "new_test"
    PAGE_TEST     = "test"
    PAGE_SETTINGS = "settings"
    PAGE_HISTORY  = "history"
    PAGE_REPORT   = "report"

    def __init__(self, parent=None):
        super().__init__(parent)

        # ── Infrastruttura ────────────────────────────────────────────────────
        self._db         = Database(Config.database_path)
        self._controller = TestController(db=self._db, parent=self)

        self._build_ui()
        self._connect_page_signals()
        self._connect_controller_signals()

    @property
    def controller(self) -> TestController:
        """Esposto per permettere a main.py di collegare il worker."""
        return self._controller

    # ─── Build ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.setWindowTitle("ElasticReactionTest  —  Industrie Borla srl")
        self.setMinimumSize(1280, 800)

        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Stack ─────────────────────────────────────────────────────────────
        self._stack = QStackedWidget()

        self.home     = HomePage()
        self.new_test = NewTestPage()
        self.test     = TestPage()
        self.settings = SettingsPage()
        self.history  = HistoryPage()
        self.report   = ReportPage()

        self._pages: dict[str, QWidget] = {
            self.PAGE_HOME:     self.home,
            self.PAGE_NEW_TEST: self.new_test,
            self.PAGE_TEST:     self.test,
            self.PAGE_SETTINGS: self.settings,
            self.PAGE_HISTORY:  self.history,
            self.PAGE_REPORT:   self.report,
        }

        for page in self._pages.values():
            self._stack.addWidget(page)

        # ── Status bar ────────────────────────────────────────────────────────
        self._status = StatusWidget()

        # ── Topbar logo (sopra lo stack, parte del layout — non overlay) ──────
        topbar = QWidget()
        topbar.setObjectName("logoTopbar")
        topbar.setFixedHeight(60)
        topbar_lay = QHBoxLayout(topbar)
        topbar_lay.setContentsMargins(14, 4, 14, 4)
        topbar_lay.setSpacing(0)
        self._logo = LogoWidget(parent=topbar, max_h=48, max_w=200,
                                align=Qt.AlignLeft | Qt.AlignVCenter)
        topbar_lay.addWidget(self._logo)
        topbar_lay.addStretch()

        root.addWidget(topbar)
        root.addWidget(self._stack)
        root.addWidget(self._status)

    # ─── Segnali pagine → navigazione ──────────────────────────────────────

    def _connect_page_signals(self):
        # Home
        self.home.start_test_requested.connect(lambda: self.show_page(self.PAGE_NEW_TEST))
        self.home.settings_requested.connect(self._open_settings_with_password)
        self.home.history_requested.connect(self._open_history)

        # NewTest
        self.new_test.back_requested.connect(lambda: self.show_page(self.PAGE_HOME))
        self.new_test.start_confirmed.connect(self._on_start_confirmed)

        # Test
        self.test.end_test_requested.connect(self._on_end_test)

        # Settings
        self.settings.back_requested.connect(lambda: self.show_page(self.PAGE_HOME))
        self.settings.settings_saved.connect(self._on_settings_saved)

        # History Page
        self.history.back_requested.connect(lambda: self.show_page(self.PAGE_HOME))
        self.history.view_report_requested.connect(self._on_view_report)
        self.history.delete_report_requested.connect(self._on_delete_report)

        # Report
        self.report.back_requested.connect(lambda: self.show_page(self.PAGE_HISTORY))
        self.report.regenerate_requested.connect(self._on_regenerate_report)

    # ─── Segnali Controller → GUI ────────────────────────────────────────────

    def _connect_controller_signals(self):
        ctrl = self._controller

        # Forza corrente → widget forza sulla TestPage
        ctrl.force_updated.connect(self.test.set_force)

        # Dati del pezzo (inviati in blocco a fine acquisizione)
        ctrl.piece_data_ready.connect(self.test.set_piece_data)

        # Messaggio di stato → status bar
        ctrl.status_changed.connect(
            lambda txt, color: self._status.set_message(txt, color)
        )

        # Avvio acquisizione → UI
        ctrl.acquiring_started.connect(self.test.set_status_acquiring)

        # Progresso acquisizione → barra di avanzamento
        ctrl.acquiring_progress.connect(self.test.set_progress)

        # Pezzo completato → notifica visiva
        ctrl.piece_done.connect(self._on_piece_done)

        # Statistiche aggiornate → widget statistiche
        ctrl.stats_updated.connect(
            lambda d: self.test.set_statistics(
                qty  = d["qty"],
                min_v = d["min"],
                mean  = d["mean"],
                max_v = d["max"],
                std   = d["std"],
                rng   = d["range"],
            )
        )

        # Sessione completata
        ctrl.session_done.connect(self._on_session_done)

        # Errori → MessageBox
        ctrl.error_occurred.connect(
            lambda msg: QMessageBox.warning(self, _("Errore"), msg)
        )

    # ─── Navigation ─────────────────────────────────────────────────────────

    def show_page(self, name: str):
        page = self._pages.get(name)
        if page:
            self._stack.setCurrentWidget(page)

    # ─── Slot pagine ────────────────────────────────────────────────────────

    def _on_start_confirmed(self, data: dict):
        """L'operatore ha premuto START TEST — prepara UI e avvia il controller."""
        self.test.reset()
        self.test.set_session_info(
            operator = data.get("OPERATOR", "—"),
            mould    = data.get("MOULD", "—"),
        )
        self.test.set_limits(Config.lower_limit, Config.upper_limit)
        self.test.set_expected_samples(int(Config.test_time * Config.sampling_rate))
        self.show_page(self.PAGE_TEST)

        self._controller.start_session(
            operator         = data.get("OPERATOR", ""),
            mould            = data.get("MOULD", ""),
            production_lot   = data.get("PRODUCTION LOT", ""),
            raw_material_lot = data.get("RAW MATERIAL", ""),
        )
        self._status.set_message(_("ATTESA TRIGGER..."), "#94a3b8")

    def _on_end_test(self):
        """L'operatore ha premuto END TEST."""
        self._controller.end_session()

    def _on_piece_done(self, piece_idx: int, passed: bool):
        """Feedback visivo al completamento di ogni pezzo."""
        color = "#00e676" if passed else "#ff3d57"
        label = _("OK ✓") if passed else _("FUORI LIMITE ✗")
        self._status.set_message(
            f"{_('Pezzo')} #{piece_idx} — {label}", color
        )
        self.test.set_status_waiting()

    def _on_session_done(self, result):
        """
        Sessione completata: aggiorna la history, mostra il report,
        notifica l'operatore con il risultato.
        """
        self._open_history()

        # Mostra esito con MessageBox
        icon = QMessageBox.Information if result.result == "PASS" else QMessageBox.Warning
        QMessageBox(
            icon,
            _("Sessione completata"),
            f"{_('Risultato')}:  {result.result}\n"
            f"{_('Pezzi')}:      {result.qty}\n"
            f"Min:        {result.min_mn:.1f} mN\n"
            f"Mean:       {result.mean_mn:.1f} mN\n"
            f"Max:        {result.max_mn:.1f} mN\n"
            f"Std:        {result.std_mn:.1f} mN",
            parent=self,
        ).exec_()

    # ─── Settings ────────────────────────────────────────────────────────────

    def _open_settings_with_password(self):
        dlg = PasswordDialog(
            parent=self,
            title=_("Accesso protetto"),
            prompt=_("Inserire la password:"),
        )
        if dlg.exec_() == PasswordDialog.Accepted:
            password    = dlg.password()
            db_password = self._db.get_password()
            if password == db_password:
                self.settings.load_current_values(db_password)
                self.show_page(self.PAGE_SETTINGS)
            else:
                QMessageBox.warning(self, _("Accesso negato"), _("Password errata."))

    def _on_settings_saved(self, values: dict):
        if "password" in values:
            self._db.set_password(values.pop("password"))
        for key, value in values.items():
            Config.set(key, value)
        Config.save()
        # Aggiorna anche il controller con i nuovi limiti se in idle
        QMessageBox.information(self, "Salvato", "Impostazioni salvate correttamente.")
        self.show_page(self.PAGE_HOME)

    # ─── History ─────────────────────────────────────────────────────────────

    def _open_history(self):
        records = self._db.load_tests()
        # Adatta i nomi delle colonne al formato atteso dalla HistoryPage
        mapped = [
            {
                "id":    r["id"],
                "date":  r["date"][:16].replace("T", " "),
                "mould": r["mould"],
                "min":   r["min_mn"],
                "mean":  r["mean_mn"],
                "max":   r["max_mn"],
            }
            for r in records
        ]
        self.history.load_records(mapped)
        self.show_page(self.PAGE_HISTORY)

    def _on_view_report(self, test_id: int):
        record = self._db.load_test(test_id)
        if record is None:
            QMessageBox.warning(self, "Errore", f"Collaudo #{test_id} non trovato.")
            return

        samples_raw = record.get("samples", [])
        self.report.load_report({
            "id":               record["id"],
            "date":             record["date"][:16].replace("T", " "),
            "operator":         record["operator"],
            "mould":            record["mould"],
            "production_lot":   record["production_lot"],
            "raw_material_lot": record["raw_material_lot"],
            "qty":              record["qty"],
            "lower_limit":      record["lower_limit"],
            "upper_limit":      record["upper_limit"],
            "min_v":            record["min_mn"],
            "mean":             record["mean_mn"],
            "max_v":            record["max_mn"],
            "rng":              record["range_mn"],
            "std":              record["std_mn"],
            "result":           record["result"],
            "samples":          samples_raw,
            "pdf_path":         record["pdf_path"],
        })
        self.show_page(self.PAGE_REPORT)

    def _on_delete_report(self, test_id: int):
        reply = QMessageBox.question(
            self,
            _("Conferma eliminazione"),
            _("Sei sicuro di voler eliminare il report selezionato? L'operazione è irreversibile."),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._db.delete_test(test_id)
            self._open_history()  # Ricarica la tabella

    def _on_regenerate_report(self, test_id: int):
        record = self._db.load_test(test_id)
        if record is None:
            return
            
        from core.pdf_generator import generate_report
        import logging
        log = logging.getLogger(__name__)
        
        try:
            data_for_pdf = {
                "id": record["id"],
                "date": record["date"],
                "operator": record["operator"],
                "mould": record["mould"],
                "production_lot": record["production_lot"],
                "raw_material_lot": record["raw_material_lot"],
                "qty": record["qty"],
                "lower_limit": record["lower_limit"],
                "upper_limit": record["upper_limit"],
                "min_mn": record["min_mn"],
                "mean_mn": record["mean_mn"],
                "max_mn": record["max_mn"],
                "range_mn": record["range_mn"],
                "std_mn": record["std_mn"],
                "result": record["result"],
                "samples": record.get("samples", []),
                "part_number": Config.part_number
            }
            
            pdf_path = generate_report(data_for_pdf, Config.reports_path)
            self._db.update_pdf_path(test_id, pdf_path)
            log.info(f"Report PDF rigenerato con successo in {pdf_path}")
            
            QMessageBox.information(self, _("Successo"), _("Report PDF rigenerato con successo."))
            self._on_view_report(test_id)  # Ricarica il report
        except Exception as e:
            log.error(f"Errore rigenerazione PDF: {e}", exc_info=True)
            QMessageBox.critical(self, _("Errore"), f"{_('Impossibile generare il PDF')}:\n{e}")

    # ─── Utility ──────────────────────────────────────────────────────────────

    def set_loadcell_status(self, connected: bool):
        self._status.set_loadcell(connected)
