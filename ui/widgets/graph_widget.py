"""
graph_widget.py
---------------
Scatter plot per visualizzare i valori di forza campionati (Matplotlib).
Mostra le linee LSL/USL e colora i punti in base all'esito (PASS/FAIL).
"""

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QFrame, QVBoxLayout
import numpy as np

from config import Config
from core.i18n import _

class GraphWidget(QFrame):
    """
    Scatter plot in tempo reale (Matplotlib backend).

    Usage:
        graph.set_limits(lsl=1060, usl=1350)
        graph.add_sample(force_mn)
        graph.clear()
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")

        self._lsl: float = 1060.0
        self._usl: float = 1350.0
        self._samples: list[float] = []
        self._expected_n: int = 1

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.fig = Figure(facecolor="#0b0f1a")
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        
        self._apply_style()
        self.fig.tight_layout()
        layout.addWidget(self.canvas)
        
        # Inizializza plot
        self._redraw()

    def _apply_style(self):
        self.ax.set_facecolor("#0b0f1a")
        self.ax.tick_params(colors="#94a3b8")
        self.ax.xaxis.label.set_color("#94a3b8")
        self.ax.yaxis.label.set_color("#94a3b8")
        for spine in self.ax.spines.values():
            spine.set_color("#94a3b8")
        self.ax.set_ylabel("Forza (mN)")
        self.ax.set_xlabel(_("Pezzo"))
        self.ax.grid(True, alpha=0.15, color="#94a3b8")

    # ─── API ────────────────────────────────────────────────────────────────

    def set_limits(self, lsl: float, usl: float):
        self._lsl = lsl
        self._usl = usl
        self._redraw()

    def set_expected_samples(self, n: int):
        self._expected_n = max(1, n)
        self._redraw()

    def add_sample(self, force: float):
        self._samples.append(force)
        self._redraw()

    def add_samples(self, samples: list[float]):
        self._samples = list(samples)
        self._redraw()

    def clear(self):
        self._samples = []
        self._redraw()

    # ─── Internals ──────────────────────────────────────────────────────────

    def _redraw(self):
        self.ax.clear()
        self._apply_style()

        # Limiti LSL / USL
        self.ax.axhline(self._lsl, color="#ffab00", linestyle="--", linewidth=1.5, zorder=1)
        self.ax.axhline(self._usl, color="#ffab00", linestyle="--", linewidth=1.5, zorder=1)
        self.ax.text(0.01, self._lsl, "LSL", color="#ffab00", transform=self.ax.get_yaxis_transform(), va="bottom", fontsize=9)
        self.ax.text(0.01, self._usl, "USL", color="#ffab00", transform=self.ax.get_yaxis_transform(), va="bottom", fontsize=9)

        if self._samples:
            # L'asse X è il numero del pezzo (1, 2, 3...)
            x = np.arange(1, len(self._samples) + 1)
            y = np.array(self._samples)
            
            # Disegna una singola linea continua per il trend
            self.ax.plot(x, y, color="#00c8ff", linewidth=2.0, zorder=2)

            margin = (self._usl - self._lsl) * 0.5
            y_min = min(self._lsl - margin, min(y) - margin * 0.3)
            y_max = max(self._usl + margin, max(y) + margin * 0.3)
            self.ax.set_ylim(y_min, y_max)
        else:
            margin = (self._usl - self._lsl) * 0.5
            self.ax.set_ylim(self._lsl - margin, self._usl + margin)

        import matplotlib.ticker as ticker
        self.ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        max_x = max(5, len(self._samples))
        self.ax.set_xlim(0.5, max_x + 0.5)
        
        self.fig.tight_layout()
        self.canvas.draw()
