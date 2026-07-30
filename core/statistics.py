"""
core/statistics.py
------------------
Funzioni pure per il calcolo delle statistiche su una lista di campioni.
Non dipende da Qt. Non ha stato.
"""

import math
from model.sample import Sample


def compute(samples: list[Sample]) -> dict:
    """
    Calcola le statistiche su una lista di Sample.

    Args:
        samples: Lista di Sample acquisiti durante la sessione.

    Returns:
        dict con le chiavi:
            qty   (int)   — numero campioni
            min   (float) — valore minimo [mN]
            mean  (float) — valore medio [mN]
            max   (float) — valore massimo [mN]
            std   (float) — deviazione standard [mN]
            range (float) — range max-min [mN]
    """
    if not samples:
        return {"qty": 0, "min": 0.0, "mean": 0.0,
                "max": 0.0, "std": 0.0, "range": 0.0}

    values = [s.force_mn for s in samples]
    n      = len(values)
    min_v  = min(values)
    max_v  = max(values)
    mean   = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    std    = math.sqrt(variance)
    rng    = max_v - min_v

    return {
        "qty":   n,
        "min":   min_v,
        "mean":  mean,
        "max":   max_v,
        "std":   std,
        "range": rng,
    }


def is_pass(samples: list[Sample], lsl: float, usl: float) -> bool:
    """
    Restituisce True se TUTTI i campioni rientrano nella finestra [lsl, usl].
    Un singolo campione fuori range porta l'intera sessione a FAIL.
    """
    return all(lsl <= s.force_mn <= usl for s in samples)
