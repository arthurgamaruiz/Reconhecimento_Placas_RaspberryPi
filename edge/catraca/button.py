"""Botão físico de autorização: um carro acabou de ser negado? Aperte o botão
e a placa entra na whitelist da nuvem na hora (janela de N segundos).
"""
import logging
import time
from collections.abc import Callable

from gpiozero import Button

log = logging.getLogger(__name__)


class AuthorizeButton:
    def __init__(self, client, pin: int = 23, window_s: float = 30.0,
                 clock: Callable[[], float] = time.monotonic,
                 on_authorized: Callable[[str], None] | None = None):
        self._client = client
        self._window = window_s
        self._clock = clock
        self._on_authorized = on_authorized
        self._last: tuple[str, float] | None = None
        self.button = Button(pin)
        self.button.when_pressed = self.pressed

    def register_denied(self, plate: str) -> None:
        self._last = (plate, self._clock())

    def pressed(self) -> None:
        if self._last is None:
            return
        plate, ts = self._last
        if self._clock() - ts > self._window:
            self._last = None
            return
        try:
            ok = self._client.add_plate(plate, "Autorizado no botão")
        except Exception:
            log.warning("botão: falha ao autorizar %s na nuvem", plate, exc_info=True)
            return
        if not ok:
            return  # mantém pendente para nova tentativa
        self._last = None
        log.info("botão: placa %s autorizada", plate)
        if self._on_authorized is not None:
            self._on_authorized(plate)

    def close(self) -> None:
        self.button.close()
