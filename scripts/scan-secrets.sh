#!/usr/bin/env bash
# Linux x86_64, locally or on ubuntu-24.04. Findings are fully redacted.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
scan_dir=$(mktemp -d)
trap 'rm -rf "$scan_dir"' EXIT
if [[ -n "${GITLEAKS_BIN:-}" ]]; then
  scanner="$GITLEAKS_BIN"
else
  archive="$scan_dir/gitleaks.tar.gz"
  curl --fail --silent --show-error --location --retry 3 \
    https://github.com/gitleaks/gitleaks/releases/download/v8.24.3/gitleaks_8.24.3_linux_x64.tar.gz \
    --output "$archive"
  echo "9991e0b2903da4c8f6122b5c3186448b927a5da4deef1fe45271c3793f4ee29c  $archive" | sha256sum --check
  tar -xzf "$archive" -C "$scan_dir" gitleaks
  scanner="$scan_dir/gitleaks"
fi
"$scanner" git --config .gitleaks.toml --redact=100 --no-banner \
  --ignore-gitleaks-allow --log-opts='--all --full-history' .
# Include tracked and untracked, unignored source; omit ignored caches and .git.
python - "$scan_dir/tree" <<'PY'
import shutil
import subprocess
import sys
from pathlib import Path
root = Path(sys.argv[1])
root.mkdir()
for name in subprocess.check_output(
    ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z']
).decode().split('\0'):
    if name:
        source = Path(name)
        if source.is_file():
            target = root / source
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
PY
"$scanner" dir --config .gitleaks.toml --redact=100 --no-banner \
  --ignore-gitleaks-allow "$scan_dir/tree"
