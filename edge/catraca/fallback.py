"""Fallback de OCR via API Claude (multimodal): entra só quando o OCR local
tem confiança baixa ou produz placa inválida. Nunca derruba o loop — qualquer
erro vira None e a leitura é descartada.
"""
import base64
import logging

from catraca import plates

log = logging.getLogger(__name__)

_PROMPT = (
    "A imagem é o recorte de uma placa veicular brasileira (padrão Mercosul "
    "LLLDLDD, ex. ABC1D23, ou antigo LLLDDDD, ex. ABC1234). Responda APENAS os "
    "7 caracteres da placa, sem espaços nem pontuação. Se não houver placa "
    "legível, responda exatamente NONE."
)


class ClaudeOcrFallback:
    def __init__(self, client=None, model: str = "claude-haiku-4-5"):
        self._client = client
        self._model = model

    def _get_client(self):
        if self._client is None:
            import anthropic

            self._client = anthropic.Anthropic()
        return self._client

    def read_plate(self, crop_jpeg: bytes) -> str | None:
        try:
            response = self._get_client().messages.create(
                model=self._model,
                max_tokens=16,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64.standard_b64encode(crop_jpeg).decode("utf-8"),
                            },
                        },
                        {"type": "text", "text": _PROMPT},
                    ],
                }],
            )
        except Exception:
            log.warning("fallback OCR falhou; descartando leitura", exc_info=True)
            return None

        text = next((b.text for b in response.content if b.type == "text"), "")
        plate = plates.normalize(text)
        if plates.is_valid(plate):
            return plate
        return plates.fix_confusions(plate)
