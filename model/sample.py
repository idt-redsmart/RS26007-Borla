"""
model/sample.py
---------------
Singolo campione acquisito durante un collaudo.
Classe dati pura — nessuna logica.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Sample:
    """
    Un campione di forza acquisito durante un ciclo di collaudo.

    Attributes:
        force_mn:   Forza misurata in milliNewton.
        timestamp:  Istante di acquisizione.
        piece_idx:  Indice del pezzo a cui appartiene il campione (0-based).
        in_range:   True se la forza è dentro la finestra [lsl, usl].
    """

    force_mn:  float
    timestamp: datetime = field(default_factory=datetime.now)
    piece_idx: int = 0
    in_range:  bool = True
