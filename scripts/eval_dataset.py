"""Avaliação quantitativa do ALPR num diretório de imagens rotuladas.

Rotulagem aceita (por imagem .jpg/.jpeg/.png):
  1. Arquivo .txt de mesmo nome contendo uma linha "plate: ABC1D23"
     (formato do dataset RodoSol-ALPR); ou
  2. O nome do arquivo começa com a placa: ABC1D23.jpg, ABC1D23_01.jpg, ...

Uso:
  edge/.venv/bin/python scripts/eval_dataset.py <dir-de-imagens> [max_imagens]

Saída (colar em docs/benchmarks.md):
  - acurácia bruta (OCR cru) e final (após correção de confusões)
  - latência média
  - top confusões de caracteres (esperado → lido)
"""
import re
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

import cv2

from catraca import plates
from catraca.alpr_engine import AlprEngine

PLATE_PREFIX = re.compile(r"^([A-Z]{3}\d[A-Z0-9]\d{2})")


def label_for(img: Path) -> str | None:
    txt = img.with_suffix(".txt")
    if txt.exists():
        for line in txt.read_text().splitlines():
            if line.lower().startswith("plate:"):
                return plates.normalize(line.split(":", 1)[1])
    m = PLATE_PREFIX.match(plates.normalize(img.stem))
    return m.group(1) if m else None


def main() -> None:
    root = Path(sys.argv[1])
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10_000
    images = sorted(
        p for p in root.rglob("*")
        if p.suffix.lower() in (".jpg", ".jpeg", ".png")
    )[:limit]
    if not images:
        raise SystemExit(f"nenhuma imagem em {root}")

    engine = AlprEngine()
    total = raw_ok = fixed_ok = detected = 0
    latencies: list[float] = []
    confusions: Counter[tuple[str, str]] = Counter()

    for img_path in images:
        expected = label_for(img_path)
        if expected is None or not plates.is_valid(expected):
            continue
        frame = cv2.imread(str(img_path))
        if frame is None:
            continue
        total += 1
        t0 = time.perf_counter()
        reading = engine.read(frame)
        latencies.append(time.perf_counter() - t0)
        if reading is None:
            continue
        detected += 1
        raw = reading.plate
        fixed = raw if plates.is_valid(raw) else (plates.fix_confusions(raw) or raw)
        raw_ok += raw == expected
        fixed_ok += fixed == expected
        if fixed != expected and len(fixed) == len(expected):
            for exp_ch, got_ch in zip(expected, fixed):
                if exp_ch != got_ch:
                    confusions[(exp_ch, got_ch)] += 1

    if total == 0:
        raise SystemExit("nenhuma imagem com rótulo de placa válido (ver docstring)")
    print(f"imagens avaliadas   : {total}")
    print(f"placa detectada     : {detected}/{total} ({100 * detected / total:.1f}%)")
    print(f"acuracia OCR bruta  : {raw_ok}/{total} ({100 * raw_ok / total:.1f}%)")
    print(f"acuracia final      : {fixed_ok}/{total} ({100 * fixed_ok / total:.1f}%)"
          f"  (+{fixed_ok - raw_ok} recuperadas pela correcao)")
    print(f"latencia media      : {1000 * statistics.mean(latencies):.0f} ms")
    print("top confusoes (esperado->lido):",
          [f"{a}->{b}: {n}" for (a, b), n in confusions.most_common(8)] or "nenhuma")


if __name__ == "__main__":
    main()
