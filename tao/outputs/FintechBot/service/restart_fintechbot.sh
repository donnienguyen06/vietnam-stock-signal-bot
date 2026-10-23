#!/bin/zsh
set -euo pipefail
PROJECT="/Users/nguyenchitinh/Documents/Codex/2026-09-10/tao/outputs/FintechBot"
mkdir -p "$PROJECT/logs"
# Never terminate an unrelated service merely because it owns port 8010.
for pid in $(lsof -tiTCP:8010 -sTCP:LISTEN 2>/dev/null || true); do
  proc_cwd=$(lsof -a -p "$pid" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p')
  proc_cmd=$(ps -p "$pid" -o command=)
  if [[ "$proc_cwd" != "$PROJECT" || "$proc_cmd" != *run.py* ]]; then
    echo "Cổng 8010 do tiến trình khác giữ (PID $pid); hãy kiểm tra trước khi dừng."
    exit 1
  fi
  kill -TERM "$pid"
done
for attempt in {1..15}; do
  if ! lsof -tiTCP:8010 -sTCP:LISTEN >/dev/null 2>&1; then break; fi
  sleep 1
done
if lsof -tiTCP:8010 -sTCP:LISTEN >/dev/null 2>&1; then
  echo 'Bản cũ chưa dừng; chưa khởi động thêm bản mới.'
  exit 1
fi
nohup "$PROJECT/.venv/bin/python" "$PROJECT/run.py" >> "$PROJECT/logs/fintechbot.out.log" 2>> "$PROJECT/logs/fintechbot.error.log" < /dev/null &
for attempt in {1..15}; do
  if curl -fsS --max-time 2 http://127.0.0.1:8010/healthz >/dev/null; then
    echo 'Fintech Bot sẵn sàng tại http://127.0.0.1:8010'
    exit 0
  fi
  sleep 1
done
echo 'Chưa xác nhận khởi động thành công. Kiểm tra logs/fintechbot.error.log.'
exit 1
