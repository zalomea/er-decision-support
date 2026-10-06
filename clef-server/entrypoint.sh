#!/bin/bash
set -e

if [ ! -f /models/clef-flash-q4_k_m.gguf ]; then
    echo "Downloading model..."
    /app/download-model.sh
fi

exec /llama.cpp/build/bin/llama-server \
    -m /models/clef-flash-q4_k_m.gguf \
    --host 0.0.0.0 \
    --port 5080 \
    --n-gpu-layers 0 \
    -b 2048 \
    -ub 2048 \
    -t "${LLAMA_THREADS:-10}"
