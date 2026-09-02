"""THROWAWAY spike: valida API e latência do fast-alpr.

Uso: edge/.venv/bin/python scripts/spike_alpr.py [caminho-da-imagem]
"""
import sys
import time

import cv2
from fast_alpr import ALPR

alpr = ALPR(
    detector_model="yolo-v9-t-384-license-plate-end2end",
    ocr_model="global-plates-mobile-vit-v2-model",
)
path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-spike-plate.png"
frame = cv2.imread(path)
if frame is None:
    raise SystemExit(f"imagem nao carregou: {path}")

alpr.predict(frame)  # warm-up (nao conta download/carga do modelo)
t0 = time.perf_counter()
results = alpr.predict(frame)
dt = time.perf_counter() - t0
print(f"latency={dt * 1000:.0f}ms n={len(results)}")
for r in results:
    print(repr(r))
    print("  detection attrs:", vars(r.detection) if hasattr(r.detection, "__dict__") else r.detection)
    print("  ocr attrs:", vars(r.ocr) if hasattr(r.ocr, "__dict__") else r.ocr)
