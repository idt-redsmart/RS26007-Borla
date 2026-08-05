"""
history_page.py
---------------
Pagina storico collaudi: tabella con ID, DATA, STAMPO, MIN, MEAN, MAX, VIEW.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView
)
from PyQt5.QtCore import pyqtSignal, Qt

from core.i18n import _


class HistoryPage(QWidget):
    """
    Tabella storico collaudi.

    Signals:
        view_report_requested(int): ID del collaudo di cui visualizzare il report
        back_requested:             l'utente ha premuto BACK
    """

    view_report_requested = pyqtSignal(int)
    delete_report_requested = pyqtSignal(int)
    back_requested        = pyqtSignal()

    _COLUMNS = ["ID", _("DATA"), _("STAMPO"), "MIN mN", "MEAN mN", "MAX mN", _("AZIONI")]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # ─── Build ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 30, 40, 30)
        root.setSpacing(20)

        # ── Header ──────────────────────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel(_("STORICO COLLAUDI"))
        title.setObjectName("titleLabel")
        back_btn = QPushButton("← " + _("INDIETRO"))
        back_btn.setObjectName("backBtn")
        back_btn.clicked.connect(self.back_requested)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(back_btn)

        subtitle = QLabel(_("Collaudi precedenti — clicca VIEW per aprire il report PDF"))
        subtitle.setObjectName("subtitleLabel")

        # ── Tabella ─────────────────────────────────────────────────────────
        self._table = QTableWidget()
        self._table.setColumnCount(len(self._COLUMNS))
        self._table.setHorizontalHeaderLabels(self._COLUMNS)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(
            "QTableWidget { alternate-background-color: #131c2e; }"
        )

        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Stretch)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)   # ID
        hdr.setSectionResizeMode(6, QHeaderView.ResizeToContents)   # VIEW e DELETE

        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(70)
        self._table.setShowGrid(False)

        # ── Assembly ─────────────────────────────────────────────────────────
        root.addLayout(header)
        root.addWidget(subtitle)
        root.addWidget(self._table)

    # ─── Public API ─────────────────────────────────────────────────────────

    def load_records(self, records: list[dict]):
        """
        Popola la tabella con i record forniti.

        Ogni record è un dict con le chiavi:
            id, date, mould, min, mean, max
        """
        self._table.setRowCount(0)
        for rec in records:
            row = self._table.rowCount()
            self._table.insertRow(row)

            def make_item(text, align=Qt.AlignCenter):
                item = QTableWidgetItem(str(text))
                item.setTextAlignment(align)
                return item

            self._table.setItem(row, 0, make_item(rec.get("id", "—")))
            self._table.setItem(row, 1, make_item(rec.get("date", "—")))
            self._table.setItem(row, 2, make_item(rec.get("mould", "—")))
            self._table.setItem(row, 3, make_item(f"{rec.get('min', 0):.0f}"))
            self._table.setItem(row, 4, make_item(f"{rec.get('mean', 0):.1f}"))
            self._table.setItem(row, 5, make_item(f"{rec.get('max', 0):.0f}"))

            # Pulsante VIEW
            view_btn = QPushButton("📄 " + _("VIEW"))
            view_btn.setCursor(Qt.PointingHandCursor)
            view_btn.setMinimumSize(95, 36)
            view_btn.setStyleSheet(
                "QPushButton { color: #00c8ff; border: 1px solid #00c8ff; "
                "border-radius: 6px; padding: 6px 12px; font-size: 14px; font-weight: 700; background: transparent; }"
                "QPushButton:hover { background: #00c8ff; color: #0b0f1a; }"
            )
            
            # Pulsante DELETE
            del_btn = QPushButton("🗑 " + _("DEL"))
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setMinimumSize(95, 36)
            del_btn.setStyleSheet(
                "QPushButton { color: #ff3d57; border: 1px solid #ff3d57; "
                "border-radius: 6px; padding: 6px 12px; font-size: 14px; font-weight: 700; background: transparent; }"
                "QPushButton:hover { background: #ff3d57; color: #0b0f1a; }"
            )
            
            # Container per dare margini ai pulsanti all'interno della cella
            container = QWidget()
            container.setStyleSheet("background: transparent;")
            container.setMinimumWidth(250)
            lay = QHBoxLayout(container)
            lay.setContentsMargins(8, 4, 8, 4)
            lay.setSpacing(12)
            lay.addWidget(view_btn)
            lay.addWidget(del_btn)
            lay.addStretch()  # Spinge i bottoni a sinistra

            rec_id = rec.get("id", -1)
            view_btn.clicked.connect(lambda _, rid=rec_id: self.view_report_requested.emit(rid))
            del_btn.clicked.connect(lambda _, rid=rec_id: self.delete_report_requested.emit(rid))
            self._table.setCellWidget(row, 6, container)
            
            # Forza l'altezza della riga in modo che contenga sicuramente i bottoni
            self._table.setRowHeight(row, 65)

        # Rimosso resizeRowsToContents per evitare che schiacci le righe ignorando i CellWidget
        pass

    def clear(self):
        self._table.setRowCount(0)
