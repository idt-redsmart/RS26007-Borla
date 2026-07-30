"""
report_page.py
--------------
Visualizza un report PDF già generato tramite un viewer integrato.
Usa QWebEngineView se disponibile, altrimenti mostra le statistiche
direttamente nel widget (fallback senza dipendenze esterne).
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QScrollArea, QSizePolicy, QGridLayout, QStackedWidget
)
from PyQt5.QtCore import pyqtSignal, Qt, QUrl

from ui.widgets.graph_widget import GraphWidget
from core.i18n import _


class ReportPage(QWidget):
    """
    Pagina di visualizzazione report.

    Signals:
        back_requested: l'utente ha premuto BACK
    """

    back_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # ─── Build ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 30, 40, 30)
        root.setSpacing(16)

        # ── Header ──────────────────────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel(_("REPORT"))
        title.setObjectName("titleLabel")
        back_btn = QPushButton("← " + _("INDIETRO"))
        back_btn.setObjectName("backBtn")
        back_btn.clicked.connect(self.back_requested)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(back_btn)

        # ── Tentativo di caricare QWebEngineView per PDF ─────────────────────
        self._pdf_loaded = False
        self._viewer = None
        try:
            from PyQt5.QtWebEngineWidgets import QWebEngineView
            self._viewer = QWebEngineView()
            self._viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self._pdf_loaded = True
        except ImportError:
            pass

        # ── Stacked Widget per Corpo Centrale ────────────────────────────────
        self._stack = QStackedWidget()

        # ── Fallback: mostra dati come card ──────────────────────────────────
        self._fallback = self._build_fallback()
        self._stack.addWidget(self._fallback)

        # ── Assembly ─────────────────────────────────────────────────────────
        root.addLayout(header)
        root.addWidget(self._stack)
        
        if self._pdf_loaded and self._viewer:
            self._stack.addWidget(self._viewer)

    def _build_fallback(self) -> QScrollArea:
        """Costruisce il viewer fallback con dati e grafico."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")

        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setSpacing(16)
        lay.setContentsMargins(0, 0, 0, 0)

        # Header report
        hdr = QFrame()
        hdr.setObjectName("accentCard")
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(24, 16, 24, 16)

        company_lbl = QLabel("Industrie Borla srl")
        company_lbl.setObjectName("companyLabel")
        title_lbl = QLabel(_("ELASTIC REACTION TEST REPORT"))
        title_lbl.setStyleSheet(
            "font-size: 18px; font-weight: 700; color: #e2e8f0; letter-spacing: 2px;"
        )
        part_lbl = QLabel("PF0924")
        part_lbl.setStyleSheet("font-size: 14px; color: #94a3b8;")

        hdr_lay.addWidget(company_lbl)
        hdr_lay.addStretch()
        hdr_lay.addWidget(title_lbl)
        hdr_lay.addStretch()
        hdr_lay.addWidget(part_lbl)

        # Dati sessione
        info_frame = QFrame()
        info_frame.setObjectName("card")
        self._make_info_grid(info_frame)

        # Statistiche
        stats_frame = QFrame()
        stats_frame.setObjectName("card")
        self._make_stats_grid(stats_frame)

        # Grafico
        self._report_graph = GraphWidget()
        self._report_graph.setMinimumHeight(400)

        # Esito
        self._result_frame = QFrame()
        self._result_frame.setObjectName("card")
        result_lay = QHBoxLayout(self._result_frame)
        result_lay.setContentsMargins(24, 16, 24, 16)
        result_lbl = QLabel(_("INSPECTION RESULT"))
        result_lbl.setObjectName("statKeyLabel")
        self._result_value = QLabel("—")
        self._result_value.setObjectName("passLabel")
        self._result_value.setAlignment(Qt.AlignRight)
        result_lay.addWidget(result_lbl)
        result_lay.addStretch()
        result_lay.addWidget(self._result_value)

        lay.addWidget(hdr)
        lay.addWidget(info_frame)
        lay.addWidget(stats_frame)
        lay.addWidget(self._report_graph)
        lay.addWidget(self._result_frame)

        scroll.setWidget(container)
        return scroll

    def _make_info_grid(self, parent: QFrame) -> None:
        grid = QGridLayout(parent)
        grid.setContentsMargins(24, 16, 24, 16)
        grid.setSpacing(12)
        self._info_labels = {}
        fields = ["DATE", "OPERATOR", "MOULD", "PRODUCTION LOT", "RAW MATERIAL LOT"]
        for i, f in enumerate(fields):
            row, col = divmod(i, 2)
            key_lbl = QLabel(_(f))
            key_lbl.setObjectName("statKeyLabel")
            val_lbl = QLabel("—")
            val_lbl.setStyleSheet("font-size: 15px; font-weight: 600; color: #e2e8f0;")
            self._info_labels[f] = val_lbl
            grid.addWidget(key_lbl, row, col * 2)
            grid.addWidget(val_lbl, row, col * 2 + 1)

    def _make_stats_grid(self, parent: QFrame) -> None:
        grid = QGridLayout(parent)
        grid.setContentsMargins(24, 16, 24, 16)
        grid.setSpacing(12)
        self._stat_labels = {}
        fields = [
            ("QTY",                 ""),
            ("LOWER SPEC LIMIT",    "mN"),
            ("UPPER SPEC LIMIT",    "mN"),
            ("MIN DETECTED VALUE",  "mN"),
            ("MEAN VALUE",          "mN"),
            ("MAX DETECTED VALUE",  "mN"),
            ("RANGE",               "mN"),
            ("STANDARD DEVIATION",  "mN"),
        ]
        for i, (f, unit) in enumerate(fields):
            row, col = divmod(i, 2)
            key_lbl = QLabel(_(f))
            key_lbl.setObjectName("statKeyLabel")
            val_lbl = QLabel("—")
            val_lbl.setStyleSheet("font-size: 15px; font-weight: 600; color: #e2e8f0;")
            self._stat_labels[f] = (val_lbl, unit)
            grid.addWidget(key_lbl, row, col * 2)
            grid.addWidget(val_lbl, row, col * 2 + 1)

    # ─── Public API ─────────────────────────────────────────────────────────

    def load_report(self, data: dict):
        """
        Carica i dati del report.

        Args:
            data: dict con chiavi: date, operator, mould, production_lot,
                  raw_material_lot, qty, lower_limit, upper_limit,
                  min_v, mean, max_v, rng, std, result (PASS/FAIL),
                  samples (list[float]), pdf_path (str)
        """
        pdf_path = data.get("pdf_path", "")
        import os
        
        if self._pdf_loaded and self._viewer and pdf_path and os.path.exists(pdf_path):
            from PyQt5.QtCore import QUrl
            self._viewer.load(QUrl.fromLocalFile(pdf_path))
            self._stack.setCurrentWidget(self._viewer)
            return

        self._stack.setCurrentWidget(self._fallback)
        # ── Fallback ─────────────────────────────────────────────────────────
        info_map = {
            "DATE":             data.get("date", "—"),
            "OPERATOR":         data.get("operator", "—"),
            "MOULD":            data.get("mould", "—"),
            "PRODUCTION LOT":   data.get("production_lot", "—"),
            "RAW MATERIAL LOT": data.get("raw_material_lot", "—"),
        }
        for k, v in info_map.items():
            if k in self._info_labels:
                self._info_labels[k].setText(str(v))

        stat_map = {
            "QTY":                data.get("qty", 0),
            "LOWER SPEC LIMIT":   data.get("lower_limit", 0),
            "UPPER SPEC LIMIT":   data.get("upper_limit", 0),
            "MIN DETECTED VALUE": data.get("min_v", 0),
            "MEAN VALUE":         data.get("mean", 0),
            "MAX DETECTED VALUE": data.get("max_v", 0),
            "RANGE":              data.get("rng", 0),
            "STANDARD DEVIATION": data.get("std", 0),
        }
        for k, v in stat_map.items():
            if k in self._stat_labels:
                lbl, unit = self._stat_labels[k]
                lbl.setText(f"{v:.1f} {unit}".strip() if unit else str(int(v)))

        # Grafico
        samples = data.get("samples", [])
        if samples:
            lsl = data.get("lower_limit", 1060)
            usl = data.get("upper_limit", 1350)
            self._report_graph.set_limits(lsl, usl)
            
            # Estrai solo i valori di forza
            force_values = []
            for s in samples:
                if isinstance(s, dict) and "force_mn" in s:
                    force_values.append(s["force_mn"])
                elif isinstance(s, (int, float)):
                    force_values.append(s)
            
            self._report_graph.add_samples(force_values)

        # Esito
        result = data.get("result", "—")
        self._result_value.setText(result)
        if result == "PASS":
            self._result_value.setObjectName("passLabel")
        else:
            self._result_value.setObjectName("failLabel")
        self._result_value.style().unpolish(self._result_value)
        self._result_value.style().polish(self._result_value)
