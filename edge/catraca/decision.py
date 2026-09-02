"""Decisão de acesso com cooldown por placa (evita re-acionar no carro parado)."""
import time
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Decision:
    plate: str
    authorized: bool
    name: str | None


class DecisionEngine:
    def __init__(
        self,
        whitelist,
        cooldown_s: float = 10.0,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._whitelist = whitelist
        self._cooldown_s = cooldown_s
        self._clock = clock
        self._last_seen: dict[str, float] = {}

    def decide(self, plate: str) -> Decision | None:
        now = self._clock()
        last = self._last_seen.get(plate)
        if last is not None and now - last < self._cooldown_s:
            return None
        self._last_seen[plate] = now
        name = self._whitelist.lookup(plate)
        return Decision(plate=plate, authorized=name is not None, name=name)
