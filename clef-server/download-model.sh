#!/bin/bash
set -e

mkdir -p /models

python3 - <<'PY'
from huggingface_hub import snapshot_download
path = snapshot_download(
    'ggml-org/Clef-Flash-GGUF',
    revision='4a7a08c09bc63baf043b62b5ba89dd67a0357d95',
    allow_patterns=['*Q4_K_M*'],
)
print(f'Model downloaded to: {path}')
import shutil, glob
for f in glob.glob(path + '/**/*.gguf', recursive=True):
    shutil.copy(f, '/models/clef-flash-q4_k_m.gguf')
    print(f'Copied: {f}')
PY
