"""
verify_hardware.py — verifica del layer hardware, non fa parte del prodotto
"""
import sys
sys.path.insert(0, ".")

from hardware.filters import MovingAverageFilter, NullFilter
from hardware.loadcell import LoadCell
from hardware.acquisition_worker import AcquisitionWorker

print("=== Filtri ===")
f = MovingAverageFilter(window=5)
vals = [1100.0, 1150.0, 1200.0, 1250.0, 1300.0]
results = [f.process(v) for v in vals]
print(f"Input:    {vals}")
print(f"Filtered: {[round(r, 1) for r in results]}")

f.reset()
nf = NullFilter()
print(f"NullFilter: {nf.process(1234.5)}")

print("\n=== LoadCell (mock) ===")
lc = LoadCell()
ok = lc.connect()
print(f"connect()  -> {ok}")
print(f"connected  -> {lc.is_connected}")

lc.tare()
print(f"tare()     -> OK")

samples = [lc.read() for _ in range(10)]
print(f"read() x10 -> min={min(samples):.1f}  max={max(samples):.1f}  mean={sum(samples)/len(samples):.1f}")

lc.disconnect()
print(f"disconnect -> is_connected={lc.is_connected}")

print("\n=== AcquisitionWorker costruzione ===")
w = AcquisitionWorker(loadcell=LoadCell(), sampling_rate=10, filter_window=3)
print(f"sampling_rate -> {w.sampling_rate} Hz")
print(f"isRunning     -> {w.isRunning()}")

print("\nAll hardware checks OK")
