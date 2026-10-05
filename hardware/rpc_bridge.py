import socket
import logging

import msgpack

log = logging.getLogger(__name__)


class ArduinoRPCBridge:

    SOCKET_PATH = "/var/run/arduino-router.sock"

    def __init__(self):
        self.connected = False
        self._request_id = 0

    def connect(self):
        if not self.connected:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.connect(self.SOCKET_PATH)

            self.connected = True
            log.info(
                "Arduino RPC Bridge inizializzato: %s",
                self.SOCKET_PATH
            )

    def close(self):
        self.connected = False
        log.info("Arduino RPC Bridge chiuso")

    def call(self, method, *args, timeout=5.0):
        if not self.connected:
            raise RuntimeError(
                "Arduino RPC Bridge non connesso"
            )

        self._request_id += 1
        request_id = self._request_id

        request = [
            0,
            request_id,
            method,
            list(args)
        ]

        packet = msgpack.packb(
            request,
            use_bin_type=True
        )

        with socket.socket(
            socket.AF_UNIX,
            socket.SOCK_STREAM
        ) as sock:

            sock.settimeout(timeout)

            sock.connect(self.SOCKET_PATH)

            log.debug(
                "RPC -> method=%s args=%s",
                method,
                args
            )

            sock.sendall(packet)

            unpacker = msgpack.Unpacker(raw=False)

            while True:
                data = sock.recv(4096)

                if not data:
                    raise RuntimeError(
                        "Connessione RPC chiusa senza risposta"
                    )

                unpacker.feed(data)

                for response in unpacker:

                    log.debug(
                        "RPC <- %s",
                        response
                    )

                    if not isinstance(response, list):
                        continue

                    if len(response) != 4:
                        continue

                    response_type = response[0]
                    response_id = response[1]
                    error = response[2]
                    result = response[3]

                    if response_type != 1:
                        continue

                    if response_id != request_id:
                        continue

                    if error is not None:
                        raise RuntimeError(
                            f"Errore RPC {method}: {error}"
                        )

                    return result