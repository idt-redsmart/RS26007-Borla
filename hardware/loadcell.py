import random
import math
import time
import logging

from hardware.rpc_bridge import ArduinoRPCBridge

logger = logging.getLogger(__name__)

_MOCK = False

_DEFAULT_TIMEOUT = 5.0
_TARE_TIMEOUT = 15.0


class LoadCell:

    def __init__(self):
        self._bridge = ArduinoRPCBridge()
        self._connected = False
        self._t0 = 0.0

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

            logger.info(
                "LoadCell Bridge: isReady=%s",
                self._connected
            )

            return self._connected

        except Exception as e:
            logger.error(
                "LoadCell connect: %s",
                e
            )

            self._connected = False
            return False

    def tare(self) -> None:
        if _MOCK:
            return

        try:
            self._bridge.call(
                "tare",
                timeout=_TARE_TIMEOUT
            )

        except Exception as e:
            logger.error("LoadCell tare: %s", e)
            raise

    def read(self) -> float:
        if not self._connected:
            return 0.0

        if _MOCK:
            t = time.monotonic() - self._t0

            return round(
                1200.0
                + 80.0 * math.sin(t * 0.3)
                + random.gauss(0, 25),
                2
            )

        try:
            value = self._bridge.call(
                "readForce",
                timeout=_DEFAULT_TIMEOUT
            )

            return float(value)

        except Exception as e:
            logger.error(
                "LoadCell readForce: %s",
                e
            )

            return 0.0

    def disconnect(self) -> None:
        self._connected = False

        try:
            self._bridge.close()
        except Exception:
            pass

    @property
    def is_connected(self) -> bool:
        return self._connected