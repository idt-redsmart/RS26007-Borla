"""
trend_graph_widget.py
---------------------
Visualizza 3 grafici sovrapposti per l'andamento dei valori MIN, MAX e MEAN
su più pezzi (campioni) della stessa sessione, usando Matplotlib.
"""

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QFrame, QVBoxLayout
import numpy as np

class TrendGraphWidget(QFrame):
    """
    3 grafici sovrapposti per MIN, MAX e MEAN (Matplotlib backend).
    
    Usage:
        graph.set_limits(lsl=1060, usl=1350)
        graph.add_piece_stats(qty, min_v, max_v, mean)
        graph.clear()
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")

        self._lsl: float = 1060.0
        self._usl: float = 1350.0
        
        self._x_data: list[int] = []
        self._min_data: list[float] = []
        self._max_data: list[float] = []
        self._mean_data: list[float] = []

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.fig = Figure(facecolor="#0b0f1a", figsize=(5, 8))
        self.canvas = FigureCanvas(self.fig)
        
        # 3 subplots sharing X axis
        self.ax_max = self.fig.add_subplot(311)
        self.ax_mean = self.fig.add_subplot(312, sharex=self.ax_max)
        self.ax_min = self.fig.add_subplot(313, sharex=self.ax_max)
        
        self.axes = [self.ax_max, self.ax_mean, self.ax_min]

        layout.addWidget(self.canvas)
        self._redraw()

    def _apply_style(self):
        titles = ["Trend MASSIMO", "Trend MEDIA", "Trend MINIMO"]
        ylabels = ["Max (mN)", "Media (mN)", "Min (mN)"]
        
        for i, ax in enumerate(self.axes):
            ax.set_facecolor("#0b0f1a")
            ax.tick_params(colors="#94a3b8")
            ax.xaxis.label.set_color("#94a3b8")
            ax.yaxis.label.set_color("#94a3b8")
            for spine in ax.spines.values():
                spine.set_color("#94a3b8")
            ax.grid(True, alpha=0.15, color="#94a3b8")
            ax.set_title(titles[i], color="#94a3b8", fontsize=10, pad=3)
            ax.set_ylabel(ylabels[i])
            
            # Hide X tick labels for top two plots
            if ax != self.ax_min:
                ax.tick_params(labelbottom=False)

        self.ax_min.set_xlabel("Pezzo #")

    # ─── API ────────────────────────────────────────────────────────────────

    def set_limits(self, lsl: float, usl: float):
        self._lsl = lsl
        self._usl = usl
        self._redraw()

    def add_piece_stats(self, qty: int, min_v: float, max_v: float, mean_v: float):
        self._x_data.append(qty)
        self._min_data.append(min_v)
        self._max_data.append(max_v)
        self._mean_data.append(mean_v)
        self._redraw()

    def load_all_pieces(self, x_data: list, min_data: list, max_data: list, mean_data: list):
        self._x_data = x_data
        self._min_data = min_data
        self._max_data = max_data
        self._mean_data = mean_data
        self._redraw()

    def clear(self):
        self._x_data.clear()
        self._min_data.clear()
        self._max_data.clear()
        self._mean_data.clear()
        self._redraw()

    # ─── Internals ──────────────────────────────────────────────────────────

    def _redraw(self):
        for ax in self.axes:
            ax.clear()
        self._apply_style()

        datasets = [self._max_data, self._mean_data, self._min_data]
        
        for ax, data in zip(self.axes, datasets):
            ax.axhline(self._lsl, color="#ffab00", linestyle="--", linewidth=1.5, zorder=1)
            ax.axhline(self._usl, color="#ffab00", linestyle="--", linewidth=1.5, zorder=1)
            ax.text(0.01, self._lsl, "LSL", color="#ffab00", transform=ax.get_yaxis_transform(), va="bottom", fontsize=9)
            ax.text(0.01, self._usl, "USL", color="#ffab00", transform=ax.get_yaxis_transform(), va="bottom", fontsize=9)

            if self._x_data and data:
                ax.plot(self._x_data, data, color="#00c8ff", marker="o", markersize=5, linewidth=1.5, zorder=3)
                
                margin = (self._usl - self._lsl) * 0.3
                y_min = min(self._lsl - margin, min(data) - margin * 0.5)
                y_max = max(self._usl + margin, max(data) + margin * 0.5)
                ax.set_ylim(y_min, y_max)
            else:
                margin = (self._usl - self._lsl) * 0.3
                ax.set_ylim(self._lsl - margin, self._usl + margin)

        if self._x_data:
            # Padding del 5% ai lati
            x_range = self._x_data[-1] - self._x_data[0]
            if x_range == 0: x_range = 1
            self.ax_max.set_xlim(self._x_data[0] - x_range*0.05, self._x_data[-1] + x_range*0.05)
        else:
            self.ax_max.set_xlim(0, 5)

        self.fig.tight_layout()
        self.canvas.draw()
