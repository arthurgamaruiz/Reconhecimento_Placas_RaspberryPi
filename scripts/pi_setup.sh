#!/usr/bin/env bash
# Setup inicial do Pi — rodar UMA vez, do WSL:
#   ssh $PI_HOST 'bash -s' < scripts/pi_setup.sh
set -euo pipefail

sudo apt-get update
sudo apt-get install -y python3-venv libgl1 libglib2.0-0 sqlite3 v4l-utils swig liblgpio-dev
mkdir -p ~/catraca
python3 -m venv ~/catraca/venv
~/catraca/venv/bin/pip install lgpio  # pin factory correto do gpiozero no kernel atual
touch ~/catraca/.env
echo "setup ok — agora rode scripts/deploy_pi.sh do WSL"
