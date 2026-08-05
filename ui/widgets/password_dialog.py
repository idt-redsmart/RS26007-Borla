"""
password_dialog.py
-------------------
Dialogo modale per l'inserimento della password su schermo touch.
Integra VirtualKeyboard per evitare l'uso della tastiera fisica.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame
)
from PyQt5.QtCore import Qt

from ui.widgets.virtual_keyboard import VirtualKeyboard
from core.i18n import _


class PasswordDialog(QDialog):
    """
    Dialogo modale con campo password + VirtualKeyboard integrata.

    Uso::
        dlg = PasswordDialog(parent=self, title="Accesso protetto",
                             prompt="Inserire la password:")
        if dlg.exec_() == QDialog.Accepted:
            pwd = dlg.password()
    """

    def __init__(self, parent=None, title: str = "", prompt: str = ""):
        super().__init__(parent)
        self.setWindowTitle(title or _("Accesso protetto"))
        self.setModal(True)
        # Nessun bordo / barra del titolo nativa (touch-friendly)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self._build_ui(prompt or _("Inserire la password:"))

    # ─── Build ──────────────────────────────────────────────────────────────

    def _build_ui(self, prompt: str) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(16)
        root.setContentsMargins(24, 24, 24, 24)

        # ── Titolo ──────────────────────────────────────────────────────────
        title_lbl = QLabel(self.windowTitle())
        title_lbl.setObjectName("pwdDialogTitle")
        title_lbl.setAlignment(Qt.AlignCenter)
        root.addWidget(title_lbl)

        # ── Separatore ──────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("pwdSeparator")
        root.addWidget(sep)

        # ── Prompt ──────────────────────────────────────────────────────────
        prompt_lbl = QLabel(prompt)
        prompt_lbl.setObjectName("pwdPrompt")
        prompt_lbl.setAlignment(Qt.AlignCenter)
        root.addWidget(prompt_lbl)

        # ── Campo password ───────────────────────────────────────────────────
        self._field = QLineEdit()
        self._field.setObjectName("pwdField")
        self._field.setEchoMode(QLineEdit.Password)
        self._field.setAlignment(Qt.AlignCenter)
        self._field.setReadOnly(True)          # input solo dalla tastiera virtuale
        self._field.setFixedHeight(56)
        root.addWidget(self._field)

        # ── Tastiera virtuale ────────────────────────────────────────────────
        self._keyboard = VirtualKeyboard()
        self._keyboard.key_pressed.connect(self._on_key)
        root.addWidget(self._keyboard)

        # ── Pulsanti OK / Annulla ────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(16)

        self._btn_cancel = QPushButton(_("Annulla"))
        self._btn_cancel.setObjectName("pwdCancelBtn")
        self._btn_cancel.setFixedHeight(56)
        self._btn_cancel.clicked.connect(self.reject)

        self._btn_ok = QPushButton(_("OK"))
        self._btn_ok.setObjectName("pwdOkBtn")
        self._btn_ok.setFixedHeight(56)
        self._btn_ok.clicked.connect(self.accept)

        btn_row.addWidget(self._btn_cancel)
        btn_row.addWidget(self._btn_ok)
        root.addLayout(btn_row)

    # ─── Slots ──────────────────────────────────────────────────────────────

    def _on_key(self, key: str) -> None:
        if key == "BACK":
            txt = self._field.text()
            self._field.setText(txt[:-1])
        elif key == "ENTER":
            self.accept()
        elif key == "SPACE":
            self._field.setText(self._field.text() + " ")
        elif key == "CAPS":
            pass  # gestito internamente dalla VirtualKeyboard
        else:
            self._field.setText(self._field.text() + key)

    # ─── API pubblica ────────────────────────────────────────────────────────

    def password(self) -> str:
        """Restituisce il testo inserito dall'utente."""
        return self._field.text()
