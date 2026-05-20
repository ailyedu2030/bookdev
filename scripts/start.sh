#!/usr/bin/env bash
# =============================================================================
# AI多Agent教材编写系统 - 启动脚本
# =============================================================================
set -euo pipefail

APP_NAME="textbook-writing-system"
APP_DIR="/app"

echo "==> ${APP_NAME} v${APP_VERSION:-1.0.0} 启动中..."

# ---- 环境变量检查 ----
check_env() {
    local missing=0
    local required=(
        "MINIMAX_API_KEY"
        "POSTGRES_HOST"
        "TEMPORAL_HOST"
        "KAFKA_BOOTSTRAP_SERVERS"
    )
    for var in "${required[@]}"; do
        if [ -z "${!var:-}" ] || [[ "${!var}" == your_* ]] || [[ "${!var}" == change_me_* ]]; then
            echo "ERROR: 环境变量 ${var} 未配置或仍为默认值"
            missing=1
        fi
    done
    if [ $missing -eq 1 ]; then
        echo "请从 .env.example 复制 .env 并填入实际值"
        exit 1
    fi
}

# ---- 等待服务就绪 ----
wait_for_service() {
    local host="$1"
    local port="$2"
    local service="$3"
    local max_attempts=30
    local attempt=1

    echo "--> 等待 ${service} 就绪 (${host}:${port})..."
    while ! curl -sf "http://${host}:${port}/" >/dev/null 2>&1; do
        if [ $attempt -ge $max_attempts ]; then
            echo "ERROR: ${service} 在 ${max_attempts}s 内未就绪"
            exit 1
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    echo "--> ${service} 已就绪"
}

wait_for_postgres() {
    local attempts=0
    local max_attempts=30
    echo "--> 等待 PostgreSQL 就绪..."
    while ! python -c "
import psycopg2, os
try:
    conn = psycopg2.connect(
        host=os.environ['POSTGRES_HOST'],
        port=os.environ.get('POSTGRES_PORT', 5432),
        dbname=os.environ.get('POSTGRES_DB', 'textbook'),
        user=os.environ['POSTGRES_USER'],
        password=os.environ['POSTGRES_PASSWORD']
    )
    conn.close()
    print('connected')
except Exception as e:
    exit(1)
" 2>/dev/null; do
        attempts=$((attempts + 1))
        if [ $attempts -ge $max_attempts ]; then
            echo "ERROR: PostgreSQL 在 ${max_attempts}s 内未就绪"
            exit 1
        fi
        sleep 1
    done
    echo "--> PostgreSQL 已就绪"
}

# ---- 数据库迁移 ----
run_migrations() {
    echo "--> 运行数据库迁移..."
    if [ -f "${APP_DIR}/scripts/migrate.sh" ]; then
        bash "${APP_DIR}/scripts/migrate.sh"
    else
        echo "WARN: migrate.sh 不存在, 跳过迁移"
    fi
}

# ---- 主入口 ----
main() {
    check_env

    # 等待依赖服务
    wait_for_postgres
    wait_for_service "${TEMPORAL_HOST}" "${TEMPORAL_PORT:-7233}" "Temporal"
    # Kafka 不使用 HTTP 端口, 用 tcp 探活
    echo "--> 等待 Kafka 就绪..."
    python -c "
import socket, os, time
host = os.environ['KAFKA_BOOTSTRAP_SERVERS'].split(':')[0]
port = int(os.environ['KAFKA_BOOTSTRAP_SERVERS'].split(':')[1])
for i in range(30):
    try:
        s = socket.create_connection((host, port), timeout=2)
        s.close()
        print('connected')
        break
    except Exception:
        time.sleep(1)
else:
    exit(1)
"

    # 运行迁移
    run_migrations

    # 启动 API 服务
    echo "==> 启动 FastAPI 服务 (workers=${API_WORKERS:-4})..."
    exec python -m uvicorn \
        src.main:app \
        --host "${API_HOST:-0.0.0.0}" \
        --port "${API_PORT:-8000}" \
        --workers "${API_WORKERS:-4}" \
        --timeout-keep-alive 60 \
        --limit-concurrency 1000 \
        --backlog 2048 \
        --log-level "${LOG_LEVEL:-info}"
}

main "$@"
