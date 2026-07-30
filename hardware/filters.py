"""
hardware/filters.py
--------------------
Filtri digitali applicati al segnale grezzo della cella di carico.
Nessuna dipendenza da Qt. Nessuno stato globale.

Filtri disponibili:
    MovingAverageFilter  — media mobile su N campioni (default: 5)
    NullFilter           — pass-through, usato quando il filtro è disabilitato
"""

from collections import deque


class MovingAverageFilter:
    """
    Media mobile (FIR non ricorsivo) su una finestra di N campioni.
    Utile per smussare il rumore elettrico della cella di carico.

    Usage:
        f = MovingAverageFilter(window=5)
        filtered = f.process(raw_value)
        f.reset()
    """

    def __init__(self, window: int = 5):
        """
        Args:
            window: Numero di campioni su cui calcolare la media.
                    Valori tipici: 3–10. Più alto = più smooth, più latenza.
        """
        if window < 1:
            raise ValueError("window deve essere >= 1")
        self._window = window
        self._buffer: deque[float] = deque(maxlen=window)

    def process(self, value: float) -> float:
        """
        Inserisce il nuovo campione e restituisce la media corrente.

        Finché il buffer non è pieno (avvio), la media è calcolata
        sui campioni disponibili — nessun ritardo artificiale.
        """
        self._buffer.append(value)
        return sum(self._buffer) / len(self._buffer)

    def reset(self) -> None:
        """Svuota il buffer. Da chiamare all'avvio di ogni nuovo pezzo."""
        self._buffer.clear()

    @property
    def window(self) -> int:
        return self._window


class NullFilter:
    """
    Filtro identità — restituisce il valore invariato.
    Usato quando il filtraggio è disabilitato dalla configurazione.
    """

    def process(self, value: float) -> float:
        return value

    def reset(self) -> None:
        pass
