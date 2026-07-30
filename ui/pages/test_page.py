"""
test_page.py
------------
Schermata di collaudo attivo.
Mostra in tempo reale: forza, grafico scatter, statistiche, timer, contatore pezzi.
Non calcola nulla — aggiorna solo la UI.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QProgressBar, QSizePolicy
)
from PyQt5.QtCore import pyqtSignal, Qt

from ui.widgets.graph_widget import GraphWidget
from ui.widgets.statistics_widget import StatisticsWidget
from ui.widgets.force_widget import ForceWidget
from core.i18n import _


class TestPage(QWidget):
    """
    Pagina di collaudo in corso.

    Signals:
        end_test_requested: l'utente ha premuto END TEST
    """

    end_test_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # ─── Build ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        # ══ Colonna SINISTRA ════════════════════════════════════════════════
        left = QVBoxLayout()
        left.setSpacing(12)

        # -- Header branding -------------------------------------------------
        hdr = self._make_header()
        left.addWidget(hdr)

        # -- Forza corrente --------------------------------------------------
        self._force_widget = ForceWidget()
        self._force_widget.setMinimumHeight(90)
        left.addWidget(self._force_widget)

        # -- Limiti ----------------------------------------------------------
        limits_frame = QFrame()
        limits_frame.setObjectName("card")
        limits_lay = QHBoxLayout(limits_frame)
        limits_lay.setContentsMargins(16, 10, 16, 10)

        self._lsl_lbl = QLabel("LSL  1060 mN")
        self._lsl_lbl.setObjectName("limitLabel")
        self._usl_lbl = QLabel("USL  1350 mN")
        self._usl_lbl.setObjectName("limitLabel")
        self._lsl_lbl.setStyleSheet("color: #ffab00; font-size: 14px; font-weight: 700;")
        self._usl_lbl.setStyleSheet("color: #ffab00; font-size: 14px; font-weight: 700;")

        limits_lay.addWidget(self._lsl_lbl)
        limits_lay.addStretch()
        limits_lay.addWidget(self._usl_lbl)
        left.addWidget(limits_frame)

        # -- Statistiche -----------------------------------------------------
        self._stats = StatisticsWidget()
        left.addWidget(self._stats)

        # -- Stato pezzo corrente --------------------------------------------
        self._piece_status = QLabel("● " + _("ATTESA TRIGGER"))
        self._piece_status.setAlignment(Qt.AlignCenter)
        self._piece_status.setStyleSheet(
            "color: #94a3b8; font-size: 15px; font-weight: 700; "
            "background: #111827; border: 1px solid #2d3748; "
            "border-radius: 8px; padding: 12px;"
        )
        left.addWidget(self._piece_status)

        # -- Timer acquisizione ----------------------------------------------
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setFormat("Acquisizione: %p%")
        self._progress.setFixedHeight(28)
        left.addWidget(self._progress)

        # -- END TEST --------------------------------------------------------
        end_btn = QPushButton("⏹  " + _("TERMINA COLLAUDO"))
        end_btn.setObjectName("dangerBtn")
        end_btn.setMinimumHeight(60)
        end_btn.clicked.connect(self.end_test_requested)
        left.addWidget(end_btn)

        # ══ Colonna DESTRA: Grafico ═════════════════════════════════════════
        self._graph = GraphWidget()
        self._graph.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ── Assembly ─────────────────────────────────────────────────────────
        root.addLayout(left, stretch=1)
        root.addWidget(self._graph, stretch=2)

    def _make_header(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("accentCard")
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(16, 10, 16, 10)

        company = QLabel("Industrie Borla srl")
        company.setObjectName("companyLabel")

        title = QLabel("ELASTIC REACTION TEST")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #e2e8f0; letter-spacing: 2px;")

        self._session_lbl = QLabel("—")
        self._session_lbl.setObjectName("statKeyLabel")
        self._session_lbl.setAlignment(Qt.AlignRight)

        lay.addWidget(company)
        lay.addStretch()
        lay.addWidget(title)
        lay.addStretch()
        lay.addWidget(self._session_lbl)
        return frame

    # ─── Public API ─────────────────────────────────────────────────────────

    def set_session_info(self, operator: str, mould: str):
        self._session_lbl.setText(f"{operator}  |  {mould}")

    def set_limits(self, lsl: float, usl: float):
        self._lsl_lbl.setText(f"LSL  {lsl:.0f} mN")
        self._usl_lbl.setText(f"USL  {usl:.0f} mN")
        self._graph.set_limits(lsl, usl)

    def set_expected_samples(self, n: int):
        self._graph.set_expected_samples(n)

    def set_force(self, force: float):
        self._force_widget.set_value(force)

    def set_status_waiting(self):
        self._piece_status.setText("● " + _("ATTESA TRIGGER"))
        self._piece_status.setStyleSheet(
            "color: #94a3b8; font-size: 15px; font-weight: 700; "
            "background: #111827; border: 1px solid #2d3748; "
            "border-radius: 8px; padding: 12px;"
        )
        self._progress.setValue(0)

    def set_status_acquiring(self):
        self._piece_status.setText("● " + _("ACQUISIZIONE IN CORSO"))
        self._piece_status.setStyleSheet(
            "color: #00c8ff; font-size: 15px; font-weight: 700; "
            "background: #0a1929; border: 1px solid #00c8ff; "
            "border-radius: 8px; padding: 12px;"
        )

    def set_progress(self, percent: int):
        self._progress.setValue(percent)

    def set_piece_data(self, samples: list):
        self._graph.add_samples(samples)

    def set_statistics(self, qty, min_v, mean, max_v, std, rng):
        self._stats.set_values(qty=qty, min_v=min_v, mean=mean,
                               max_v=max_v, std=std, rng=rng)

    def reset(self):
        self._graph.clear()
        self._stats.clear()
        self._progress.setValue(0)
        self._force_widget.set_value(0.0)
        self.set_status_waiting()
