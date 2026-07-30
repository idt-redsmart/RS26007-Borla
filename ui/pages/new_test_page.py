"""
new_test_page.py
----------------
Pagina di inserimento dati pre-test:
    Operatore / Stampo / Lotto Produzione / Lotto Materia Prima
Tastiera virtuale integrata. Emette segnali verso il controller.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QFrame
)
from PyQt5.QtCore import pyqtSignal

from ui.widgets.virtual_keyboard import VirtualKeyboard
from core.i18n import _


class NewTestPage(QWidget):
    """
    Schermata inserimento dati iniziali.

    Signals:
        start_confirmed(dict): emesso con i dati inseriti dall'operatore
        back_requested:        l'utente ha premuto BACK
    """

    start_confirmed = pyqtSignal(dict)
    back_requested  = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._active_field: QLineEdit | None = None
        self._build_ui()

    # ─── Build ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 30, 40, 20)
        root.setSpacing(20)

        # ── Header ──────────────────────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel(_("IMPOSTA COLLAUDO"))
        title.setObjectName("titleLabel")
        back_btn = QPushButton("← " + _("INDIETRO"))
        back_btn.setObjectName("backBtn")
        back_btn.clicked.connect(self.back_requested)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(back_btn)

        subtitle = QLabel(_("Inserire i dati prima di avviare il collaudo"))
        subtitle.setObjectName("subtitleLabel")

        # ── Campi di input ───────────────────────────────────────────────────
        form_frame = QFrame()
        form_frame.setObjectName("card")
        form = QGridLayout(form_frame)
        form.setContentsMargins(30, 24, 30, 24)
        form.setSpacing(16)
        form.setColumnStretch(1, 1)

        self._fields: dict[str, QLineEdit] = {}
        field_defs = [
            ("OPERATOR",       _("OPERATORE"), _("Codice Operatore")),
            ("MOULD",          _("STAMPO"), _("Codice Stampo")),
            ("PRODUCTION LOT", _("LOTTO PRODUZIONE"), _("Lotto Produzione")),
            ("RAW MATERIAL",   _("MATERIA PRIMA"), _("Lotto Materia Prima")),
        ]

        for row, (key, label, placeholder) in enumerate(field_defs):
            lbl = QLabel(label)
            lbl.setObjectName("statKeyLabel")
            lbl.setFixedWidth(160)

            field = QLineEdit()
            field.setPlaceholderText(placeholder)
            field.setObjectName("inputField")
            
            # Consente sia tastiera normale che virtuale
            def focus_handler(e, f=field, orig=field.focusInEvent):
                self._activate_field(f)
                orig(e)
            field.focusInEvent = focus_handler

            self._fields[key] = field
            form.addWidget(lbl,   row, 0)
            form.addWidget(field, row, 1)

        # ── Tastiera virtuale ────────────────────────────────────────────────
        self._keyboard = VirtualKeyboard()
        self._keyboard.key_pressed.connect(self._on_key)

        # ── Pulsante START TEST ──────────────────────────────────────────────
        start_btn = QPushButton("▶  " + _("AVVIA COLLAUDO"))
        start_btn.setObjectName("primaryBtn")
        start_btn.setMinimumHeight(56)
        start_btn.clicked.connect(self._on_start)

        # ── Assembly ─────────────────────────────────────────────────────────
        root.addLayout(header)
        root.addWidget(subtitle)
        root.addWidget(form_frame)
        root.addWidget(self._keyboard)
        root.addWidget(start_btn)

        # Attiva il primo campo di default
        self._activate_field(self._fields["OPERATOR"])

    # ─── Slots ──────────────────────────────────────────────────────────────

    def _activate_field(self, field: QLineEdit):
        if self._active_field:
            self._active_field.setStyleSheet("")
        self._active_field = field
        field.setStyleSheet("border: 2px solid #00c8ff;")

    def _on_key(self, char: str):
        if self._active_field is None:
            return
        if char == "BACK":
            txt = self._active_field.text()
            self._active_field.setText(txt[:-1])
        elif char == "ENTER":
            # Passa al campo successivo
            fields = list(self._fields.values())
            idx = fields.index(self._active_field)
            if idx < len(fields) - 1:
                self._activate_field(fields[idx + 1])
        elif char == "SPACE":
            self._active_field.setText(self._active_field.text() + " ")
        elif char == "CAPS":
            pass  # gestito dalla tastiera
        else:
            self._active_field.setText(self._active_field.text() + char)

    def _on_start(self):
        data = {key: field.text().strip() for key, field in self._fields.items()}
        self.start_confirmed.emit(data)

    # ─── Public ─────────────────────────────────────────────────────────────

    def clear(self):
        """Svuota tutti i campi."""
        for field in self._fields.values():
            field.clear()
        self._activate_field(self._fields["OPERATOR"])
