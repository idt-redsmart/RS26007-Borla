"""
settings_page.py
-----------------
Pagina impostazioni: accessibile solo dopo verifica password.
Campi: Lower Limit / Upper Limit / Time / Trigger Force.
Tastiera virtuale numerica integrata.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QFrame, QMessageBox, QComboBox
)
from PyQt5.QtCore import pyqtSignal

from ui.widgets.virtual_keyboard import VirtualKeyboard
from config import Config
from core.i18n import _


class SettingsPage(QWidget):
    """
    Pagina impostazioni.

    Signals:
        settings_saved(dict): i nuovi valori salvati
        back_requested:       l'utente ha premuto BACK
    """

    settings_saved  = pyqtSignal(dict)
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
        title = QLabel(_("IMPOSTAZIONI DI SISTEMA"))
        title.setObjectName("titleLabel")
        back_btn = QPushButton("← " + _("INDIETRO"))
        back_btn.setObjectName("backBtn")
        back_btn.clicked.connect(self.back_requested)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(back_btn)

        subtitle = QLabel(_("Modifica i parametri di collaudo  ·  Accesso protetto"))
        subtitle.setObjectName("subtitleLabel")

        # ── Form ─────────────────────────────────────────────────────────────
        form_frame = QFrame()
        form_frame.setObjectName("card")
        form = QGridLayout(form_frame)
        form.setContentsMargins(30, 24, 30, 24)
        form.setSpacing(16)
        form.setColumnStretch(1, 1)
        form.setColumnStretch(3, 1)

        self._fields: dict[str, QLineEdit] = {}
        field_defs = [
            ("lower_limit",    _("LIMITE INFERIORE"),    "mN", 0, 0),
            ("upper_limit",    _("LIMITE SUPERIORE"),    "mN", 0, 2),
            ("test_time",      _("TEMPO"),           "s",  1, 0),
            ("trigger_force",  _("FORZA TRIGGER"),  "mN", 1, 2),
            ("password",       _("PASSWORD"),       "",   2, 2),
        ]

        for key, label, unit, row, col in field_defs:
            lbl = QLabel(label)
            lbl.setObjectName("statKeyLabel")

            field = QLineEdit()
            
            # Consente sia tastiera normale che virtuale
            def focus_handler(e, f=field, orig=field.focusInEvent):
                self._activate_field(f)
                orig(e)
            field.focusInEvent = focus_handler

            unit_lbl = QLabel(unit)
            unit_lbl.setObjectName("statKeyLabel")
            unit_lbl.setFixedWidth(40)

            row_lay = QHBoxLayout()
            row_lay.setSpacing(8)
            row_lay.addWidget(field)
            row_lay.addWidget(unit_lbl)

            form.addWidget(lbl, row, col)
            form.addLayout(row_lay, row, col + 1)
            self._fields[key] = field

        # Lingua
        lbl_lang = QLabel(_("Lingua di Sistema"))
        lbl_lang.setObjectName("statKeyLabel")
        self._lang_cb = QComboBox()
        self._lang_cb.addItems(["Italiano", "English"])
        self._lang_cb.setStyleSheet("padding: 8px; font-size: 16px; border: 1px solid #1e293b; background: #0f172a; color: white;")
        form.addWidget(lbl_lang, 2, 0)
        form.addWidget(self._lang_cb, 2, 1)

        self.load_current_values()

        # ── Tastiera virtuale ────────────────────────────────────────────────
        self._keyboard = VirtualKeyboard()
        self._keyboard.key_pressed.connect(self._on_key)

        # ── CONFIRM ──────────────────────────────────────────────────────────
        confirm_btn = QPushButton("✓  " + _("SALVA IMPOSTAZIONI"))
        confirm_btn.setObjectName("successBtn")
        confirm_btn.setMinimumHeight(56)
        confirm_btn.clicked.connect(self._on_confirm)

        # ── Assembly ─────────────────────────────────────────────────────────
        root.addLayout(header)
        root.addWidget(subtitle)
        root.addWidget(form_frame)
        root.addWidget(self._keyboard)
        root.addWidget(confirm_btn)

        self._activate_field(self._fields["lower_limit"])

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
            self._active_field.setText(self._active_field.text()[:-1])
        elif char in ("ENTER", "SPACE", "CAPS"):
            pass
        elif char.isdigit() or char in (".", ","):
            c = "." if char == "," else char
            self._active_field.setText(self._active_field.text() + c)

    def _on_confirm(self):
        try:
            values = {
                "lower_limit":   float(self._fields["lower_limit"].text()),
                "upper_limit":   float(self._fields["upper_limit"].text()),
                "test_time":     float(self._fields["test_time"].text()),
                "trigger_force": float(self._fields["trigger_force"].text()),
                "password":      self._fields["password"].text(),
            }
        except ValueError:
            QMessageBox.warning(self, _("Errore"), _("Valori non validi. Inserire solo numeri."))
            return

        lang_idx = self._lang_cb.currentIndex()
        new_lang = "it" if lang_idx == 0 else "en"
        
        if new_lang != Config.language:
            values["language"] = new_lang
            QMessageBox.information(self, _("Salvataggio"), _("Per applicare il cambio di lingua, riavviare l'applicazione."))

        self.settings_saved.emit(values)

    # ─── Public ─────────────────────────────────────────────────────────────

    def load_current_values(self, current_password: str = ""):
        """Popola i campi con i valori correnti da Config e la password dal DB."""
        self._fields["lower_limit"].setText(str(Config.lower_limit))
        self._fields["upper_limit"].setText(str(Config.upper_limit))
        self._fields["test_time"].setText(str(Config.test_time))
        self._fields["trigger_force"].setText(str(Config.trigger_force))
        self._fields["password"].setText(current_password)
        self._lang_cb.setCurrentIndex(1 if Config.language == "en" else 0)
