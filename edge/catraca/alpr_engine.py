"""Wrapper do fast-alpr: melhor leitura do frame, já normalizada, com crop da placa.

ocr.confidence do fast-alpr vem como lista por caractere (às vezes com padding);
agregamos com min() — o pior caractere é o que decide se o fallback entra.
"""
from dataclasses import dataclass

import numpy as np

from catraca import plates

DETECTOR_MODEL = "yolo-v9-t-384-license-plate-end2end"
OCR_MODEL = "global-plates-mobile-vit-v2-model"


@dataclass
class PlateReading:
    plate: str
    ocr_confidence: float
    crop: np.ndarray


def _aggregate(confidence) -> float:
    if isinstance(confidence, (list, tuple)):
        return float(min(confidence)) if confidence else 0.0
    return float(confidence)


class AlprEngine:
    def __init__(self, alpr=None):
        self._alpr = alpr

    def _get_alpr(self):
        if self._alpr is None:
            from fast_alpr import ALPR

            self._alpr = ALPR(detector_model=DETECTOR_MODEL, ocr_model=OCR_MODEL)
        return self._alpr

    def read(self, frame_bgr: np.ndarray) -> PlateReading | None:
        results = [r for r in self._get_alpr().predict(frame_bgr) if r.ocr and r.ocr.text]
        if not results:
            return None
        best = max(results, key=lambda r: _aggregate(r.ocr.confidence))
        h, w = frame_bgr.shape[:2]
        bb = best.detection.bounding_box
        x1, y1 = max(0, int(bb.x1)), max(0, int(bb.y1))
        x2, y2 = min(w, int(bb.x2)), min(h, int(bb.y2))
        return PlateReading(
            plate=plates.normalize(best.ocr.text),
            ocr_confidence=_aggregate(best.ocr.confidence),
            crop=frame_bgr[y1:y2, x1:x2],
        )
