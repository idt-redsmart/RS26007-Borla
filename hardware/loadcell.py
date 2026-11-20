import random
import math
import time
import logging

from hardware.rpc_bridge import ArduinoRPCBridge

logger = logging.getLogger(__name__)

_MOCK = False

_DEFAULT_TIMEOUT = 5.0
_COMMAND_TIMEOUT = 15.0     # calibrazione: 500 campioni a 80 SPS ≈ 6 s
_POLL_INTERVAL   = 0.1


class LoadCellError(RuntimeError):
    """Lettura o comando non riuscito: il valore non va usato."""


class LoadCell:

    def __init__(self):
        self._bridge = ArduinoRPCBridge()
        self._connected = False
        self._t0 = 0.0
        self.last_error = ""        # perché l'ultimo connect() non è riuscito

    def connect(self) -> bool:
        if _MOCK:
            self._connected = True
            self._t0 = time.monotonic()
            return True

        try:
            self._bridge.connect()

            self._connected = bool(
                self._bridge.call(
                    "isReady",
                    timeout=_DEFAULT_TIMEOUT
                )
            )

            # Il worker ritenta finché la scheda non è pronta: niente INFO a ogni giro
            logger.log(
                logging.INFO if self._connected else logging.DEBUG,
                "LoadCell Bridge: isReady=%s",
                self._connected
            )

            self.last_error = "" if self._connected else (
                "isReady=False: lo sketch risponde ma il NAU7802 non è inizializzato"
            )
            return self._connected

        except Exception as e:
            logger.debug(
                "LoadCell connect: %s",
                e
            )

            self.last_error = f"{type(e).__name__}: {e}"
            if isinstance(e, PermissionError):
                # Socket del router ricreato con permessi ristretti (riavvio, flash da App Lab)
                self.last_error += " → sudo bash tools/router_socket_permissions.sh"
            self._connected = False
            return False

    def tare(self) -> None:
        if _MOCK:
            return

        try:
            self._run_command("tare")

        except Exception as e:
            logger.error("LoadCell tare: %s", e)
            raise

    def calibrate(self, reference_mn: float) -> float:
        """
        Calibra con un peso noto appoggiato (dopo una tara a vuoto).
        Restituisce il nuovo fattore di scala [mN / conteggio ADC].
        """
        if _MOCK:
            return 1.0

        try:
            self._run_command("calibrate", float(reference_mn))
            return self.get_scale_factor()

        except Exception as e:
            logger.error("LoadCell calibrate: %s", e)
            raise

    def set_scale_factor(self, factor: float) -> None:
        if _MOCK:
            return

        try:
            self._run_command("setScaleFactor", float(factor))

        except Exception as e:
            logger.error("LoadCell setScaleFactor: %s", e)
            raise

    def get_scale_factor(self) -> float:
        if _MOCK:
            return 1.0

        return float(
            self._bridge.call(
                "getScaleFactor",
                timeout=_DEFAULT_TIMEOUT
            )
        )

    def read(self) -> float:
        """
        Forza attuale [mN].
        Solleva LoadCellError se la lettura non è valida: un errore non deve
        mai diventare un campione da 0 mN.
        """
        if not self._connected:
            raise LoadCellError("cella di carico non connessa")

        if _MOCK:
            t = time.monotonic() - self._t0

            return round(
                1200.0
                + 80.0 * math.sin(t * 0.3)
                + random.gauss(0, 25),
                2
            )

        try:
            value = float(
                self._bridge.call(
                    "readForce",
                    timeout=_DEFAULT_TIMEOUT
                )
            )

        except Exception as e:
            raise LoadCellError(f"readForce: {e}") from e

        # Lo sketch restituisce NaN quando il sensore non risponde
        if math.isnan(value):
            raise LoadCellError("readForce: sensore non pronto")

        return value

    def disconnect(self) -> None:
        self._connected = False

        try:
            self._bridge.close()
        except Exception:
            pass

    @property
    def is_connected(self) -> bool:
        return self._connected

    def _run_command(self, method: str, *args) -> None:
        """
        Avvia un comando sulla scheda e ne attende la fine.
        Lo sketch mette il comando in coda e lo esegue nel loop():
        l'avanzamento si legge con isBusy, l'esito con lastCommandOk.
        """
        accepted = self._bridge.call(
            method,
            *args,
            timeout=_DEFAULT_TIMEOUT
        )

        if not accepted:
            raise LoadCellError(f"{method}: comando rifiutato (scheda occupata)")

        deadline = time.monotonic() + _COMMAND_TIMEOUT

        while self._bridge.call("isBusy", timeout=_DEFAULT_TIMEOUT):
            if time.monotonic() > deadline:
                raise LoadCellError(f"{method}: timeout")

            time.sleep(_POLL_INTERVAL)

        if not self._bridge.call("lastCommandOk", timeout=_DEFAULT_TIMEOUT):
            raise LoadCellError(f"{method}: non riuscito sulla scheda")
