<div align="center">

```text
 ██████╗ █████╗ ████████╗██████╗  █████╗  ██████╗ █████╗
██╔════╝██╔══██╗╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██╔══██╗
██║     ███████║   ██║   ██████╔╝███████║██║     ███████║
██║     ██╔══██║   ██║   ██╔══██╗██╔══██║██║     ██╔══██║
╚██████╗██║  ██║   ██║   ██║  ██║██║  ██║╚██████╗██║  ██║
 ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
```

# Catraca ANPR — Sistema Embarcado de Leitura de Placas

**Engenharia de Computação · Mauá Institute of Technology**

[![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow?style=flat-square)](.)
[![Ano](https://img.shields.io/badge/Projeto-2026-blue?style=flat-square)](.)
[![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square\&logo=python\&logoColor=white)](.)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi%204-A22846?style=flat-square\&logo=raspberrypi\&logoColor=white)](.)
[![Linux](https://img.shields.io/badge/Linux%20Embarcado-FCC624?style=flat-square\&logo=linux\&logoColor=black)](.)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square\&logo=fastapi\&logoColor=white)](.)
[![ONNX](https://img.shields.io/badge/ONNX-005CED?style=flat-square\&logo=onnx\&logoColor=white)](.)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square\&logo=docker\&logoColor=white)](.)
[![IoT](https://img.shields.io/badge/IoT-Cloud-00C4CC?style=flat-square)](.)

> *"Intelligence at the edge, connectivity in the cloud."*

</div>

---

## 1. ◈ Equipe

<div align="center">

| Nome                               | RA         | Papel             |
| ---------------------------------- | ---------- | ----------------- |
| Arthur Gama Ruiz                   | 23.01445-8 | Desenvolvedor     |
| Enzo Oliveira D'Onofrio            | 23.01561-6 | Desenvolvedor     |
| João Vitor Morimoto Sesma          | 23.01516-0 | Desenvolvedor     |
| Leonardo Souza Olivieri            | 23.01512-8 | Desenvolvedor     |
| Pedro Wilian Palumbo Bevilacqua    | 23.01307-9 | Desenvolvedor     |

**Orientadores**

Prof. Sergio Ribeiro Augusto · Prof. Rodrigo de Marca França

</div>

---

## 2. ◈ Descrição Geral do Projeto

O **Catraca ANPR** é um sistema embarcado para **leitura automática de placas veiculares (Automatic Number Plate Recognition — ANPR)** desenvolvido sobre um **Raspberry Pi 4**.

O projeto simula o funcionamento de uma catraca de estacionamento inteligente. Uma webcam USB captura imagens dos veículos, enquanto um sistema de visão computacional realiza a identificação da placa. A decisão de acesso é tomada localmente a partir de uma **whitelist armazenada em SQLite**.

O sistema foi projetado seguindo uma arquitetura **edge → cloud**, na qual o processamento principal ocorre no Raspberry Pi, reduzindo a dependência da conexão com a internet. Quando a confiança do OCR local é insuficiente, o sistema pode utilizar um **fallback multimodal via API Claude** para tentar recuperar a leitura da placa.

Os eventos de entrada são armazenados localmente e posteriormente sincronizados com um **dashboard hospedado na nuvem**, permitindo o acompanhamento remoto das leituras e o gerenciamento da whitelist.

### Objetivos

* [ ] Capturar imagens de veículos através de uma webcam USB.
* [ ] Detectar e reconhecer placas veiculares brasileiras.
* [ ] Suportar placas no padrão **Mercosul** e no padrão brasileiro anterior.
* [ ] Realizar o processamento OCR localmente no Raspberry Pi.
* [ ] Utilizar fallback multimodal quando a confiança do OCR local for baixa.
* [ ] Validar a placa através de uma whitelist.
* [ ] Controlar LEDs e buzzer para indicar a decisão de acesso.
* [ ] Registrar todos os eventos juntamente com suas respectivas imagens.
* [ ] Permitir funcionamento offline através de uma fila local de eventos.
* [ ] Sincronizar dados entre o Raspberry Pi e a aplicação em nuvem.
* [ ] Disponibilizar um dashboard para visualização dos eventos.
* [ ] Permitir o gerenciamento remoto da whitelist.
* [ ] Avaliar desempenho e precisão do sistema.

### Fluxo principal

```text
                    ┌──────────────────────┐
                    │      Webcam USB      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │     MotionGate       │
                    │ Detecção de movimento│
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │     ALPR Engine      │
                    │     fast-alpr/ONNX   │
                    └──────────┬───────────┘
                               │
                         Confiança alta?
                        ┌──────┴──────┐
                       SIM            NÃO
                        │              │
                        │              ▼
                        │    ┌──────────────────┐
                        │    │ Claude OCR        │
                        │    │ Fallback           │
                        │    └────────┬─────────┘
                        │             │
                        └──────┬──────┘
                               ▼
                    ┌──────────────────────┐
                    │  Decision Engine     │
                    │      + SQLite        │
                    └──────────┬───────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                 AUTORIZADA            NEGADA
                    │                     │
                    ▼                     ▼
              LED VERDE +            LED VERMELHO +
              2 BEEPS                 BEEP LONGO
                    │                     │
                    └──────────┬──────────┘
                               ▼
                    ┌──────────────────────┐
                    │     Event Store      │
                    │   Fila offline       │
                    └──────────┬───────────┘
                               │
                         Sync Worker
                            30s
                               │
                               ▼
                    ┌──────────────────────┐
                    │       Nuvem           │
                    │      FastAPI          │
                    │      Dashboard       │
                    └──────────────────────┘
```

---

## 3. ◈ Arquitetura do Sistema

A arquitetura do Catraca ANPR é dividida em duas camadas principais: **edge**, executada no Raspberry Pi 4, e **cloud**, responsável pelo armazenamento, dashboard e gerenciamento remoto.

### 3.1 Edge — Raspberry Pi 4

O Raspberry Pi concentra as operações que precisam apresentar baixa latência e continuar funcionando mesmo sem conexão com a internet.

```text
┌──────────────────────── Raspberry Pi 4 ─────────────────────────┐
│                                                                  │
│  Webcam                                                          │
│    │                                                             │
│    ▼                                                             │
│ MotionGate ──► AlprEngine ──► DecisionEngine                    │
│                    │                  │                          │
│                    │                  ├── SQLite Whitelist       │
│                    │                  ├── Cooldown               │
│                    │                  └── GateSignals             │
│                    │                                             │
│                    ▼                                             │
│             ClaudeOcrFallback                                    │
│                                                                  │
│  EventStore ◄──────────── Decision                               │
│      │                                                           │
│      ▼                                                           │
│  SyncWorker ─────────────── HTTPS ──────────────► Cloud          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 Cloud — Render

A camada em nuvem disponibiliza uma API REST desenvolvida com **FastAPI**, além da interface de dashboard.

```text
┌────────────────────────── Render ──────────────────────────┐
│                                                            │
│                    ┌─────────────────┐                     │
│                    │     FastAPI     │                     │
│                    └────────┬────────┘                     │
│                             │                              │
│              ┌──────────────┼──────────────┐               │
│              ▼              ▼              ▼               │
│       /api/events    /api/whitelist     /                  │
│              │              │              │               │
│              ▼              ▼              ▼               │
│          Eventos       Whitelist       Dashboard            │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

A comunicação entre o Raspberry Pi e o servidor utiliza **HTTPS** e autenticação através de **API Key**.

---

## 4. ◈ Funcionamento

### 4.1 Captura de imagem

A webcam USB conectada ao Raspberry Pi realiza a captura dos frames.

Para evitar processamento desnecessário, o componente `MotionGate` verifica a existência de movimento antes de encaminhar uma imagem para o sistema de reconhecimento.

A resolução padrão utilizada é:

```text
1280 × 720 pixels
```

A resolução pode ser ajustada através das variáveis de ambiente:

```text
CATRACA_FRAME_WIDTH
CATRACA_FRAME_HEIGHT
```

---

### 4.2 Reconhecimento da placa

O reconhecimento local utiliza o **fast-alpr**, baseado em modelos **ONNX**, permitindo que o processamento seja realizado diretamente no Raspberry Pi.

O sistema trabalha com placas brasileiras:

* Padrão Mercosul;
* Padrão brasileiro anterior.

A confiança retornada pelo reconhecimento é utilizada para determinar se a leitura pode ser aceita diretamente.

Por padrão:

```text
CATRACA_OCR_CONF_THRESHOLD = 0.85
```

Quando a confiança é inferior a esse valor, o sistema pode utilizar o OCR de fallback.

---

### 4.3 OCR multimodal de fallback

Quando habilitado, o sistema pode enviar a imagem para uma API multimodal da **Claude**, utilizando-a como segunda etapa do processo de reconhecimento.

```text
Imagem
   │
   ▼
OCR local
   │
   ├── confiança ≥ 0.85 ──► Resultado
   │
   └── confiança < 0.85 ──► Claude OCR
                                │
                                ▼
                             Resultado
```

Esse mecanismo implementa uma arquitetura de **processamento em cascata**, priorizando o processamento local e utilizando a nuvem apenas quando necessário.

O fallback é controlado por:

```text
CATRACA_FALLBACK_ENABLED=false
```

Quando ativado, é necessária uma `ANTHROPIC_API_KEY`.

---

### 4.4 Decisão de acesso

Após a identificação da placa, o `DecisionEngine` consulta a whitelist local armazenada em **SQLite**.

Existem dois resultados possíveis:

| Situação           | Ação                      |
| ------------------ | ------------------------- |
| Placa autorizada   | LED verde + dois beeps    |
| Placa desconhecida | LED vermelho + beep longo |

O sistema também possui um mecanismo de **cooldown**, evitando que a mesma placa seja processada repetidamente em um intervalo curto.

Valor padrão:

```text
CATRACA_COOLDOWN_S=10
```

---

### 4.5 Autorização através do botão físico

O sistema possui um botão opcional conectado ao **GPIO23**.

Caso uma placa seja negada, o operador pode pressionar o botão para autorizar o veículo localmente.

A autorização:

1. Identifica a última placa negada;
2. Verifica se a decisão ocorreu nos últimos 30 segundos;
3. Adiciona a placa à whitelist;
4. Sincroniza a alteração com a nuvem;
5. Aciona o LED verde como confirmação.

O recurso é habilitado através de:

```text
CATRACA_BUTTON_ENABLED=true
```

---

### 4.6 Funcionamento offline

O Raspberry Pi não depende permanentemente da conexão com a internet.

Os eventos são armazenados localmente através do `EventStore`. Caso a comunicação com o servidor esteja indisponível, os eventos permanecem em uma fila local.

Quando a conexão é restabelecida, o `SyncWorker` realiza o envio dos eventos pendentes.

```text
              INTERNET DISPONÍVEL
                     │
                     ▼
                ┌─────────┐
                │  Cloud  │
                └─────────┘

              INTERNET INDISPONÍVEL
                     │
                     ▼
                ┌─────────┐
                │ SQLite  │
                │  Queue  │
                └────┬────┘
                     │
              conexão restaurada
                     │
                     ▼
                ┌─────────┐
                │  Sync   │
                │ Worker  │
                └────┬────┘
                     │
                     ▼
                ┌─────────┐
                │  Cloud  │
                └─────────┘
```

---

## 5. ◈ Dashboard e Comunicação com a Nuvem

O dashboard permite acompanhar remotamente o funcionamento da catraca.

Entre as informações disponibilizadas estão:

* Placa identificada;
* Data e horário do evento;
* Decisão de acesso;
* Imagem capturada;
* Confiança do reconhecimento;
* Origem do OCR;
* Status de sincronização.

A API disponibiliza os principais endpoints:

| Endpoint         | Método   | Função                       |
| ---------------- | -------- | ---------------------------- |
| `/api/events`    | `GET`    | Consulta eventos registrados |
| `/api/events`    | `POST`   | Envio de novos eventos       |
| `/api/whitelist` | `GET`    | Consulta whitelist           |
| `/api/whitelist` | `POST`   | Adiciona placa autorizada    |
| `/api/whitelist` | `DELETE` | Remove placa autorizada      |
| `/`              | `GET`    | Dashboard                    |

A sincronização da whitelist ocorre de forma **bidirecional a cada 30 segundos**.

```text
              ┌──────────────────────┐
              │      Dashboard       │
              │       Cloud          │
              └──────────┬───────────┘
                         │
                    HTTPS / API
                         │
                         ▼
              ┌──────────────────────┐
              │     Raspberry Pi     │
              │      SQLite          │
              └──────────────────────┘
                         ▲
                         │
                    Sync Worker
                       30s
```

---

## 6. ◈ Hardware

| Qtd | Componente           | Finalidade                            |
| --- | -------------------- | ------------------------------------- |
| 1   | Raspberry Pi 4       | Computador embarcado principal        |
| 1   | Webcam USB           | Captura das imagens dos veículos      |
| 1   | LED verde            | Indicação visual de acesso autorizado |
| 1   | LED vermelho         | Indicação visual de acesso negado     |
| 1   | Buzzer               | Indicação sonora da decisão           |
| 1   | Push-button          | Autorização manual de veículos        |
| 2   | Resistor 330 Ω       | Limitação de corrente dos LEDs        |
| —   | Jumpers e fios       | Conexões elétricas                    |
| —   | Protoboard           | Montagem e prototipagem do circuito   |
| 1   | Fonte de alimentação | Alimentação do Raspberry Pi 4         |

---

## 7. ◈ Materiais, Componentes e Custos

| Qtd | Componente           | Finalidade                                         | Preço Est. (R$) |
| --- | -------------------- | -------------------------------------------------- | --------------: |
| 1   | Raspberry Pi 4       | Processamento embarcado e execução do sistema ANPR |          350,00 |
| 1   | Webcam USB           | Captura das imagens dos veículos                   |          100,00 |
| 1   | LED verde            | Indicação visual de acesso autorizado              |            1,00 |
| 1   | LED vermelho         | Indicação visual de acesso negado                  |            1,00 |
| 1   | Buzzer               | Indicação sonora da decisão                        |            3,00 |
| 1   | Push-button          | Autorização manual de veículos                     |            1,00 |
| 2   | Resistor 330 Ω       | Limitação de corrente dos LEDs                     |            0,50 |
| —   | Jumpers e fios       | Conexões elétricas                                 |           10,00 |
| —   | Protoboard           | Montagem e prototipagem do circuito                |           20,00 |
| 1   | Fonte de alimentação | Alimentação do Raspberry Pi 4                      |           50,00 |

### **Total estimado: R$ 536,50**

> **Observação:** Os valores apresentados são estimativas e podem variar de acordo com o fornecedor, modelo dos componentes e disponibilidade no mercado.

### Custos de software e infraestrutura

| Recurso          | Utilização                    |                    Custo |
| ---------------- | ----------------------------- | -----------------------: |
| Python           | Desenvolvimento do sistema    |                 Gratuito |
| fast-alpr / ONNX | Reconhecimento de placas      |                 Gratuito |
| SQLite           | Banco de dados local          |                 Gratuito |
| FastAPI          | API da aplicação              |                 Gratuito |
| GPIO Zero        | Controle dos GPIOs            |                 Gratuito |
| Render           | Hospedagem da API e dashboard | Conforme plano utilizado |
| Claude API       | OCR multimodal de fallback    |  Conforme consumo da API |

O processamento principal é realizado localmente no Raspberry Pi, reduzindo a necessidade de utilização de serviços externos. A API multimodal é utilizada apenas como **fallback**, quando a confiança do reconhecimento local não atinge o limiar definido.

---

## 8. ◈ Pinos utilizados

| GPIO   | Pino físico | Periférico   | Função              |
| ------ | ----------: | ------------ | ------------------- |
| GPIO17 |          11 | LED verde    | Acesso autorizado   |
| GPIO27 |          13 | LED vermelho | Acesso negado       |
| GPIO22 |          15 | Buzzer       | Feedback sonoro     |
| GPIO23 |          16 | Botão        | Autorização local   |
| GND    |      9 / 14 | Periféricos  | Referência elétrica |

### Ligações

```text
Raspberry Pi 4

GPIO17 ─── 330Ω ───► LED VERDE ───► GND

GPIO27 ─── 330Ω ───► LED VERMELHO ───► GND

GPIO22 ─────────────► BUZZER ─────────► GND

GPIO23 ─────────────► BOTÃO ──────────► GND
                         │
                    Pull-up interno
```

O botão utiliza o **pull-up interno** do Raspberry Pi, não sendo necessário um resistor externo.

A webcam deve ser conectada preferencialmente a uma porta **USB 3.0**.

---

## 9. ◈ Estrutura do Repositório

```text
catraca-anpr/
│
├── edge/
│   ├── app/
│   │   ├── alpr/                  # Motor de reconhecimento de placas
│   │   ├── decision/              # Regras de decisão
│   │   ├── gpio/                  # Controle dos GPIOs
│   │   ├── storage/               # SQLite e fila offline
│   │   ├── sync/                  # Sincronização com a nuvem
│   │   ├── camera/                # Captura da webcam
│   │   └── main.py                # Aplicação principal
│   │
│   ├── tests/                     # Testes automatizados do edge
│   ├── scripts/
│   │   ├── spike_alpr.py          # Testes do ALPR
│   │   ├── benchmark_alpr.py      # Benchmark de desempenho
│   │   ├── eval_dataset.py        # Avaliação do OCR
│   │   ├── hw_smoke.py            # Teste dos componentes físicos
│   │   └── deploy_pi.sh           # Deploy no Raspberry Pi
│   │
│   ├── .env.example               # Exemplo de configuração
│   └── pyproject.toml             # Dependências do projeto
│
├── cloud/
│   ├── app/
│   │   ├── main.py                # Aplicação FastAPI
│   │   ├── api/                   # Endpoints REST
│   │   ├── models/                # Modelos de dados
│   │   └── templates/             # Dashboard
│   │
│   ├── tests/                     # Testes da API
│   ├── requirements.txt           # Dependências
│   └── render.yaml                # Configuração do Render
│
├── docs/
│   └── benchmarks.md              # Resultados dos benchmarks
│
├── images/                        # Imagens da documentação
│   ├── arquitetura.png
│   ├── esquema_eletrico.png
│   ├── prototipo.jpeg
│   └── dashboard.png
│
├── scripts/
│   └── pi_setup.sh                # Configuração inicial do Raspberry Pi
│
├── .gitignore
├── README.md
└── LICENSE
```

---

## 10. ◈ Desenvolvimento Local

O desenvolvimento do sistema pode ser realizado em um computador convencional, sem a necessidade de conexão com o hardware.

### Edge

Entre no diretório:

```bash
cd edge
```

Crie o ambiente virtual:

```bash
uv venv .venv
```

Instale as dependências:

```bash
uv pip install -p .venv -e '.[dev]'
```

Como os GPIOs não estão disponíveis durante o desenvolvimento no computador, o projeto utiliza o **mock pin factory** do `gpiozero`:

```bash
GPIOZERO_PIN_FACTORY=mock .venv/bin/pytest
```

Esse comando executa a suíte de testes do sistema embarcado sem necessidade do Raspberry Pi.

### Desenvolvimento do ALPR

Como a webcam física está disponível somente no Raspberry Pi, o desenvolvimento local pode utilizar imagens previamente gravadas:

```bash
scripts/spike_alpr.py
```

---

## 11. ◈ Desenvolvimento da Nuvem

Entre no diretório:

```bash
cd cloud
```

Crie o ambiente virtual:

```bash
uv venv .venv
```

Instale as dependências:

```bash
uv pip install -p .venv -r requirements.txt
uv pip install -p .venv pytest httpx
```

Execute os testes:

```bash
.venv/bin/python -m pytest
```

Para executar a API localmente:

```bash
API_KEY=dev .venv/bin/uvicorn app.main:app
```

O dashboard estará disponível em:

```text
http://localhost:8000
```

---

## 12. ◈ Configuração

As configurações do sistema utilizam o prefixo:

```text
CATRACA_
```

O arquivo de configuração do Raspberry Pi está localizado em:

```text
/home/pi/catraca/.env
```

### Principais variáveis

| Variável                     | Default | Função                        |
| ---------------------------- | ------- | ----------------------------- |
| `CATRACA_CLOUD_URL`          | vazio   | URL da API na nuvem           |
| `CATRACA_CLOUD_API_KEY`      | —       | Chave de autenticação         |
| `CATRACA_OCR_CONF_THRESHOLD` | `0.85`  | Limiar para fallback          |
| `CATRACA_MIN_DECISION_CONF`  | `0.5`   | Confiança mínima para decisão |
| `CATRACA_FALLBACK_ENABLED`   | `false` | Ativa OCR via Claude          |
| `CATRACA_FRAME_WIDTH`        | `1280`  | Largura da captura            |
| `CATRACA_FRAME_HEIGHT`       | `720`   | Altura da captura             |
| `CATRACA_COOLDOWN_S`         | `10`    | Intervalo entre decisões      |
| `CATRACA_MOTION_THRESHOLD`   | `0.02`  | Sensibilidade do MotionGate   |
| `CATRACA_BUTTON_ENABLED`     | `false` | Ativa botão físico            |
| `CATRACA_PREVIEW_PORT`       | `8088`  | Porta do preview da câmera    |

Quando:

```text
CATRACA_PREVIEW_PORT=0
```

o preview da câmera é desativado.

Caso esteja habilitado, o preview pode ser acessado em:

```text
http://<IP-DO-PI>:8088
```

---

## 13. ◈ Testes e Validação

O projeto possui diferentes níveis de testes.

### Testes de software

```bash
GPIOZERO_PIN_FACTORY=mock .venv/bin/pytest
```

São avaliados componentes como:

* Motor de decisão;
* Whitelist;
* Cooldown;
* EventStore;
* Sincronização;
* Controle dos GPIOs;
* Tratamento de falhas.

### Teste do hardware

Após a instalação no Raspberry Pi:

```bash
scripts/hw_smoke.py
```

Esse teste permite validar individualmente:

* LED verde;
* LED vermelho;
* Buzzer;
* Botão;
* GPIOs utilizados pelo projeto.

---

## 14. ◈ Benchmark

O desempenho do ALPR deve ser avaliado diretamente no Raspberry Pi utilizando diferentes resoluções de captura.

Exemplo:

```bash
~/catraca/venv/bin/python ~/catraca/benchmark_alpr.py 640 480 50
```

O benchmark mede:

* FPS de captura;
* Latência média do ALPR;
* Latência P95;
* Taxa de leituras válidas.

Os resultados são documentados em:

```text
docs/benchmarks.md
```

### Avaliação da acurácia

Para avaliar a capacidade de reconhecimento sobre imagens rotuladas:

```bash
edge/.venv/bin/python scripts/eval_dataset.py fotos/ 200
```

O processo pode ser utilizado para analisar:

* Taxa de reconhecimento;
* Caracteres incorretos;
* Placas não identificadas;
* Confiança do OCR;
* Diferença entre placas Mercosul e padrão antigo.

Também pode ser utilizado o dataset **RodoSol-ALPR**, mediante disponibilidade e autorização para uso acadêmico.

---

## 15. ◈ Deploy

### 15.1 Configuração inicial do Raspberry Pi

A configuração inicial pode ser realizada remotamente através de SSH:

```bash
ssh $PI_HOST 'bash -s' < scripts/pi_setup.sh
```

Após a instalação, recomenda-se executar:

```bash
scripts/hw_smoke.py
```

para verificar as conexões físicas.

---

### 15.2 Deploy do Edge

A atualização do software no Raspberry Pi é realizada através do script:

```bash
PI_HOST=pi@<ip> scripts/deploy_pi.sh
```

O processo realiza:

1. Sincronização dos arquivos através de `rsync`;
2. Instalação/atualização das dependências;
3. Atualização da aplicação;
4. Reinicialização do serviço;
5. Execução do sistema através do `systemd`.

O serviço é denominado:

```text
catraca
```

O serviço é configurado para:

* Iniciar automaticamente com o sistema;
* Reiniciar caso o processo falhe;
* Executar continuamente no Raspberry Pi.

Para acompanhar os logs:

```bash
journalctl -u catraca -f
```

---

### 15.3 Deploy da Cloud

A aplicação da nuvem é hospedada no **Render** utilizando o arquivo:

```text
cloud/render.yaml
```

O Blueprint aponta para o repositório do projeto e configura o serviço FastAPI.

A `API_KEY` é gerada pelo ambiente de produção e posteriormente configurada no `.env` do Raspberry Pi:

```text
CATRACA_CLOUD_API_KEY=<API_KEY>
```

---

## 16. ◈ Privacidade e LGPD

O sistema trabalha com **placas veiculares**, que podem constituir dados pessoais quando associadas a uma pessoa identificável.

Por se tratar de um projeto acadêmico, recomenda-se:

* Utilizar apenas placas próprias, autorizadas ou impressas;
* Evitar registrar veículos de terceiros durante os testes;
* Armazenar somente os dados necessários para a demonstração;
* Não disponibilizar publicamente imagens contendo placas reais;
* Apagar os eventos após a conclusão das demonstrações;
* Não utilizar dados reais em datasets públicos sem verificar suas condições de uso;
* Proteger as credenciais utilizadas para acesso à API.

As chaves de API **não devem ser armazenadas no repositório**.

Utilize arquivos `.env` e mantenha-os no `.gitignore`.

---

## 17. ◈ Resultados e Demonstração

<p align="center">
  <strong>Protótipo físico</strong><br><br>
  <img src="images/prototipo.jpeg" width="700" align="center"/><br>
  <em>Figura 1 — Protótipo da catraca ANPR</em>
</p>

<p align="center">
  <strong>Dashboard</strong><br><br>
  <img src="images/dashboard.png" width="700" align="center"/><br>
  <em>Figura 2 — Dashboard de monitoramento</em>
</p>

<p align="center">
  <strong>Arquitetura do sistema</strong><br><br>
  <img src="images/arquitetura.png" width="700" align="center"/><br>
  <em>Figura 3 — Arquitetura edge → cloud</em>
</p>

### ▶ Vídeo de Apresentação

[Assista ao vídeo de apresentação do projeto](#)

> Substituir o link acima pelo vídeo de apresentação quando disponível.

---

## 18. ◈ Tecnologias Utilizadas

<div align="center">

| Categoria           | Tecnologias                      |
| ------------------- | -------------------------------- |
| Hardware            | Raspberry Pi 4, Webcam USB, GPIO |
| Linguagem           | Python                           |
| ALPR                | fast-alpr, ONNX                  |
| OCR Fallback        | Claude API                       |
| Banco local         | SQLite                           |
| Backend             | FastAPI                          |
| Comunicação         | HTTPS / REST                     |
| Cloud               | Render                           |
| Sistema Operacional | Linux / Raspberry Pi OS          |
| Automação           | systemd, rsync                   |
| Testes              | pytest, gpiozero mock            |
| Ambiente            | uv, Python virtual environment   |

</div>

---

<div align="center">

**Catraca ANPR — Sistema Embarcado de Leitura Automática de Placas**

**Engenharia de Computação · Mauá Institute of Technology · 2026**

[![Python](https://img.shields.io/badge/-Python-3776AB?style=flat-square\&logo=python\&logoColor=white)](.)
[![Raspberry Pi](https://img.shields.io/badge/-Raspberry%20Pi-A22846?style=flat-square\&logo=raspberrypi\&logoColor=white)](.)
[![FastAPI](https://img.shields.io/badge/-FastAPI-009688?style=flat-square\&logo=fastapi\&logoColor=white)](.)
[![ONNX](https://img.shields.io/badge/-ONNX-005CED?style=flat-square\&logo=onnx\&logoColor=white)](.)
[![Linux](https://img.shields.io/badge/-Linux-FCC624?style=flat-square\&logo=linux\&logoColor=black)](.)
[![IoT](https://img.shields.io/badge/-IoT-00C4CC?style=flat-square)](.)

</div>

---

## 19. ◈ Referências Bibliográficas

RASPBERRY PI FOUNDATION. *Raspberry Pi 4 Model B Documentation*. Disponível em: https://www.raspberrypi.com/documentation/computers/raspberry-pi.html.

FAST-ALPR. *Fast Automatic License Plate Recognition*. Disponível em: https://github.com/ankandrew/fast-alpr.

ONNX. *Open Neural Network Exchange*. Disponível em: https://onnx.ai/.

FASTAPI. *FastAPI Documentation*. Disponível em: https://fastapi.tiangolo.com/.

GPIOZERO. *gpiozero Documentation*. Disponível em: https://gpiozero.readthedocs.io/.

ANTHROPIC. *Claude API Documentation*. Disponível em: https://docs.anthropic.com/.

RENDER. *Render Documentation*. Disponível em: https://render.com/docs.

BRASIL. *Lei Geral de Proteção de Dados Pessoais — Lei nº 13.709/2018*. Disponível em: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm.
