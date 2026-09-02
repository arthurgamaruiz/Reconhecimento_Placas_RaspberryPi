# Levantamento de requisitos, tecnologias e pesquisa

## 1. Levantamento de requisitos

### Contexto e problema

Controle de acesso veicular (estacionamento, condomínio, garagem de empresa)
depende de intervenção humana ou de dispositivos por veículo (tag RFID,
controle remoto). A proposta é uma catraca autônoma que identifica o veículo
pela **placa** — que todo carro já tem — usando visão computacional embarcada,
com gestão remota de autorizações.

### Requisitos do trabalho (disciplina)

| # | Requisito da disciplina | Como o projeto atende |
|---|---|---|
| RD1 | Utilizar entrada/saída física (GPIO) | LEDs verde/vermelho, buzzer e botão físico de autorização |
| RD2 | Utilizar o sistema operacional / recursos do Raspberry Pi | Serviço systemd com boot automático e restart; journald para logs; SQLite; venv Python; barramento USB (webcam) |
| RD3 | Conter uma aplicação | Aplicação Python embarcada (pipeline de visão + decisão) e aplicação web (dashboard) |
| RD4 | Ter um componente em nuvem | API FastAPI hospedada no Render com dashboard de eventos e gestão remota da whitelist |

### Requisitos funcionais

| # | Requisito |
|---|---|
| RF1 | Capturar vídeo continuamente pela webcam USB |
| RF2 | Detectar e ler placas nos padrões Mercosul (`LLLDLDD`) e antigo (`LLLDDDD`) |
| RF3 | Autorizar ou negar o acesso consultando uma lista de placas cadastradas (whitelist) |
| RF4 | Sinalizar a decisão fisicamente: LED verde + 2 beeps (autorizada), LED vermelho + beep longo (negada) |
| RF5 | Registrar todo evento (placa, decisão, confiança, foto) e enviá-lo ao dashboard na nuvem |
| RF6 | Permitir cadastro/remoção remota de placas pelo dashboard, refletido no equipamento em até 30 s |
| RF7 | Permitir autorização local: botão físico cadastra a última placa negada (janela de 30 s) |
| RF8 | Alertar no dashboard quando a mesma placa for negada 3+ vezes na última hora |
| RF9 | Exibir em página web o que a câmera está vendo e a última decisão (preview para acompanhamento) |

### Requisitos não funcionais

| # | Requisito |
|---|---|
| RNF1 | Funcionar offline: a decisão não pode depender de internet (whitelist local; eventos em fila até a conexão voltar) |
| RNF2 | Iniciar sozinho no boot e se recuperar de falhas (queda da câmera, queda de rede, crash) sem intervenção |
| RNF3 | Processamento de imagem local (edge), sem enviar vídeo contínuo para a nuvem |
| RNF4 | Não acionar a catraca com leitura de baixa qualidade (piso de confiança do OCR) nem repetir decisão da mesma placa em menos de 10 s (cooldown) |
| RNF5 | Comunicação com a nuvem sobre HTTPS autenticada por chave de API; nenhum segredo versionado no repositório |
| RNF6 | Custo zero de infraestrutura (hardware já disponível + nuvem em tier gratuito) |
| RNF7 | Tratamento de dado pessoal conforme LGPD (placa identifica o proprietário): mínimo necessário, retenção curta, acesso restrito |

### Restrições

- Hardware disponível: Raspberry Pi 4 Model B 8 GB, webcam USB (Logitech
  C270), LEDs, buzzer, botão, protoboard e jumpers — sem servo/cancela física.
- Orçamento zero (nuvem em free tier).
- A rede local pode ser hostil (bloqueio de portas, interceptação TLS), como
  observado na prática — reforçou o RNF1/RNF2.

## 2. Conjunto de tecnologias

| Tecnologia | Papel | Por que foi escolhida |
|---|---|---|
| Raspberry Pi 4 B (8 GB) | Computador de borda | Requisito da disciplina; CPU ARM64 suficiente para inferência de redes leves |
| Raspberry Pi OS (Debian 13) | Sistema operacional | Padrão da plataforma; systemd, journald e apt |
| Python 3.13 | Linguagem do edge e da nuvem | Ecossistema maduro de visão computacional e ML; produtividade |
| OpenCV (headless) | Captura da webcam e manipulação de frames | Padrão de fato; build headless dispensa dependências gráficas |
| fast-alpr | Pipeline ANPR pronto (detecção + OCR) | Combina detector YOLOv9-tiny e OCR ViT treinados para placas sul-americanas; roda em CPU |
| ONNX Runtime | Execução dos modelos | Formato aberto; desempenho em ARM64 sem GPU |
| gpiozero + lgpio | Acesso ao GPIO | API de alto nível; *mock pin factory* permite testar sem hardware |
| SQLite | Persistência local (whitelist, fila de eventos) e da nuvem | Zero administração, arquivo único, transacional |
| FastAPI + Uvicorn | API e dashboard na nuvem | Framework moderno, validação automática, documentação OpenAPI |
| Render (free tier) | Hospedagem da nuvem | Deploy direto do repositório git, HTTPS e variáveis de ambiente gerenciadas, custo zero |
| systemd | Gestão do processo no Pi | Boot automático, restart em falha, logs centralizados (journald) |
| pytest | Testes automatizados | 70+ testes escritos antes do código (TDD); GPIO mockado e HTTP fake |
| rsync + ssh | Deploy no Pi | Sincronização incremental do código a partir da máquina de desenvolvimento |

Alternativas consideradas: Tesseract OCR genérico (descartado — acurácia ruim
em placas sem treinamento específico); OpenALPR (descartado — versão aberta
desatualizada, foco em placas americanas); AWS/GCP para a nuvem (descartado —
complexidade e custo desnecessários para o escopo); RFID/tag (descartado —
exige dispositivo por veículo, e a proposta era visão computacional).

## 3. Pesquisa e interpretação de documentação

Documentação consultada durante o desenvolvimento e o que se extraiu de cada:

- **fast-alpr / fast-plate-ocr (GitHub)** — modelos disponíveis e API de
  predição. Da leitura do código-fonte se interpretou um detalhe não óbvio:
  a confiança do OCR vem **por caractere** (lista), não por placa — adotou-se
  o **mínimo** da lista como confiança da leitura, critério mais conservador.
- **gpiozero (readthedocs)** — conceito de *pin factories*: em máquina de
  desenvolvimento usa-se o factory `mock` (testes sem hardware); no Pi com
  kernel recente o backend correto é `lgpio` (o fallback "nativo" é
  experimental), o que exigiu compilar o pacote com swig.
- **Documentação do OpenCV (VideoCapture)** — semântica de `cap.read()` e a
  constatação de que um handle de câmera não se recupera sozinho quando o
  dispositivo USB cai: motivou a rotina de reabertura automática da câmera.
- **Resolução CONTRAN nº 969/2022 e padrão Mercosul** — formatos válidos de
  placa (`LLLDLDD` novo, `LLLDDDD` antigo), base das expressões regulares de
  validação e do mapa de confusões de OCR (0↔O, 1↔I, 2↔Z, 5↔S, 6↔G, 8↔B).
- **FastAPI (fastapi.tiangolo.com)** — injeção de dependências para
  autenticação por header (`X-API-Key`), upload multipart de arquivos e
  fábrica de aplicação (`create_app`) para testes isolados.
- **Render (docs)** — deploy de serviço web Python a partir de repositório
  público, variáveis de ambiente geradas, comportamento do free tier
  (hibernação após inatividade e disco efêmero — documentados como
  limitações operacionais do projeto).
- **systemd (man systemd.service / systemd.exec)** — unidades de serviço,
  `Restart=on-failure`, `EnvironmentFile` para configuração fora do código e
  `WantedBy=multi-user.target` para subir no boot.
- **Lei 13.709/2018 (LGPD)** — enquadramento da placa como dado pessoal e
  consequências para o projeto (ver seção de privacidade no
  `relatorio-notas.md`).
- **Documentação do Debian/Raspberry Pi OS** — instalação headless,
  `raspi-config`/SSH, `ca-certificates` e diagnóstico de USB (`dmesg`,
  `lsusb`, `v4l2-ctl`), usados na depuração de queda da webcam e de rede.

A pesquisa não ficou só na leitura: vários pontos foram **validados
experimentalmente** (benchmark de latência do ALPR, teste da confiança por
caractere, comportamento da câmera após reset USB, hibernação do Render) e as
conclusões estão registradas em `como-funciona.md` e `relatorio-notas.md`.
