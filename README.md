# Catraca ANPR

Leitor de placas veiculares (Mercosul e padrão antigo BR) em um Raspberry Pi 4
com webcam USB, simulando a catraca de um estacionamento:

- **Placa autorizada** → LED verde + beep duplo (catraca liberada)
- **Placa desconhecida** → LED vermelho + beep longo
- Todos os eventos (com foto) sobem para um **dashboard na nuvem**, que também
  gerencia a whitelist remotamente (sincronização bidirecional a cada 30s)
- OCR local (fast-alpr/ONNX) com **fallback multimodal via API Claude** quando a
  confiança é baixa — arquitetura em cascata edge → cloud

## Arquitetura

```
┌────────────────────── Raspberry Pi 4 (edge) ──────────────────────┐
│ webcam ─► MotionGate ─► AlprEngine (fast-alpr) ─► plates          │
│                                │                     │            │
│                        conf < limiar?          DecisionEngine     │
│                                │               (whitelist SQLite  │
│                        ClaudeOcrFallback        + cooldown)       │
│                                                      │            │
│ EventStore (fila offline) ◄────────────── GateSignals (GPIO)      │
│        │ SyncWorker (30s)                                         │
└────────┼──────────────────────────────────────────────────────────┘
         ▼ HTTPS + X-API-Key
┌─────── nuvem (Render) ────────┐
│ FastAPI: /api/events          │
│          /api/whitelist       │
│          / (dashboard)        │
└───────────────────────────────┘
```

## Hardware

| Componente | GPIO | Pino físico |
|---|---|---|
| LED verde (liberado) | GPIO17 | 11 |
| LED vermelho (negado) | GPIO27 | 13 |
| Buzzer | GPIO22 | 15 |
| Botão "autorizar" (opcional) | GPIO23 | 16 |

LEDs com resistor de 330Ω no ânodo; catodos e (−) do buzzer no GND (pino 9).
Botão entre o pino 16 e GND (pino 14) — sem resistor (pull-up interno).
Webcam USB em porta USB3.

O botão implementa autorização no local: um carro negado nos últimos 30s?
Apertou o botão, a placa entra na whitelist da nuvem e o LED verde confirma.

## Desenvolvimento (WSL/desktop, sem hardware)

```bash
cd edge
uv venv .venv && uv pip install -p .venv -e '.[dev]'
GPIOZERO_PIN_FACTORY=mock .venv/bin/pytest       # suite completa
```

O GPIO usa o mock pin factory do gpiozero fora do Pi; a webcam só existe no Pi,
então o desenvolvimento local usa imagens gravadas (`scripts/spike_alpr.py`).

Nuvem local:

```bash
cd cloud
uv venv .venv && uv pip install -p .venv -r requirements.txt pytest httpx
.venv/bin/python -m pytest                        # testes da API
API_KEY=dev .venv/bin/uvicorn app.main:app        # dashboard em http://localhost:8000
```

## Deploy

**Pi (uma vez):** `ssh $PI_HOST 'bash -s' < scripts/pi_setup.sh`, depois valide a
fiação com `scripts/hw_smoke.py` no Pi.

**Pi (a cada mudança):** `PI_HOST=pi@<ip> scripts/deploy_pi.sh` — rsync + pip
install + restart do serviço systemd `catraca` (sobe no boot, reinicia se cair;
logs: `journalctl -u catraca -f`).

**Nuvem:** Render Blueprint apontando para este repo (`cloud/render.yaml`).
A `API_KEY` é gerada pelo Render; copie-a para o `.env` do Pi.

## Configuração (env, prefixo `CATRACA_`)

Arquivo `/home/pi/catraca/.env` no Pi (ver `edge/.env.example`):

| Variável | Default | Uso |
|---|---|---|
| `CATRACA_CLOUD_URL` | (vazio = offline) | URL do serviço no Render |
| `CATRACA_CLOUD_API_KEY` | — | API key do serviço |
| `CATRACA_OCR_CONF_THRESHOLD` | `0.85` | abaixo disso, tenta o fallback |
| `CATRACA_MIN_DECISION_CONF` | `0.5` | leitura válida abaixo disso não decide (espera frame melhor) |
| `CATRACA_FALLBACK_ENABLED` | `false` | liga o OCR via API Claude (requer `ANTHROPIC_API_KEY`) |
| `CATRACA_FRAME_WIDTH/HEIGHT` | `1280/720` | resolução (calibrar com `scripts/benchmark_alpr.py`) |
| `CATRACA_COOLDOWN_S` | `10` | não re-decide a mesma placa nesse intervalo |
| `CATRACA_MOTION_THRESHOLD` | `0.02` | sensibilidade do gate de movimento |
| `CATRACA_BUTTON_ENABLED` | `false` | liga o botão físico de autorização (GPIO23) |
| `CATRACA_PREVIEW_PORT` | `8088` | preview da câmera + última decisão em `http://<ip-do-pi>:8088` (0 desliga) |

## Benchmark

No Pi, com uma placa impressa na frente da câmera:

```bash
~/catraca/venv/bin/python ~/catraca/benchmark_alpr.py 640 480 50
```

Mede FPS de captura, latência média/p95 do ALPR e taxa de leitura válida —
resultados vão em `docs/benchmarks.md`.

Avaliação de acurácia do OCR (matriz de confusão de caracteres) sobre um
diretório de imagens rotuladas (fotos das placas impressas, ou o dataset
RodoSol-ALPR mediante acesso acadêmico):

```bash
edge/.venv/bin/python scripts/eval_dataset.py fotos/ 200
```

## Privacidade (LGPD)

Placa veicular é dado pessoal. Este projeto é acadêmico: use placas próprias ou
impressas, retenha o mínimo necessário e apague os eventos após a demonstração.
