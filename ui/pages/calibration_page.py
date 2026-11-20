"""
calibration_page.py
-------------------
Calibrazione della cella di carico con un peso noto.
Si apre dalle impostazioni, quindi è già protetta da password.

Procedura:
    1. TARA A VUOTO         — cella libera, nessun peso
    2. CALIBRA CON IL PESO  — peso noto appoggiato, massa inserita in grammi
    3. Verifica             — la forza deve leggere il valore atteso e tornare
                              a 0 togliendo il peso

La scheda calcola il fattore; MainWindow lo salva in config.json.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFrame
)
from PyQt5.QtCore import pyqtSignal, Qt

from ui.widgets.force_widget import ForceWidget
from ui.widgets.virtual_keyboard import VirtualKeyboard
from config import Config
from core.i18n import _

# Accelerazione di gravità standard: massa [g] × _G = forza [mN]
_G = 9.80665

_COLOR_INFO  = "#94a3b8"
_COLOR_BUSY  = "#ffab00"
_COLOR_OK    = "#00e676"
_COLOR_ERROR = "#ff3d57"


class CalibrationPage(QWidget):
    """
    Pagina di calibrazione della cella di carico.

    Signals:
        tare_requested:               l'utente ha premuto TARA A VUOTO
        calibration_requested(float): l'utente ha premuto CALIBRA (forza di riferimento in mN)
        back_requested:               l'utente ha premuto BACK
    """

    tare_requested        = pyqtSignal()
    calibration_requested = pyqtSignal(float)
    back_requested        = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pending: str | None = None        # "tare" / "calibrate" in corso
        self._tared = False                     # tara a vuoto fatta da questa pagina
        self._requested_mass_g: float = 0.0
        self._build_ui()

    # ─── Build ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 10, 30, 14)
        root.setSpacing(10)

        # ── Header ──────────────────────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(16)
        title = QLabel(_("CALIBRAZIONE CELLA DI CARICO"))
        title.setObjectName("titleLabel")
        title.setStyleSheet("font-size: 20px;")
        back_btn = QPushButton("← " + _("INDIETRO"))
        back_btn.setObjectName("backBtn")
        back_btn.clicked.connect(self.back_requested)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(back_btn)

        # ── Forza in tempo reale + procedura ────────────────────────────────
        top = QHBoxLayout()
        top.setSpacing(12)

        self._force_widget = ForceWidget()

        steps_frame = QFrame()
        steps_frame.setObjectName("card")
        steps = QVBoxLayout(steps_frame)
        steps.setContentsMargins(20, 12, 20, 12)
        steps.setSpacing(4)
        for text in (
            _("1 · Togliere tutto dalla cella e premere TARA A VUOTO"),
            _("2 · Appoggiare il peso, inserire la massa e premere CALIBRA"),
            _("3 · Verificare il valore atteso, poi togliere il peso: deve tornare a 0"),
        ):
            lbl = QLabel(text)
            lbl.setObjectName("statKeyLabel")
            lbl.setWordWrap(True)
            steps.addWidget(lbl)

        self._factor_lbl = QLabel()
        self._factor_lbl.setObjectName("statKeyLabel")
        self._factor_lbl.setWordWrap(True)
        steps.addWidget(self._factor_lbl)

        top.addWidget(self._force_widget, 1)
        top.addWidget(steps_frame, 2)

        # ── Massa di riferimento ────────────────────────────────────────────
        mass_frame = QFrame()
        mass_frame.setObjectName("card")
        mass = QHBoxLayout(mass_frame)
        mass.setContentsMargins(24, 10, 24, 10)
        mass.setSpacing(12)

        mass_lbl = QLabel(_("MASSA DI RIFERIMENTO"))
        mass_lbl.setObjectName("statKeyLabel")

        # Unico campo della pagina: sempre attivo per la tastiera virtuale
        self._mass_field = QLineEdit()
        self._mass_field.setStyleSheet("border: 2px solid #00c8ff;")
        self._mass_field.textChanged.connect(self._update_expected)

        unit_lbl = QLabel("g")
        unit_lbl.setObjectName("statKeyLabel")
        unit_lbl.setFixedWidth(40)

        self._expected_lbl = QLabel()
        self._expected_lbl.setObjectName("statKeyLabel")

        mass.addWidget(mass_lbl)
        mass.addWidget(self._mass_field, 1)
        mass.addWidget(unit_lbl)
        mass.addWidget(self._expected_lbl, 1)

        # ── Pulsanti ────────────────────────────────────────────────────────
        buttons = QHBoxLayout()
        buttons.setSpacing(12)

        self._tare_btn = QPushButton("1 · " + _("TARA A VUOTO"))
        self._tare_btn.setObjectName("primaryBtn")
        self._tare_btn.setMinimumHeight(56)
        self._tare_btn.clicked.connect(self._on_tare)

        self._calib_btn = QPushButton("2 · " + _("CALIBRA CON IL PESO"))
        self._calib_btn.setObjectName("successBtn")
        self._calib_btn.setMinimumHeight(56)
        self._calib_btn.clicked.connect(self._on_calibrate)

        buttons.addWidget(self._tare_btn)
        buttons.addWidget(self._calib_btn)

        # ── Esito ───────────────────────────────────────────────────────────
        self._status_lbl = QLabel()
        self._status_lbl.setAlignment(Qt.AlignCenter)
        self._status_lbl.setWordWrap(True)

        # ── Tastiera virtuale ───────────────────────────────────────────────
        self._keyboard = VirtualKeyboard(key_max_height=44)
        self._keyboard.key_pressed.connect(self._on_key)

        # ── Assembly ────────────────────────────────────────────────────────
        root.addLayout(header)
        root.addLayout(top)
        root.addWidget(mass_frame)
        root.addLayout(buttons)
        root.addWidget(self._status_lbl)
        root.addWidget(self._keyboard, 1)

        self.load_current_values()

    # ─── Slots ──────────────────────────────────────────────────────────────

    def _on_key(self, char: str):
        # Solo cifre e punto decimale
        if char == "BACK":
            self._mass_field.setText(self._mass_field.text()[:-1])
        elif char.isdigit() or char in (".", ","):
            c = "." if char == "," else char
            self._mass_field.setText(self._mass_field.text() + c)

    def _on_tare(self):
        self._pending = "tare"
        self._tared = False
        self._set_status(_("Tara in corso — non toccare la cella..."), _COLOR_BUSY)
        self._update_buttons()
        self.tare_requested.emit()

    def _on_calibrate(self):
        mass_g = self._mass_g()
        if mass_g is None:
            self._set_status(_("Inserire una massa valida in grammi."), _COLOR_ERROR)
            return

        self._pending = "calibrate"
        self._requested_mass_g = mass_g
        self._set_status(_("Calibrazione in corso — non toccare il peso..."), _COLOR_BUSY)
        self._update_buttons()
        self.calibration_requested.emit(mass_g * _G)

    def _update_expected(self):
        mass_g = self._mass_g()
        text = f"= {mass_g * _G:.1f} mN" if mass_g is not None else "—"
        self._expected_lbl.setText(text)

    # ─── Helpers ────────────────────────────────────────────────────────────

    def _mass_g(self) -> float | None:
        try:
            mass_g = float(self._mass_field.text())
        except ValueError:
            return None
        return mass_g if mass_g > 0 else None

    def _set_status(self, text: str, color: str):
        self._status_lbl.setText(text)
        self._status_lbl.setStyleSheet(
            f"color: {color}; font-size: 15px; font-weight: 700;"
        )

    def _update_buttons(self):
        idle = self._pending is None
        self._tare_btn.setEnabled(idle)
        # La calibrazione usa l'offset della tara: prima va fatta quella a vuoto
        self._calib_btn.setEnabled(idle and self._tared)

    def _refresh_factor(self):
        factor = Config.scale_factor
        if factor is None:
            self._factor_lbl.setText(
                _("Cella non calibrata: la forza è in conteggi ADC, non in mN")
            )
            self._factor_lbl.setStyleSheet(f"color: {_COLOR_ERROR};")
            return

        date = (Config.calibration_date or "—")[:16].replace("T", " ")
        self._factor_lbl.setText(
            f"{_('Fattore')}: {factor:.6g} mN/{_('conteggio')}  ·  "
            f"{_('Ultima calibrazione')}: {date}"
        )
        self._factor_lbl.setStyleSheet("")

    # ─── Public ─────────────────────────────────────────────────────────────

    def load_current_values(self):
        """Prepara la pagina all'apertura: massa proposta e fattore attuale."""
        self._mass_field.setText(f"{Config.calibration_mass_g:g}")
        self._refresh_factor()
        if self._pending is None:
            self._tared = False
            self._set_status(_("Premere TARA A VUOTO con la cella libera."), _COLOR_INFO)
        self._update_buttons()

    def set_force(self, force: float):
        self._force_widget.set_value(force)

    def on_tare_finished(self, ok: bool):
        """Esito della tara: riguarda la pagina solo se l'ha chiesta lei."""
        if self._pending != "tare":
            return
        self._pending = None
        self._tared = ok
        if ok:
            self._set_status(
                _("Tara completata. Appoggiare il peso e premere CALIBRA."), _COLOR_OK
            )
        else:
            self._set_status(
                _("Tara non riuscita: controllare la cella di carico."), _COLOR_ERROR
            )
        self._update_buttons()

    def on_calibration_finished(self, ok: bool):
        """Esito della calibrazione, dopo che MainWindow ha salvato il fattore."""
        if self._pending != "calibrate":
            return
        self._pending = None
        if ok:
            expected = self._requested_mass_g * _G
            self._set_status(
                f"{_('Calibrazione salvata. Valore atteso')}: {expected:.1f} mN — "
                f"{_('togliendo il peso deve tornare a 0.')}",
                _COLOR_OK,
            )
            self._refresh_factor()
        else:
            self._set_status(
                _("Calibrazione non riuscita: peso non appoggiato o cella non pronta."),
                _COLOR_ERROR,
            )
        self._update_buttons()

    @property
    def requested_mass_g(self) -> float:
        """Massa usata nell'ultima calibrazione richiesta [g]."""
        return self._requested_mass_g
