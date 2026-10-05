"""
virtual_keyboard.py
--------------------
Tastiera virtuale QWERTY da usare su schermo touch.
Emette il segnale `key_pressed(str)` per ogni tasto premuto.
Caratteri speciali: 'BACK', 'ENTER', 'SPACE', 'CAPS'.
Blocco simboli: . , - _ @ / ! ? " ' ( ) # % & *
"""

from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QSizePolicy
from PyQt5.QtCore import pyqtSignal, Qt


_ROWS_LOWER = [
    ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
    ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
    ["A", "S", "D", "F", "G", "H", "J", "K", "L"],
    ["Z", "X", "C", "V", "B", "N", "M"],
]

# Simboli speciali più usati (non soggetti a CAPS), blocco 4x4 a destra
_ROW_SYMBOLS = [
    ".", ",", "-", "_", "@", "/", "!", "?",
    '"', "'", "(", ")", "#", "%", "&", "*",
]

# Griglia a mezze colonne: ogni tasto standard occupa 2 colonne,
# così le righe possono essere sfalsate di mezzo tasto.
_LETTER_COLS = 24          # area lettere/numeri: colonne 0..23
_GAP_COL     = 24          # colonna vuota di separazione
_SYM_COL0    = 25          # blocco simboli: colonne 25..32
_TOTAL_COLS  = _SYM_COL0 + 8

_KEY_MIN_H = 40
_KEY_MAX_H = 52


class VirtualKeyboard(QWidget):
    """
    Tastiera virtuale QWERTY.

    Signals:
        key_pressed(str): emesso per ogni tasto, inclusi BACK/ENTER/SPACE/CAPS
    """

    key_pressed = pyqtSignal(str)

    def __init__(self, parent=None, key_max_height: int = _KEY_MAX_H):
        super().__init__(parent)
        self._key_max_h = key_max_height
        self._caps = False          # avvio in minuscolo, CAPS attiva le maiuscole
        self._build_ui()
        self._update_case()

    # ─── Build ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        grid = QGridLayout(self)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)
        grid.setContentsMargins(10, 10, 10, 10)

        for col in range(_TOTAL_COLS):
            grid.setColumnStretch(col, 1)
            grid.setColumnMinimumWidth(col, 20)

        self._key_buttons = []

        # ── Riga 0: numeri + BACK ──────────────────────────────────────────
        for i, char in enumerate(_ROWS_LOWER[0]):
            grid.addWidget(self._make_key(char), 0, i * 2, 1, 2)
        grid.addWidget(self._make_special("⌫ BACK", "BACK"), 0, 20, 1, 4)

        # ── Riga 1: Q…P + ENTER (alto due righe) ───────────────────────────
        for i, char in enumerate(_ROWS_LOWER[1]):
            grid.addWidget(self._make_key(char), 1, i * 2, 1, 2)
        grid.addWidget(self._make_special("ENTER ↵", "ENTER"), 1, 20, 2, 4)

        # ── Riga 2: A…L (sfalsata di mezzo tasto) ──────────────────────────
        for i, char in enumerate(_ROWS_LOWER[2]):
            grid.addWidget(self._make_key(char), 2, 1 + i * 2, 1, 2)

        # ── Riga 3: CAPS + Z…M + SPACE ──────────────────────────────────────
        grid.addWidget(self._make_special("⇧ CAPS", "CAPS"), 3, 0, 1, 3)
        for i, char in enumerate(_ROWS_LOWER[3]):
            grid.addWidget(self._make_key(char), 3, 3 + i * 2, 1, 2)
        grid.addWidget(self._make_special("SPACE", "SPACE"), 3, 17, 1, 7)

        # ── Blocco simboli 4x4 ──────────────────────────────────────────────
        for idx, sym in enumerate(_ROW_SYMBOLS):
            r, c = divmod(idx, 4)
            grid.addWidget(self._make_sym(sym), r, _SYM_COL0 + c * 2, 1, 2)

    # ─── Helpers ────────────────────────────────────────────────────────────

    def _setup_btn(self, btn: QPushButton) -> None:
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        btn.setMinimumHeight(_KEY_MIN_H)
        btn.setMaximumHeight(self._key_max_h * 2 + 6)
        btn.setFocusPolicy(Qt.NoFocus)   # non ruba il focus al campo attivo

    def _make_key(self, char: str) -> QPushButton:
        btn = QPushButton(char)
        btn.setObjectName("keyBtn")
        self._setup_btn(btn)
        btn.setMaximumHeight(self._key_max_h)
        btn.clicked.connect(lambda _, c=char: self._on_key(c))
        self._key_buttons.append((btn, char))
        return btn

    def _make_sym(self, char: str) -> QPushButton:
        """Tasto simbolo: nessuna logica caps."""
        # '&' va raddoppiato, altrimenti Qt lo interpreta come mnemonico
        btn = QPushButton(char.replace("&", "&&"))
        btn.setObjectName("keySymBtn")
        self._setup_btn(btn)
        btn.setMaximumHeight(self._key_max_h)
        btn.clicked.connect(lambda _, c=char: self.key_pressed.emit(c))
        return btn

    def _make_special(self, label: str, action: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setObjectName("keySpecialBtn")
        self._setup_btn(btn)
        if action != "ENTER":
            btn.setMaximumHeight(self._key_max_h)
        btn.clicked.connect(lambda _, a=action: self._on_key(a))
        return btn

    # ─── Slots ──────────────────────────────────────────────────────────────

    def _on_key(self, char: str):
        if char == "CAPS":
            self._caps = not self._caps
            self._update_case()
        elif char in ("BACK", "ENTER", "SPACE"):
            # Tasti speciali: emessi invariati, non soggetti a CAPS
            self.key_pressed.emit(char)
        else:
            # Le lettere rispettano lo stato di CAPS
            actual = char.upper() if self._caps else char.lower()
            self.key_pressed.emit(actual)

    def _update_case(self):
        for btn, base in self._key_buttons:
            btn.setText(base if self._caps else base.lower())
