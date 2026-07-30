"""
statistics_widget.py
--------------------
Mostra le statistiche di sessione aggiornate in tempo reale:
QTY, MIN, MEAN, MAX, STD, RANGE.
"""

from PyQt5.QtWidgets import (
    QFrame, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout
)
from PyQt5.QtCore import Qt


class _StatCell(QFrame):
    """Singola cella: etichetta + valore."""

    def __init__(self, key: str, unit: str = "mN", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._unit = unit

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(2)

        self._key_lbl = QLabel(key)
        self._key_lbl.setObjectName("statKeyLabel")
        self._key_lbl.setAlignment(Qt.AlignCenter)

        self._val_lbl = QLabel("—")
        self._val_lbl.setObjectName("statValueLabel")
        self._val_lbl.setAlignment(Qt.AlignCenter)

        lay.addWidget(self._key_lbl)
        lay.addWidget(self._val_lbl)

    def set_value(self, value: float):
        if self._unit:
            self._val_lbl.setText(f"{value:.1f} {self._unit}")
        else:
            self._val_lbl.setText(str(int(value)))

    def clear(self):
        self._val_lbl.setText("—")


class StatisticsWidget(QFrame):
    """
    Griglia di statistiche 2×3 (QTY / MIN / MEAN / MAX / STD / RANGE).

    Usage:
        stats.set_values(qty=33, min_v=1120, mean=1161, max_v=1215, std=24.8, rng=95)
        stats.clear()
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._build_ui()

    def _build_ui(self):
        grid = QGridLayout(self)
        grid.setContentsMargins(12, 12, 12, 12)
        grid.setSpacing(8)

        self._qty  = _StatCell("Q.TY",  unit="")
        self._min  = _StatCell("MIN",   unit="mN")
        self._mean = _StatCell("MEAN",  unit="mN")
        self._max  = _StatCell("MAX",   unit="mN")
        self._std  = _StatCell("STD",   unit="mN")
        self._rng  = _StatCell("RANGE", unit="mN")

        grid.addWidget(self._qty,  0, 0)
        grid.addWidget(self._min,  0, 1)
        grid.addWidget(self._mean, 0, 2)
        grid.addWidget(self._max,  1, 0)
        grid.addWidget(self._std,  1, 1)
        grid.addWidget(self._rng,  1, 2)

    def set_values(
        self,
        qty: int   = 0,
        min_v: float = 0.0,
        mean: float  = 0.0,
        max_v: float = 0.0,
        std: float   = 0.0,
        rng: float   = 0.0,
    ):
        self._qty.set_value(qty)
        self._min.set_value(min_v)
        self._mean.set_value(mean)
        self._max.set_value(max_v)
        self._std.set_value(std)
        self._rng.set_value(rng)

    def clear(self):
        for cell in (self._qty, self._min, self._mean,
                     self._max, self._std, self._rng):
            cell.clear()
