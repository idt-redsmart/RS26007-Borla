"""
virtual_keyboard.py
--------------------
Tastiera virtuale QWERTY da usare su schermo touch.
Emette il segnale `key_pressed(str)` per ogni tasto premuto.
Caratteri speciali: 'BACK', 'ENTER', 'SPACE', 'CAPS'.
Riga simboli: . , - _ @ / ! ? " ' ( ) # % & *
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy
)
from PyQt5.QtCore import pyqtSignal, Qt


_ROWS_LOWER = [
    ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
    ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
    ["A", "S", "D", "F", "G", "H", "J", "K", "L"],
    ["Z", "X", "C", "V", "B", "N", "M"],
]

# Simboli speciali più usati (non soggetti a CAPS)
_ROW_SYMBOLS = [
    ".", ",", "-", "_", "@", "/", "!", "?",
    '"', "'", "(", ")", "#", "%", "&", "*",
]


class VirtualKeyboard(QWidget):
    """
    Tastiera virtuale QWERTY.

    Signals:
        key_pressed(str): emesso per ogni tasto, inclusi BACK/ENTER/SPACE/CAPS
    """

    key_pressed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._caps = True
        self._build_ui()

    # ─── Build ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(10, 10, 10, 10)
        root.setAlignment(Qt.AlignCenter)

        self._key_buttons = []

        # ── Riga 0: numeri + BACK ──────────────────────────────────────────
        row0 = QHBoxLayout()
        row0.setSpacing(8)
        for char in _ROWS_LOWER[0]:
            row0.addWidget(self._make_key(char))
        
        back = self._make_special("⌫ BACK", "BACK", stretch=2)
        row0.addWidget(back)
        root.addLayout(row0)

        # ── Riga simboli: . , - _ @ / ! ? " ' ( ) # % & * ────────────────
        rowS = QHBoxLayout()
        rowS.setSpacing(8)
        rowS.setAlignment(Qt.AlignCenter)
        for sym in _ROW_SYMBOLS:
            rowS.addWidget(self._make_sym(sym))
        root.addLayout(rowS)

        # ── Riga 1: Q…P ─────────────────────────────────────────────────────
        row1 = QHBoxLayout()
        row1.setSpacing(8)
        row1.setAlignment(Qt.AlignCenter)
        for char in _ROWS_LOWER[1]:
            row1.addWidget(self._make_key(char))
        root.addLayout(row1)

        # ── Riga 2: A…L + ENTER ─────────────────────────────────────────────
        row2 = QHBoxLayout()
        row2.setSpacing(8)
        row2.setAlignment(Qt.AlignCenter)
        for char in _ROWS_LOWER[2]:
            row2.addWidget(self._make_key(char))
            
        enter = self._make_special("ENTER ↵", "ENTER", stretch=2)
        row2.addWidget(enter)
        root.addLayout(row2)

        # ── Riga 3: CAPS + Z…M + SPACE ──────────────────────────────────────
        row3 = QHBoxLayout()
        row3.setSpacing(8)
        row3.setAlignment(Qt.AlignCenter)
        
        caps = self._make_special("⇧ CAPS", "CAPS", stretch=2)
        row3.addWidget(caps)

        for char in _ROWS_LOWER[3]:
            row3.addWidget(self._make_key(char))

        space = self._make_special("SPACE", "SPACE", stretch=4)
        row3.addWidget(space)
        
        root.addLayout(row3)

    # ─── Helpers ────────────────────────────────────────────────────────────

    def _make_key(self, char: str) -> QPushButton:
        btn = QPushButton(char)
        btn.setObjectName("keyBtn")
        btn.setFixedSize(52, 64)
        btn.clicked.connect(lambda _, c=char: self._on_key(c))
        self._key_buttons.append((btn, char))
        return btn

    def _make_sym(self, char: str) -> QPushButton:
        """Tasto simbolo: dimensione fissa, nessuna logica caps."""
        btn = QPushButton(char)
        btn.setObjectName("keySymBtn")
        btn.setFixedSize(52, 64)
        btn.clicked.connect(lambda _, c=char: self.key_pressed.emit(c))
        return btn

    def _make_special(self, label: str, action: str, stretch: int = 1) -> QPushButton:
        btn = QPushButton(label)
        btn.setObjectName("keySpecialBtn")
        btn.setFixedHeight(64)
        min_w = 80 + (stretch - 1) * 52
        btn.setMinimumWidth(min_w)
        btn.clicked.connect(lambda _, a=action: self._on_key(a))
        return btn

    # ─── Slots ──────────────────────────────────────────────────────────────

    def _on_key(self, char: str):
        if char == "CAPS":
            self._caps = not self._caps
            self._update_case()
        else:
            # Emetti nel case corretto (le lettere rispettano _caps)
            actual = char.upper() if self._caps else char.lower()
            self.key_pressed.emit(actual)

    def _update_case(self):
        for btn, base in self._key_buttons:
            btn.setText(base if self._caps else base.lower())
