#!/usr/bin/env bash
set -euo pipefail

echo "== Charm-crypto install script for WSL/Ubuntu =="
echo
echo "This script will:"
echo " - install required system packages (build tools, dev headers)"
echo " - create a Python virtualenv named .venv_charm in the repo directory"
echo " - activate the venv and install charm-crypto into it"
echo
echo "Run this script from inside WSL in the project directory. Example:" 
echo "  cd /mnt/d/OneDrive/Documents/cypto_proj && bash scripts/install_charm_wsl.sh"

sudo apt update
sudo apt install -y build-essential python3-dev libgmp-dev libssl-dev libffi-dev pkg-config git

PYTHON=python3
${PYTHON} -m pip install --upgrade pip setuptools wheel

VENV_DIR=.venv_charm
if [ -d "$VENV_DIR" ]; then
  echo "Virtualenv $VENV_DIR already exists. Reusing it."
else
  echo "Creating virtualenv $VENV_DIR"
  ${PYTHON} -m venv "$VENV_DIR"
fi

echo "Activating virtualenv and installing charm-crypto..."
. "$VENV_DIR/bin/activate"
pip install --upgrade pip

echo "Installing charm-crypto via pip..."
pip install charm-crypto

echo
echo "Installation finished." 
echo "To use the new environment run:"
echo "  . $VENV_DIR/bin/activate"
echo "Then run your tests or start the server with USE_CHARM=1 set in the same shell."

exit 0
