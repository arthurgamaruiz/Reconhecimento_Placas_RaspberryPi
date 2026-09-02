"""Gate de movimento barato: só deixa o ALPR rodar quando a cena mudou."""
import cv2
import numpy as np

_DIFF_LEVEL = 25  # intensidade mínima (0-255) para um pixel contar como mudança


class MotionGate:
    def __init__(self, threshold: float = 0.02, size: tuple[int, int] = (160, 120)):
        self._threshold = threshold
        self._size = size
        self._prev: np.ndarray | None = None

    def triggered(self, frame_bgr: np.ndarray) -> bool:
        small = cv2.cvtColor(cv2.resize(frame_bgr, self._size), cv2.COLOR_BGR2GRAY)
        prev, self._prev = self._prev, small
        if prev is None:
            return False
        ratio = (cv2.absdiff(small, prev) > _DIFF_LEVEL).mean()
        return bool(ratio > self._threshold)
