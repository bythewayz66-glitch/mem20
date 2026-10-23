#!/bin/bash
set -euo pipefail
export MEM20_STORE_PATH=/opt/mem20/bench/store
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
cd /opt/mem20
exec python3 bench/build_index.py
