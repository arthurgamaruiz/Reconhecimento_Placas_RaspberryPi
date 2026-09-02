# Notas para o relatório

Material bruto para o texto final. Preencher os números após rodar os scripts no Pi.

## 1. Requisitos da disciplina × implementação

| Requisito | Onde |
|---|---|
| I/O físico | Webcam USB (entrada), LEDs verde/vermelho + buzzer + botão (saída/entrada) via GPIO |
| Uso do OS | Serviço systemd `catraca` (boot automático, restart on-failure), logs no journald, SQLite local |
| Aplicação | Pipeline de visão computacional + regra de negócio (whitelist, cooldown) em Python |
| Nuvem | API FastAPI + dashboard no Render; eventos sobem, whitelist desce (bidirecional) |

## 2. Benchmark no Pi 4 (preencher — `benchmark_alpr.py`)

| Resolução | Captura (fps) | Latência ALPR média | p95 | Leituras válidas |
|---|---|---|---|---|
| 1280×720 | | | | |
| 640×480 | | | | |

## 3. Avaliação do OCR (preencher — `eval_dataset.py`)

Dataset usado: fotos próprias das placas impressas (n=___) e/ou RodoSol-ALPR
(acesso acadêmico mediante formulário no repositório do dataset).

- Acurácia bruta: ___% · Acurácia após correção de confusões: ___%
- Top confusões de caracteres: ___ (esperado 0↔O, 1↔I, 8↔B, 5↔S)

## 4. Fallback multimodal (arquitetura em cascata)

Quando a confiança do OCR local fica abaixo de 0,85 ou a placa não casa com o
layout, o recorte da placa é enviado a um modelo multimodal na nuvem. Métrica no
dashboard: % de eventos com `used_fallback`. Discussão: custo por chamada
(centavos) × ganho de cobertura; decisão barata na borda dispara inferência cara
na nuvem somente quando necessário.

## 5. Resiliência

- Fila offline: eventos gravados em SQLite com flag `synced`; reenvio automático
  a cada 30s. Teste: derrubar o Wi-Fi, gerar N eventos, religar, conferir chegada.
- Serviço systemd reinicia sozinho em caso de falha (`Restart=on-failure`).

## 6. LGPD

Placa veicular é dado pessoal (identifica o proprietário via consulta). Medidas
adotadas no protótipo: (a) uso exclusivo de placas impressas fictícias e placas
dos próprios autores; (b) retenção mínima — eventos apagados após a demonstração;
(c) acesso ao dashboard protegido por chave; (d) em um produto real: política de
retenção, base legal (legítimo interesse com teste de balanceamento), blur de
placas não autorizadas e criptografia em repouso.

## 7. Limitações conhecidas

- Disco do free tier do Render é efêmero: redeploy zera eventos (aceitável para demo).
- Placas de papel ≠ placas metálicas com reflexo/ângulo/movimento real.
- 2–7 fps de ALPR no Pi 4 (CPU): suficiente para cancela, não para via expressa.
