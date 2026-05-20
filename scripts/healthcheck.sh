#!/usr/bin/env bash
# =============================================================================
# AI多Agent教材编写系统 - 健康检查脚本
# =============================================================================
set -euo pipefail

HC_URL="${HEALTHCHECK_URL:-http://localhost:8000}"

# 检查 API 存活
if ! curl -sf --max-time 10 "${HC_URL}/healthz" >/dev/null 2>&1; then
    echo "FAIL: API 服务无响应"
    exit 1
fi

# 检查就绪状态
READY=$(curl -sf --max-time 10 "${HC_URL}/readyz" 2>/dev/null || echo '{"status":"not_ready"}')
READY_STATUS=$(echo "${READY}" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','not_ready'))" 2>/dev/null || echo "not_ready")

if [ "${READY_STATUS}" != "ready" ] && [ "${READY_STATUS}" != "ok" ]; then
    echo "WARN: API 未完全就绪: status=${READY_STATUS}"
fi

echo "OK: API 健康检查通过"
exit 0
