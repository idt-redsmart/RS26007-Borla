"""
force_widget.py
---------------
Visualizza la forza attuale letta dalla cella di carico.
"""

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt


class ForceWidget(QFrame):
    """
    Card compatta che mostra il valore di forza corrente in mN.

    Usage:
        widget.set_value(1245.5)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._build_ui()

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
        """Aggiorna la forza visualizzata (in mN)."""
        self._value_lbl.setText(f"{force:.1f} mN")
