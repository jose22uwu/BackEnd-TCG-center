#!/usr/bin/env bash
set -euo pipefail

projectDir="/mnt/e/subasta pokemon TCG/ai model"
venvDir="$projectDir/.venv-wsl"

if [ ! -d "$venvDir" ]; then
  echo "No existe el venv en WSL: $venvDir"
  exit 1
fi

source "$venvDir/bin/activate"

nvidiaLibDirs=""
for libDir in "$venvDir"/lib/python3.12/site-packages/nvidia/*/lib; do
  if [ -d "$libDir" ]; then
    if [ -z "$nvidiaLibDirs" ]; then
      nvidiaLibDirs="$libDir"
    else
      nvidiaLibDirs="$nvidiaLibDirs:$libDir"
    fi
  fi
done

export LD_LIBRARY_PATH="/usr/lib/wsl/lib:${nvidiaLibDirs}:${LD_LIBRARY_PATH:-}"

# In WSL, 127.0.0.1/localhost is the Linux namespace; MySQL runs on the Windows host.
# PHP/Laravel may pass DB_HOST=127.0.0.1 from .env, so force gateway when unset or localhost.
gatewayIp="$(ip route | awk '/default/ {print $3; exit}')"
if [ -n "$gatewayIp" ]; then
  case "${DB_HOST:-}" in
    ""|127.0.0.1|localhost) export DB_HOST="$gatewayIp" ;;
    *) ;;
  esac
fi

mode="${1:-check}"
shift || true

if [ "$mode" = "check" ]; then
  python "$projectDir/check_tf_gpu.py"
elif [ "$mode" = "train" ]; then
  python "$projectDir/train_embedding_model.py"
elif [ "$mode" = "chat" ]; then
  export PYTHONIOENCODING=utf-8
  export LC_ALL=C.UTF-8
  export LANG=C.UTF-8
  python "$projectDir/chatbot.py" "$@"
else
  echo "Modo no valido: $mode"
  echo "Usa: check | train | chat"
  exit 1
fi
