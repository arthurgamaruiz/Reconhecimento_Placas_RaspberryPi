"""Benchmark do pipeline no Pi: FPS de captura, latência do ALPR, taxa de leitura.

Rodar NO PI com a webcam apontada para uma placa impressa:
  ~/catraca/venv/bin/python ~/catraca/benchmark_alpr.py [largura] [altura] [n_frames]
Ex.: ... benchmark_alpr.py 640 480 50
Copiar a saída para docs/benchmarks.md (material do relatório).
"""
import statistics
import sys
import time

import cv2

from catraca import plates
from catraca.alpr_engine import AlprEngine

width = int(sys.argv[1]) if len(sys.argv) > 1 else 1280
height = int(sys.argv[2]) if len(sys.argv) > 2 else 720
n = int(sys.argv[3]) if len(sys.argv) > 3 else 50

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
if not cap.isOpened():
    raise SystemExit("webcam nao abriu")

engine = AlprEngine()
ok, frame = cap.read()
if not ok:
    raise SystemExit("sem frame")
engine.read(frame)  # warm-up: carrega os modelos fora da medição

t0 = time.perf_counter()
for _ in range(n):
    cap.read()
capture_fps = n / (time.perf_counter() - t0)

latencies, valid, texts = [], 0, []
for _ in range(n):
    ok, frame = cap.read()
    if not ok:
        continue
    t0 = time.perf_counter()
    reading = engine.read(frame)
    latencies.append(time.perf_counter() - t0)
    if reading and plates.is_valid(plates.fix_confusions(reading.plate) or reading.plate):
        valid += 1
        texts.append(reading.plate)

lat_ms = sorted(x * 1000 for x in latencies)
p95 = lat_ms[int(len(lat_ms) * 0.95) - 1]
print(f"resolucao          : {width}x{height}")
print(f"captura            : {capture_fps:.1f} fps")
print(f"latencia ALPR media: {statistics.mean(lat_ms):.0f} ms")
print(f"latencia ALPR p95  : {p95:.0f} ms")
print(f"throughput ALPR    : {1000 / statistics.mean(lat_ms):.1f} fps")
print(f"leituras validas   : {valid}/{n} ({100 * valid / n:.0f}%)")
print(f"placas mais lidas  : {sorted(set(texts), key=texts.count, reverse=True)[:3]}")
cap.release()
