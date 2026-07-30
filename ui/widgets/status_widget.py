"""
status_widget.py
----------------
Barra di stato in fondo alla finestra: indica lo stato della cella di carico
e lo stato generale dell'applicazione.
"""

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from core.i18n import _


class StatusWidget(QFrame):
    """
    Barra di stato con indicatori LED-like.

    Usage:
        status.set_loadcell(True)
        status.set_message("Attesa trigger...")
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedHeight(44)
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(24)

        # LED cella di carico
        self._lc_dot = QLabel("●")
        self._lc_dot.setStyleSheet("color: #ff3d57; font-size: 16px;")
        lc_lbl = QLabel(_("CELLA DI CARICO"))
        lc_lbl.setObjectName("statKeyLabel")

        # Messaggio di stato
        self._msg_lbl = QLabel(_("Sistema pronto"))
        self._msg_lbl.setObjectName("statKeyLabel")
        self._msg_lbl.setStyleSheet("color: #94a3b8;")

        layout.addWidget(self._lc_dot)
        layout.addWidget(lc_lbl)
        layout.addStretch()
        layout.addWidget(self._msg_lbl)

    def set_loadcell(self, connected: bool):
        """Aggiorna l'indicatore LED della cella di carico."""
        color = "#00e676" if connected else "#ff3d57"
        self._lc_dot.setStyleSheet(f"color: {color}; font-size: 16px;")

    def set_message(self, text: str, color: str = "#94a3b8"):
        """Imposta il messaggio di stato."""
        self._msg_lbl.setText(text)
        self._msg_lbl.setStyleSheet(f"color: {color};")
