"""
model/test_result.py
--------------------
Risultato completo di una sessione di collaudo.
Classe dati pura — nessuna logica.
"""

from dataclasses import dataclass, field
from datetime import datetime
from model.sample import Sample


@dataclass
class TestResult:
    """
    Rappresenta il risultato di una sessione di collaudo completa.

    Una sessione può contenere N pezzi. Ogni pezzo è un ciclo
    trigger → acquisizione 4s → valutazione.

    Attributes:
        id:                 Identificativo univoco (assegnato dal database).
        date:               Data e ora di inizio sessione.
        operator:           Nome dell'operatore.
        mould:              Codice stampo (es. PF0924/2).
        production_lot:     Lotto di produzione.
        raw_material_lot:   Lotto materia prima.
        samples:            Tutti i campioni acquisiti nell'intera sessione.
        qty:                Numero di pezzi collaudati.
        min_mn:             Valore minimo rilevato [mN].
        mean_mn:            Valore medio [mN].
        max_mn:             Valore massimo rilevato [mN].
        std_mn:             Deviazione standard [mN].
        range_mn:           Range (max - min) [mN].
        lower_limit:        Limite inferiore usato durante il collaudo [mN].
        upper_limit:        Limite superiore usato durante il collaudo [mN].
        result:             "PASS" o "FAIL".
        pdf_path:           Percorso del PDF generato (vuoto finché non generato).
    """

    # ─── Identificazione ────────────────────────────────────────────────────
    id:               int      = -1
    date:             datetime = field(default_factory=datetime.now)

    # ─── Dati operatore ─────────────────────────────────────────────────────
    operator:         str = ""
    mould:            str = ""
    production_lot:   str = ""
    raw_material_lot: str = ""

    # ─── Campioni ───────────────────────────────────────────────────────────
    samples:          list[Sample] = field(default_factory=list)
    qty:              int   = 0

    # ─── Statistiche ────────────────────────────────────────────────────────
    min_mn:           float = 0.0
    mean_mn:          float = 0.0
    max_mn:           float = 0.0
    std_mn:           float = 0.0
    range_mn:         float = 0.0

    # ─── Parametri di collaudo ───────────────────────────────────────────────
    lower_limit:      float = 1060.0
    upper_limit:      float = 1350.0

    # ─── Esito ──────────────────────────────────────────────────────────────
    result:           str = "—"        # "PASS" | "FAIL"
    pdf_path:         str = ""
