"""
force_widget.py
---------------
Visualizza la forza attuale letta dalla cella di carico.
"""

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer

# I campioni arrivano a decine al secondo: il numero si aggiorna solo
# REFRESH_MS ms con la media del periodo, così l'operatore riesce a leggerlo
_REFRESH_MS = 250


class ForceWidget(QFrame):
    """
    Card compatta che mostra il valore di forza corrente in mN.

    Usage:
        widget.set_value(1245.5)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._sum   = 0.0
        self._count = 0
        self._build_ui()

        self._timer = QTimer(self)
        self._timer.setInterval(_REFRESH_MS)
        self._timer.timeout.connect(self._refresh)
        self._timer.start()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)

        key_lbl = QLabel("FORCE")
        key_lbl.setObjectName("statKeyLabel")
        key_lbl.setAlignment(Qt.AlignCenter)

        self._value_lbl = QLabel("— mN")
        self._value_lbl.setObjectName("valueLabel")
        self._value_lbl.setAlignment(Qt.AlignCenter)

        layout.addWidget(key_lbl)
        layout.addWidget(self._value_lbl)

    def set_value(self, force: float):
        """Accumula un campione di forza (in mN); il display si aggiorna in _refresh."""
        self._sum   += force
        self._count += 1

    def _refresh(self):
        """Mostra la media dei campioni arrivati dall'ultimo aggiornamento."""
        if self._count == 0:
            return  # nessun campione nuovo: resta l'ultimo valore

        self._value_lbl.setText(f"{self._sum / self._count:.1f} mN")
        self._sum   = 0.0
        self._count = 0
