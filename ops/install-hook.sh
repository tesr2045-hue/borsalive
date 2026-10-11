#!/usr/bin/env bash
# ~/.bashrc başına (etkileşim korumasından ÖNCE) tek satırlık, sessiz, arka plan ensure-up kancası ekler (idempotent).
# Ajan kabukları `bash -ilc` ile başlatılır → ~/.profile → ~/.bashrc okunur → kanca çalışır.
RC=$HOME/.bashrc
MARK='# >>> bist-analiz ensure-up >>>'
if grep -qF "$MARK" "$RC" 2>/dev/null; then [ "${1:-}" = "--quiet" ] || echo "kanca zaten var: $RC"; exit 0; fi
tmp=$(mktemp)
{
  echo "$MARK"
  echo '[ -x /workspace/bist-analiz/ops/ensure-up.sh ] && ( ENSURE_TRIGGER=bashrc setsid /workspace/bist-analiz/ops/ensure-up.sh </dev/null >/dev/null 2>&1 & ) 2>/dev/null'
  echo '# <<< bist-analiz ensure-up <<<'
  cat "$RC" 2>/dev/null
} > "$tmp" && cat "$tmp" > "$RC" && rm -f "$tmp"
[ "${1:-}" = "--quiet" ] || echo "kanca eklendi: $RC"
