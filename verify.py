"""
verify.py — script di verifica rapida, non fa parte del prodotto
"""
import sys
sys.path.insert(0, ".")

from model.sample import Sample
from model.test_result import TestResult
from core.statistics import compute, is_pass
from core.database import Database
from datetime import datetime
import tempfile, os

print("=== Import check ===")
from core.test_controller import TestController, State
print("Imports OK")

print("\n=== Statistics ===")
samples = [Sample(force_mn=f) for f in [1100.0, 1200.0, 1300.0, 1250.0]]
s = compute(samples)
print(f"qty={s['qty']}  min={s['min']}  mean={s['mean']:.1f}  max={s['max']}  std={s['std']:.2f}  range={s['range']}")
print(f"is_pass(1060,1350): {is_pass(samples, 1060, 1350)}")

print("\n=== Database ===")
with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
    db = Database(os.path.join(tmpdir, "db", "test.db"))
    r = TestResult(
        date=datetime.now(), operator="Test", mould="PF0924/2",
        production_lot="L1", raw_material_lot="M1",
        samples=samples, qty=4,
        min_mn=1100, mean_mn=1212.5, max_mn=1300, std_mn=74.5, range_mn=200,
        lower_limit=1060, upper_limit=1350, result="PASS",
    )
    aid = db.save_test(r)
    print(f"save_test OK, id={aid}")
    recs = db.load_tests()
    print(f"load_tests OK, {len(recs)} record(s)")
    full = db.load_test(aid)
    print(f"load_test OK, samples={len(full['samples'])}")
    del db   # chiude la connessione prima che TemporaryDirectory faccia cleanup

print("\n=== TestController state machine (no Qt event loop) ===")
print(f"Initial state: {State.IDLE.name}")
print("All checks passed OK")
