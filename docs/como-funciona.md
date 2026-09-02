# Como o projeto funciona

Catraca de estacionamento com reconhecimento automático de placas (ANPR —
*Automatic Number Plate Recognition*), rodando num Raspberry Pi 4 com webcam
USB. Uma placa aparece na frente da câmera; o sistema lê os caracteres,
consulta uma lista de autorizados e aciona o hardware: LED verde + 2 beeps
(liberado) ou LED vermelho + beep longo (negado). Tudo que acontece vira um
evento com foto que sobe para um dashboard na nuvem, de onde também se
gerencia quem pode entrar — sem tocar no Pi.

## Visão geral

```
[webcam USB] → captura de frames (OpenCV, 1280x720)
      │
      ▼
[MotionGate] há movimento na cena? ──não──► descarta o frame (economiza CPU)
      │ sim
      ▼
[AlprEngine / fast-alpr] detecta a placa no frame (YOLO) e lê os
      │                  caracteres (OCR ViT), tudo local, em ONNX
      ▼
[plates.py] valida o formato (Mercosul LLLDLDD ou antigo LLLDDDD),
      │     corrige confusões típicas de OCR (0↔O, 1↔I, 5↔S, 8↔B…)
      │     └── se ainda inválido e confiança < 0.85: fallback multimodal
      │         (envia o recorte da placa para um modelo de visão na nuvem)
      ▼
[DecisionEngine] placa está na whitelist (SQLite local)? já foi decidida
      │          nos últimos 10s (cooldown)?
      ▼
[GateSignals / GPIO] verde+2 beeps OU vermelho+beep longo
      │
      ▼
[EventStore] grava o evento (placa, decisão, confiança, foto JPEG) numa
      │      fila local — funciona 100% offline
      ▼
[SyncWorker] a cada 30s: envia eventos pendentes pra nuvem e puxa a
             versão mais recente da whitelist (sincronização bidirecional)
```

## Hardware (GPIO do Raspberry Pi)

| Componente | GPIO | Pino físico | Papel |
|---|---|---|---|
| LED verde | 17 | 11 | catraca liberada |
| LED vermelho | 27 | 13 | acesso negado |
| Buzzer | 22 | 15 | feedback sonoro |
| Botão | 23 | 16 | autorização manual no local |
| GND comum | — | 9/14 | retorno dos LEDs, buzzer e botão |

LEDs com resistor de 330Ω; botão usa o pull-up interno do Pi (fechar para
GND = pressionado). A webcam é uma Logitech C270 numa porta USB.

## O pipeline em detalhe

**1. Gate de movimento (`motion.py`).** Rodar a rede neural em todo frame
desperdiçaria CPU com uma cena parada. O gate reduz o frame pra 160x120 em
tons de cinza, compara com o frame anterior (`absdiff`) e só deixa passar se
mais de 2% dos pixels mudaram. Custo: ~1ms por frame.

**2. Detecção + OCR (`alpr_engine.py`).** Usa a biblioteca fast-alpr com dois
modelos ONNX rodando localmente no Pi (edge computing, sem internet):
um detector YOLO v9 tiny (384px) que encontra o retângulo da placa, e um OCR
baseado em Vision Transformer treinado pra placas sul-americanas. O OCR
devolve a confiança **por caractere**; usamos o mínimo delas como confiança
da leitura — uma placa só é tão confiável quanto seu pior caractere.

**3. Validação e correção (`plates.py`).** A placa lida precisa casar com um
dos dois formatos brasileiros: Mercosul `LLLDLDD` (ex.: BRA2E19) ou antigo
`LLLDDDD` (ex.: ABC1234). OCR confunde caracteres parecidos (0↔O, 1↔I, 2↔Z,
5↔S, 6↔G, 8↔B); quando a leitura não casa com formato nenhum, tentamos as
substituições posição a posição — se a posição exige letra, 0 vira O; se
exige dígito, O vira 0 — e revalidamos.

**4. Fallback multimodal (`fallback.py`, opcional).** Se mesmo corrigida a
leitura for inválida E a confiança do OCR local for < 0.85, o recorte da
placa é enviado (JPEG base64) para um modelo de visão multimodal na nuvem,
que devolve só os 7 caracteres. Arquitetura em cascata: o caminho barato e
rápido (local) resolve a maioria dos casos; o caro e potente só entra nos
difíceis. A resposta também passa pela validação de formato — ninguém entra
sem placa válida.

**5. Decisão (`decision.py`).** Consulta a whitelist num SQLite local e
aplica um cooldown de 10s por placa — um carro parado na frente da câmera
gera UMA decisão, não trinta por segundo.

**6. Sinalização (`signals.py`).** gpiozero aciona os pinos: autorizado =
LED verde 3s + 2 beeps curtos; negado = LED vermelho 3s + 1 beep longo.

**7. Fila de eventos offline-first (`events.py`).** Todo evento (placa,
decisão, confiança, se usou fallback, foto do frame) é gravado localmente
com flag `synced=0`. Se a internet cair, nada se perde: os eventos acumulam
e sobem quando a conexão voltar.

**8. Sincronização (`sync.py`).** Um worker em thread separada roda a cada
30s: (a) envia eventos pendentes pra API na nuvem (HTTPS + API key) e marca
como sincronizados; (b) pergunta "sua whitelist mudou desde a versão N?" —
se mudou, baixa e substitui a cópia local. Assim, cadastrar uma placa no
dashboard libera o carro no Pi em até 30s.

**9. Botão de autorização (`button.py`, opcional).** Cenário real: visitante
é negado, o porteiro reconhece e aperta o botão físico. Se houve negação nos
últimos 30s, a placa negada é cadastrada na nuvem na hora e o LED verde
confirma. Sem janela recente de negação, o botão não faz nada (segurança).

**10. Preview (`preview.py`).** Servidor HTTP embutido (porta 8088) serve o
último frame da câmera e a última decisão numa página que se atualiza
sozinha — é como se "vê" o sistema funcionando, já que a webcam é exclusiva
do serviço.

## A nuvem (`cloud/`)

API FastAPI + SQLite hospedada no Render (free tier), autenticada por
`X-API-Key`:

- `POST /api/events` — o Pi envia evento + foto (multipart)
- `GET /api/whitelist?since=N` — o Pi pergunta se a whitelist mudou
  (resposta versionada; `unchanged` quando não há novidade)
- `POST/DELETE /api/whitelist` — o dashboard gerencia as placas
- `GET /` — dashboard: cards de estatísticas, linha do tempo dos eventos com
  foto, gestão da whitelist e **alerta automático** quando a mesma placa é
  negada 3+ vezes na última hora (possível tentativa de intrusão)

## Confiabilidade

- O app roda como serviço **systemd** (`catraca.service`): sobe sozinho no
  boot, reinicia em até 5s se cair. Sem webcam ou sem rede ele degrada, não
  morre.
- **Offline-first**: decisão é 100% local (whitelist em SQLite); internet só
  é necessária pra sincronizar, nunca pra abrir a catraca.

## Testes

77+ testes automatizados (pytest), escritos antes do código (TDD). O GPIO usa
o *mock pin factory* do gpiozero, então a suíte inteira roda em qualquer
máquina sem hardware; câmera e nuvem são substituídas por fakes nos testes de
unidade, e a integração edge↔cloud tem teste real com o servidor FastAPI
local. Scripts auxiliares: `hw_smoke.py` (valida a fiação pino a pino),
`benchmark_alpr.py` (FPS/latência no Pi) e `eval_dataset.py` (acurácia do OCR
e matriz de confusão de caracteres sobre imagens rotuladas).

## Privacidade (LGPD)

Placa veicular é dado pessoal (vincula-se ao proprietário via Renavam). O
projeto é acadêmico e usa placas impressas/próprias; os eventos guardam o
mínimo necessário e devem ser apagados após a demonstração. Num uso real:
base legal (legítimo interesse do controle de acesso), retenção curta com
expurgo automático, acesso restrito ao dashboard e aviso de coleta no local.
