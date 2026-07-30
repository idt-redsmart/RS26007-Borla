"""
home_page.py
------------
Schermata iniziale: TEST | SETTING | STORICO DATI.
Emette segnali verso il controller, non esegue logica.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont

from core.i18n import _


class HomePage(QWidget):
    """
    Schermata Home.

    Signals:
        start_test_requested: l'utente ha premuto TEST
        settings_requested:   l'utente ha premuto SETTING
        history_requested:    l'utente ha premuto STORICO DATI
    """

    start_test_requested = pyqtSignal()
    settings_requested   = pyqtSignal()
    history_requested    = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(60, 50, 60, 50)
        root.setSpacing(0)

        # ── Header ──────────────────────────────────────────────────────────
        header = QVBoxLayout()
        header.setSpacing(6)

        company = QLabel("Industrie Borla srl")
        company.setObjectName("companyLabel")
        company.setAlignment(Qt.AlignCenter)

        title = QLabel(_("ELASTIC REACTION TEST"))
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel(_("PF0924 — Controllo Forza di Reazione Elastica"))
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignCenter)

        header.addWidget(company)
        header.addWidget(title)
        header.addWidget(subtitle)

        # ── Separatore ──────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #00c8ff; margin: 24px 120px;")

        # ── Pulsanti principali ──────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(24)

        self._btn_test     = self._make_home_btn("▶  " + _("TEST"),         _("Avvia una nuova sessione di collaudo"))
        self._btn_settings = self._make_home_btn("⚙  " + _("SETTING"),      _("Accedi alle impostazioni (richiede password)"))
        self._btn_history  = self._make_home_btn("📋  " + _("STORICO DATI"), _("Visualizza lo storico dei collaudi"))

        btn_layout.addWidget(self._btn_test)
        btn_layout.addWidget(self._btn_settings)
        btn_layout.addWidget(self._btn_history)

        # ── Footer ──────────────────────────────────────────────────────────
        footer_lbl = QLabel(_("Versione 1.0.0  ·  IDT Solution S.r.l.s.b."))
        footer_lbl.setObjectName("subtitleLabel")
        footer_lbl.setAlignment(Qt.AlignCenter)

        # ── Assembly ────────────────────────────────────────────────────────
        root.addLayout(header)
        root.addWidget(sep)
        root.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        root.addLayout(btn_layout)
        root.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        root.addWidget(footer_lbl)

        # ── Connessioni ─────────────────────────────────────────────────────
        self._btn_test.clicked.connect(self.start_test_requested)
        self._btn_settings.clicked.connect(self.settings_requested)
        self._btn_history.clicked.connect(self.history_requested)

    def _make_home_btn(self, text: str, tooltip: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("homeBtn")
        btn.setToolTip(tooltip)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        btn.setMinimumHeight(120)
        return btn
