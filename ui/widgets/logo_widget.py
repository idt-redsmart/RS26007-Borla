"""
logo_widget.py
--------------
Widget che mostra il logo del cliente.
Se il file non esiste, mostra il nome azienda come testo fallback.
"""

from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from config import Config


class LogoWidget(QLabel):
    """
    QLabel che carica il logo da Config.logo_path.
    - Se il file esiste: mostra l'immagine scalata a max_h pixel di altezza.
    - Se il file non esiste: mostra il nome azienda come testo.

    Parametri:
        max_h   : altezza massima in pixel (default 48)
        max_w   : larghezza massima in pixel (default 180)
        align   : Qt.Alignment per il testo fallback (default AlignRight|AlignVCenter)
    """

    def __init__(self, parent=None, max_h: int = 48, max_w: int = 180,
                 align=Qt.AlignRight | Qt.AlignVCenter):
        super().__init__(parent)
        self.setAlignment(align)
        self._max_h = max_h
        self._max_w = max_w
        self.reload()

    def reload(self) -> None:
        """Ricarica il logo da disco (utile se il path cambia a runtime)."""
        logo_path = Config.logo_path
        if logo_path is not None:
            pix = QPixmap(str(logo_path))
            if not pix.isNull():
                scaled = pix.scaled(
                    self._max_w, self._max_h,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                self.setPixmap(scaled)
                self.setText("")
                return
        # Fallback testo
        self.setPixmap(QPixmap())
        self.setText(Config.company_name)
        self.setObjectName("companyLabel")
