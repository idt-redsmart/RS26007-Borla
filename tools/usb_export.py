"""
usb_export.py
-------------
Copia automatica dei report su chiavetta USB (solo Linux).

Resta in ascolto: quando viene inserita una chiavetta USB, copia tutto il
contenuto della cartella report (Config.reports_path) in
    <chiavetta>/Borla_Reports/
mantenendo le sottocartelle. I file già presenti sulla chiavetta con la stessa
dimensione vengono saltati, quindi reinserire la stessa chiavetta copia solo
i report nuovi.

Se il desktop non monta da solo la chiavetta, lo script prova a montarla con
`udisksctl` (pacchetto udisks2). A fine copia la chiavetta viene smontata e
spenta, e un popup avvisa l'operatore che può rimuoverla.

Uso:
    python tools/usb_export.py            # resta in ascolto (servizio)
    python tools/usb_export.py --once     # copia sulle chiavette già inserite ed esce
"""

import argparse
import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import Config  # noqa: E402

DEST_DIR_NAME = "Borla_Reports"
POLL_INTERVAL = 2.0     # secondi tra un controllo e l'altro
POPUP_TIMEOUT = 15      # secondi dopo cui il popup si chiude da solo

log = logging.getLogger("usb_export")


# ─── Rilevamento chiavette ──────────────────────────────────────────────────

def _is_usb_disk(disk: str) -> bool:
    """True se /sys/block/<disk> è un disco collegato via USB."""
    try:
        return "/usb" in os.path.realpath(f"/sys/block/{disk}")
    except OSError:
        return False


def _usb_partitions() -> list[str]:
    """Device delle partizioni USB (o del disco intero se non partizionato)."""
    devices = []
    for disk in sorted(os.listdir("/sys/block")):
        if not disk.startswith("sd") or not _is_usb_disk(disk):
            continue
        parts = [p for p in sorted(os.listdir(f"/sys/block/{disk}")) if p.startswith(disk)]
        devices.extend(f"/dev/{p}" for p in (parts or [disk]))
    return devices


def _usb_mounts() -> dict[str, str]:
    """{device: mountpoint} delle partizioni USB attualmente montate."""
    usb = set(_usb_partitions())
    mounts = {}
    with open("/proc/mounts") as f:
        for line in f:
            dev, mnt = line.split()[:2]
            if dev in usb:
                # /proc/mounts codifica gli spazi come \040
                mounts[dev] = mnt.replace("\\040", " ")
    return mounts


def _try_mount(devices: list[str], tried: set[str]) -> None:
    """Monta con udisksctl le partizioni USB non ancora montate (un tentativo ciascuna)."""
    if not shutil.which("udisksctl"):
        return
    for dev in devices:
        if dev in tried:
            continue
        tried.add(dev)
        res = subprocess.run(
            ["udisksctl", "mount", "-b", dev, "--no-user-interaction"],
            capture_output=True, text=True,
        )
        if res.returncode == 0:
            log.info("Montato %s: %s", dev, res.stdout.strip())
        else:
            log.debug("Mount %s non riuscito: %s", dev, res.stderr.strip())


# ─── Copia ──────────────────────────────────────────────────────────────────

def export_to(mountpoint: str) -> tuple[bool, str]:
    """Copia i report sulla chiavetta. Ritorna (ok, messaggio per l'operatore)."""
    src_root = Config.reports_path
    dst_root = Path(mountpoint) / DEST_DIR_NAME

    if not os.access(mountpoint, os.W_OK):
        log.warning("Chiavetta %s non scrivibile, salto", mountpoint)
        return False, "Chiavetta non scrivibile."

    copied = skipped = failed = 0
    for src in src_root.rglob("*"):
        if not src.is_file():
            continue
        dst = dst_root / src.relative_to(src_root)
        try:
            if dst.exists() and dst.stat().st_size == src.stat().st_size:
                skipped += 1
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            # copyfile + utime: copy2 può fallire sui permessi su FAT/exFAT
            shutil.copyfile(src, dst)
            try:
                st = src.stat()
                os.utime(dst, (st.st_atime, st.st_mtime))
            except OSError:
                pass
            copied += 1
        except OSError as e:
            failed += 1
            log.error("Errore copiando %s: %s", src.name, e)

    os.sync()   # scrive tutto su chiavetta prima di smontarla
    msg = f"Report copiati: {copied} nuovi, {skipped} già presenti"
    if failed:
        msg += f", {failed} errori"
    log.info("%s → %s", msg, dst_root)
    return failed == 0, msg + "."


def eject(device: str) -> bool:
    """Smonta la partizione e spegne il disco USB. True se smontata."""
    if not shutil.which("udisksctl"):
        log.error("udisksctl non disponibile: impossibile smontare %s", device)
        return False
    res = subprocess.run(
        ["udisksctl", "unmount", "-b", device, "--no-user-interaction"],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        log.error("Smontaggio %s fallito: %s", device, res.stderr.strip())
        return False
    log.info("Smontato %s", device)

    # Spegne il disco intero (es. /dev/sda1 → /dev/sda): il LED si spegne
    disk = "/dev/" + os.path.basename(os.path.realpath(f"/sys/class/block/{os.path.basename(device)}/.."))
    if not os.path.exists(f"/sys/block/{os.path.basename(disk)}"):
        disk = device   # partizione == disco intero (chiavetta non partizionata)
    subprocess.run(
        ["udisksctl", "power-off", "-b", disk, "--no-user-interaction"],
        capture_output=True, text=True,
    )
    return True


# ─── Popup ──────────────────────────────────────────────────────────────────

# Popup touch-friendly in un processo separato (non blocca il ciclo di ascolto)
_POPUP_CODE = r"""
import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt, QTimer
app = QApplication(sys.argv)
title, text, ok, timeout = sys.argv[1], sys.argv[2], sys.argv[3] == "1", int(sys.argv[4])
box = QMessageBox(QMessageBox.Information if ok else QMessageBox.Warning, title, text)
box.setWindowFlags(box.windowFlags() | Qt.WindowStaysOnTopHint)
box.setStyleSheet(
    "QMessageBox { background: #111827; }"
    "QLabel { color: #e2e8f0; font-size: 22px; padding: 12px; min-width: 460px; }"
    "QPushButton { font-size: 20px; min-width: 160px; min-height: 56px;"
    " background: #00c8ff; color: #0b0f1a; border-radius: 8px; }"
)
QTimer.singleShot(timeout * 1000, box.accept)
box.exec_()
"""


def _popup(title: str, text: str, ok: bool) -> None:
    """Mostra un popup sullo schermo del tablet (PyQt5, fallback notify-send)."""
    env = os.environ.copy()
    env.setdefault("DISPLAY", ":0")     # il servizio systemd non eredita il display
    env.setdefault("XAUTHORITY", str(Path.home() / ".Xauthority"))
    try:
        subprocess.Popen(
            [sys.executable, "-c", _POPUP_CODE, title, text, "1" if ok else "0", str(POPUP_TIMEOUT)],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except OSError as e:
        log.warning("Popup non disponibile (%s), uso notify-send", e)
        if shutil.which("notify-send"):
            subprocess.run(["notify-send", title, text], env=env, capture_output=True)


# ─── Main ───────────────────────────────────────────────────────────────────

def run(once: bool) -> None:
    handled: set[str] = set()       # device già esportati (finché restano collegati)
    mount_tried: set[str] = set()   # device su cui si è già tentato il mount

    log.info("In attesa di chiavette USB (sorgente: %s)", Config.reports_path)
    while True:
        devices = set(_usb_partitions())
        # Chiavetta rimossa → al reinserimento si ricomincia da capo
        handled &= devices
        mount_tried &= devices

        mounts = _usb_mounts()
        # Non rimontare le chiavette già esportate e smontate
        _try_mount([d for d in sorted(devices) if d not in mounts and d not in handled], mount_tried)
        mounts = _usb_mounts()

        for dev, mnt in sorted(mounts.items()):
            if dev in handled:
                continue
            handled.add(dev)
            log.info("Chiavetta rilevata: %s su %s", dev, mnt)
            ok, msg = export_to(mnt)
            if eject(dev):
                msg += "\n\nOra puoi rimuovere la chiavetta."
            else:
                ok = False
                msg += "\n\nImpossibile smontare la chiavetta:\nattendere qualche secondo prima di rimuoverla."
            _popup("Export report USB", msg, ok)

        if once:
            return
        time.sleep(POLL_INTERVAL)


def main() -> None:
    parser = argparse.ArgumentParser(description="Copia i report su chiavetta USB")
    parser.add_argument("--once", action="store_true",
                        help="copia sulle chiavette già inserite ed esce")
    args = parser.parse_args()

    if not sys.platform.startswith("linux"):
        sys.exit("usb_export.py funziona solo su Linux")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(Config.logs_path / "usb_export.log", encoding="utf-8"),
        ],
    )
    try:
        run(args.once)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
