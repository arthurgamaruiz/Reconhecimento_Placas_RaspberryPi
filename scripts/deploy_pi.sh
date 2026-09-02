#!/usr/bin/env bash
# Deploy do edge para o Pi e restart do serviço.
#   PI_HOST=pi@<ip> scripts/deploy_pi.sh   (default: pi@raspberrypi.local)
set -euo pipefail
cd "$(dirname "$0")/.."

PI="${PI_HOST:-pi@raspberrypi.local}"

rsync -az --delete \
  --exclude .venv --exclude __pycache__ --exclude '*.db' --exclude '*.egg-info' \
  edge/ "$PI":~/catraca/edge/
rsync -az scripts/hw_smoke.py scripts/benchmark_alpr.py scripts/eval_dataset.py "$PI":~/catraca/

ssh "$PI" '
  set -e
  ~/catraca/venv/bin/pip install -q -e ~/catraca/edge
  sudo cp ~/catraca/edge/systemd/catraca.service /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable catraca
  sudo systemctl restart catraca
  sleep 2
  systemctl --no-pager -l status catraca | head -15
'
