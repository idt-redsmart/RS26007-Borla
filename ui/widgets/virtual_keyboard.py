"""
virtual_keyboard.py
--------------------
Tastiera virtuale QWERTY da usare su schermo touch.
Emette il segnale `key_pressed(str)` per ogni tasto premuto.
Caratteri speciali: 'BACK', 'ENTER', 'SPACE', 'CAPS'.
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
        root.setSpacing(6)
        root.setContentsMargins(8, 8, 8, 8)
        root.setAlignment(Qt.AlignCenter)

        self._key_buttons = []

        # ── Riga 0: numeri + BACK ──────────────────────────────────────────
        row0 = QHBoxLayout()
        row0.setSpacing(6)
        for char in _ROWS_LOWER[0]:
            row0.addWidget(self._make_key(char))
        
        back = self._make_special("⌫ BACK", "BACK", min_w=80)
        row0.addWidget(back)
        root.addLayout(row0)

        # ── Riga 1: Q…P ─────────────────────────────────────────────────────
        row1 = QHBoxLayout()
        row1.setSpacing(6)
        row1.setAlignment(Qt.AlignCenter)
        for char in _ROWS_LOWER[1]:
            row1.addWidget(self._make_key(char))
        root.addLayout(row1)

        # ── Riga 2: A…L + ENTER ─────────────────────────────────────────────
        row2 = QHBoxLayout()
        row2.setSpacing(6)
        row2.setAlignment(Qt.AlignCenter)
        for char in _ROWS_LOWER[2]:
            row2.addWidget(self._make_key(char))
            
        enter = self._make_special("ENTER ↵", "ENTER", min_w=80)
        row2.addWidget(enter)
        root.addLayout(row2)

        # ── Riga 3: CAPS + Z…M + SPACE ──────────────────────────────────────
        row3 = QHBoxLayout()
        row3.setSpacing(6)
        row3.setAlignment(Qt.AlignCenter)
        
        caps = self._make_special("⇧ CAPS", "CAPS", min_w=80)
        row3.addWidget(caps)

        for char in _ROWS_LOWER[3]:
            row3.addWidget(self._make_key(char))

        space = self._make_special("SPACE", "SPACE", min_w=200)
        row3.addWidget(space)
        
        root.addLayout(row3)

    # ─── Helpers ────────────────────────────────────────────────────────────

    def _make_key(self, char: str) -> QPushButton:
        btn = QPushButton(char)
        btn.setObjectName("keyBtn")
        btn.setFixedSize(44, 44)
        btn.clicked.connect(lambda _, c=char: self._on_key(c))
        self._key_buttons.append((btn, char))
        return btn

    def _make_special(self, label: str, action: str, min_w: int = 60) -> QPushButton:
        btn = QPushButton(label)
        btn.setObjectName("keySpecialBtn")
        btn.setFixedHeight(44)
        btn.setMinimumWidth(min_w)
        btn.clicked.connect(lambda _, a=action: self._on_key(a))
        return btn

    # ─── Slots ──────────────────────────────────────────────────────────────

    def _on_key(self, char: str):
        if char == "CAPS":
            self._caps = not self._caps
            self._update_case()
        else:
            self.key_pressed.emit(char)

    def _update_case(self):
        for btn, base in self._key_buttons:
            btn.setText(base if self._caps else base.lower())
