"""
hardware/loadcell.py
---------------------
Interfaccia verso la cella di carico

Tutto il resto dell'applicazione usa solo questa API:

    lc = LoadCell()
    lc.connect()    → bool
    lc.tare()       → None
    lc.read()       → float  (mN)
    lc.disconnect() → None

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  MOCK ATTIVO — MODALITÀ SIMULAZIONE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  In questa versione tutti i metodi sono STUB che simulano la cella di carico
  con numeri casuali gaussiani centrati a 1200 mN.

  Per collegare il sensore reale:
    1. Sostituire il corpo dei 4 metodi pubblici (connect/tare/read/disconnect)
       con il codice dei tuoi "bricks" Arduino / Qwiic.
    2. Aggiornare _MOCK = False per disabilitare la simulazione.
    3. Il resto dell'applicazione non richiede modifiche.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import random
import math
import time
import logging

logger = logging.getLogger(__name__)

# ─── Attiva / disattiva il mock ──────────────────────────────────────────────
_MOCK = True


class LoadCell:
    """
    Interfaccia alla cella di carico.

    In modalità mock genera un segnale sinusoidale + rumore gaussiano
    per simulare un ciclo realistico di test elastico.
    """

    def __init__(self):
        self._connected: bool = False
        self._tare_offset: float = 0.0

        # ── Stato interno simulazione ────────────────────────────────────────
        self._mock_phase: float = 0.0       # fase del segnale simulato
        self._mock_t0: float = 0.0          # timestamp avvio connessione

    # ─── API pubblica ────────────────────────────────────────────────────────

    def connect(self) -> bool:
        """
        Apre la connessione con la cella di carico.

        Returns:
            True se la connessione è riuscita, False altrimenti.
        """
        if _MOCK:
            return self._mock_connect()

        # ── TODO: inserire qui il codice di connessione hardware ─────────────
        #
        # Esempio con libreria qwiic:
        #   self._sensor = qwiic_nau7802.QwiicNAU7802()
        #   if not self._sensor.begin():
        #       logger.error("NAU7802 non rilevato sul bus I2C")
        #       return False
        #   self._sensor.setSampleRate(qwiic_nau7802.NAU7802_SPS_320)
        #   self._sensor.setGain(qwiic_nau7802.NAU7802_GAIN_128)
        #   self._sensor.calibrateAFE()
        #
        # oppure con Serial/Arduino bricks:
        #   self._serial = serial.Serial(port, baudrate, timeout=1)
        #   self._serial.write(b"CONNECT\n")
        #   resp = self._serial.readline()
        #   ...
        #
        # ────────────────────────────────────────────────────────────────────
        raise NotImplementedError("Implementare la connessione hardware")

    def tare(self) -> None:
        """
        Esegue la taratura (azzeramento) della cella di carico.
        Da chiamare con il posaggio scarico prima di ogni sessione.
        """
        if _MOCK:
            self._mock_tare()
            return

        # ── TODO: inserire qui il codice di taratura hardware ────────────────
        #
        # Esempio:
        #   self._sensor.calculateZeroOffset(64)  # media su 64 letture
        #   self._tare_offset = self._sensor.getZeroOffset()
        #
        # ────────────────────────────────────────────────────────────────────
        raise NotImplementedError("Implementare la taratura hardware")

    def read(self) -> float:
        """
        Legge un campione dalla cella di carico.

        Returns:
            Forza misurata in milliNewton [mN], già corretta per la tara.
            Restituisce 0.0 in caso di errore di lettura.
        """
        if not self._connected:
            logger.warning("read() chiamato senza connessione attiva")
            return 0.0

        if _MOCK:
            return self._mock_read()

        # ── TODO: inserire qui il codice di lettura hardware ─────────────────
        #
        # Esempio con NAU7802:
        #   if not self._sensor.available():
        #       return 0.0
        #   raw = self._sensor.getReading()
        #   force_n  = (raw - self._tare_offset) * self._calibration_factor
        #   return force_n * 1000.0   # → mN
        #
        # Esempio con Arduino bricks via Serial:
        #   self._serial.write(b"READ\n")
        #   line = self._serial.readline().decode().strip()
        #   return float(line)   # atteso in mN
        #
        # ────────────────────────────────────────────────────────────────────
        raise NotImplementedError("Implementare la lettura hardware")

    def disconnect(self) -> None:
        """Chiude la connessione con la cella di carico."""
        if _MOCK:
            self._connected = False
            logger.debug("[MOCK] LoadCell disconnessa")
            return

        # ── TODO: inserire qui il codice di disconnessione hardware ──────────
        #
        # Esempio:
        #   if hasattr(self, '_serial') and self._serial.is_open:
        #       self._serial.close()
        #
        # ────────────────────────────────────────────────────────────────────
        self._connected = False

    # ─── Proprietà ───────────────────────────────────────────────────────────

    @property
    def is_connected(self) -> bool:
        return self._connected

    # ─── Simulazione (MOCK) ─────────────────────────────────────────────────

    def _mock_connect(self) -> bool:
        """Simula una connessione riuscita."""
        self._connected = True
        self._mock_t0 = time.monotonic()
        logger.debug("[MOCK] LoadCell connessa")
        return True

    def _mock_tare(self) -> None:
        """Simula la taratura."""
        self._tare_offset = 0.0
        logger.debug("[MOCK] Taratura completata")

    def _mock_read(self) -> float:
        """
        Genera un valore di forza simulato.

        Il segnale è la somma di:
          - Un valore base oscillante (simula la variazione pezzo-per-pezzo)
          - Rumore gaussiano (simula il rumore elettrico del sensore)

        I valori restano prevalentemente nell'intervallo [1060, 1350] mN
        con qualche uscita di range per rendere la simulazione realistica.
        """
        t = time.monotonic() - self._mock_t0

        # Oscillazione lenta centrata a 1200 mN, ampiezza ±80 mN
        base = 1200.0 + 80.0 * math.sin(t * 0.3)

        # Rumore gaussiano σ = 25 mN (simula ADC + vibrazioni meccaniche)
        noise = random.gauss(0.0, 25.0)

        return round(base + noise, 2)
