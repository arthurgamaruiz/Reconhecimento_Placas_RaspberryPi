"""Normalização, validação e correção de placas BR (Mercosul e formato antigo)."""
import re

MERCOSUR = re.compile(r"^[A-Z]{3}\d[A-Z]\d{2}$")
OLD_BR = re.compile(r"^[A-Z]{3}\d{4}$")

# Confusões clássicas de OCR, na direção dígito→letra e o inverso.
_TO_LETTER = {"0": "O", "1": "I", "2": "Z", "5": "S", "6": "G", "8": "B"}
_TO_DIGIT = {v: k for k, v in _TO_LETTER.items()}
_LAYOUTS = ("LLLDLDD", "LLLDDDD")  # Mercosul, antigo


def normalize(raw: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", raw.upper())


def is_valid(plate: str) -> bool:
    return bool(MERCOSUR.match(plate) or OLD_BR.match(plate))


def _coerce(plate: str, layout: str) -> str | None:
    out = []
    for ch, kind in zip(plate, layout):
        if kind == "L":
            ch = ch if ch.isalpha() else _TO_LETTER.get(ch)
        else:
            ch = ch if ch.isdigit() else _TO_DIGIT.get(ch)
        if ch is None:
            return None
        out.append(ch)
    return "".join(out)


def fix_confusions(plate: str) -> str | None:
    """Coage caracteres confundidos pelo OCR ao layout de placa; None se impossível."""
    if len(plate) != 7:
        return None
    for layout in _LAYOUTS:
        fixed = _coerce(plate, layout)
        if fixed and is_valid(fixed):
            return fixed
    return None
