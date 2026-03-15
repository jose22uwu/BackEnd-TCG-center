#!/usr/bin/env bash
# Backend setup from scratch. Run from project root or from scripts/:
#   ./scripts/setup-backend.sh
#   bash scripts/setup-backend.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v php >/dev/null 2>&1; then
  echo "Error: PHP not found. Install PHP 8.2+ and try again." >&2
  exit 1
fi

if ! command -v composer >/dev/null 2>&1; then
  echo "Error: Composer not found. Install Composer and try again." >&2
  exit 1
fi

exec php "$SCRIPT_DIR/setup-backend.php"
