#!/usr/bin/env bash
# =============================================================================
# AI多Agent教材编写系统 - 部署脚本
# 用法: ./scripts/deploy.sh [staging|production] [api|frontend|all]
# =============================================================================

set -euo pipefail

# ---- 配置 ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"
ENVIRONMENT="${1:-staging}"
SERVICE="${2:-all}"
COMPOSE_FILE="docker-compose.prod.yml"
IMAGE_PREFIX="${REGISTRY:-ghcr.io}/textbook-system"

# ---- 颜色 ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

success() {
    echo -e "${GREEN}✅ $*${NC}"
}

warn() {
    echo -e "${YELLOW}⚠️  $*${NC}"
}

error() {
    echo -e "${RED}❌ $*${NC}" >&2
}

# ---- 环境检查 ----
check_env() {
    log "检查环境..."

    if [ ! -f "${PROJECT_DIR}/.env" ]; then
        warn ".env 文件不存在，尝试从 .env.example 创建"
        if [ -f "${PROJECT_DIR}/.env.example" ]; then
            cp "${PROJECT_DIR}/.env.example" "${PROJECT_DIR}/.env"
            warn "请编辑 ${PROJECT_DIR}/.env 填入实际值"
        else
            error ".env.example 也不存在"
            exit 1
        fi
    fi

    if ! command -v docker &> /dev/null; then
        error "Docker 未安装"
        exit 1
    fi

    if ! docker compose version &> /dev/null; then
        error "Docker Compose v2 未安装"
        exit 1
    fi

    success "环境检查通过"
}

# ---- 备份 ----
backup() {
    local backup_dir="${PROJECT_DIR}/backups"
    mkdir -p "${backup_dir}"

    log "创建备份..."

    local timestamp=$(date +%Y%m%d-%H%M%S)
    local backup_file="${backup_dir}/backup-${ENVIRONMENT}-${timestamp}.tar.gz"

    tar -czf "${backup_file}" \
        -C "${PROJECT_DIR}" \
        --exclude='node_modules' \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.pytest_cache' \
        --exclude='backups' \
        --exclude='*.log' \
        . 2>/dev/null || true

    if [ -f "${backup_file}" ]; then
        success "备份已创建: ${backup_file}"
    fi

    # PostgreSQL 备份 (如果存在)
    if docker ps --format '{{.Names}}' | grep -q "textbook-postgres"; then
        log "备份 PostgreSQL..."
        docker exec textbook-postgres pg_dump -U textbook textbook > "${backup_dir}/postgres-${timestamp}.sql" 2>/dev/null || true
        success "PostgreSQL 备份已创建"
    fi
}

# ---- 拉取最新代码 ----
pull_code() {
    log "拉取最新代码..."

    cd "${PROJECT_DIR}"

    if [ -d ".git" ]; then
        git fetch origin
        git reset --hard "origin/${GIT_BRANCH:-main}"
        success "代码已更新"
    else
        warn "非 Git 仓库，跳过代码拉取"
    fi
}

# ---- 构建镜像 ----
build_images() {
    log "构建 Docker 镜像..."

    cd "${PROJECT_DIR}"

    case "${SERVICE}" in
        api)
            docker build \
                --platform linux/amd64 \
                -f Dockerfile \
                -t "${IMAGE_PREFIX}/api:latest" \
                --build-arg BUILDKIT_INLINE_CACHE=1 \
                .
            success "API 镜像构建完成"
            ;;
        frontend)
            docker build \
                --platform linux/amd64 \
                -f Dockerfile.frontend \
                -t "${IMAGE_PREFIX}/frontend:latest" \
                --build-arg BUILDKIT_INLINE_CACHE=1 \
                .
            success "Frontend 镜像构建完成"
            ;;
        all)
            docker build \
                --platform linux/amd64 \
                -f Dockerfile \
                -t "${IMAGE_PREFIX}/api:latest" \
                --build-arg BUILDKIT_INLINE_CACHE=1 \
                .

            docker build \
                --platform linux/amd64 \
                -f Dockerfile.frontend \
                -t "${IMAGE_PREFIX}/frontend:latest" \
                --build-arg BUILDKIT_INLINE_CACHE=1 \
                .
            success "所有镜像构建完成"
            ;;
        *)
            error "未知服务: ${SERVICE}"
            exit 1
            ;;
    esac
}

# ---- 推送镜像 ----
push_images() {
    log "推送镜像到 registry..."

    if [ -z "${REGISTRY:-}" ]; then
        warn "REGISTRY 未设置，跳过镜像推送"
        return
    fi

    echo "${REGISTRY_TOKEN:-}" | docker login "${REGISTRY}" -u "${REGISTRY_USER:-${USER}}" --password-stdin 2>/dev/null || true

    case "${SERVICE}" in
        api|all)
            docker push "${IMAGE_PREFIX}/api:latest" || warn "API 镜像推送失败"
            ;;
    esac

    case "${SERVICE}" in
        frontend|all)
            docker push "${IMAGE_PREFIX}/frontend:latest" || warn "Frontend 镜像推送失败"
            ;;
    esac

    success "镜像推送完成"
}

# ---- 运行数据库迁移 ----
run_migrations() {
    log "运行数据库迁移..."

    cd "${PROJECT_DIR}"

    if docker compose -f "${COMPOSE_FILE}" ps textbook-api | grep -q "Up"; then
        docker compose -f "${COMPOSE_FILE}" exec -T textbook-api /app/scripts/migrate.sh
        success "迁移完成"
    else
        warn "API 服务未运行，跳过迁移"
    fi
}

# ---- 重启服务 ----
restart_services() {
    log "重启 ${SERVICE} 服务..."

    cd "${PROJECT_DIR}"

    case "${SERVICE}" in
        api)
            docker compose -f "${COMPOSE_FILE}" up -d --no-deps textbook-api textbook-worker
            ;;
        frontend)
            docker compose -f "${COMPOSE_FILE}" up -d textbook-frontend
            ;;
        all)
            docker compose -f "${COMPOSE_FILE}" up -d
            ;;
    esac

    success "服务已重启"
}

# ---- 健康检查 ----
health_check() {
    log "等待服务健康..."

    local max_attempts=30
    local attempt=1
    local api_url="${API_URL:-http://localhost/healthz}"

    while [ $attempt -le $max_attempts ]; do
        if curl -sf "${api_url}" > /dev/null 2>&1; then
            success "健康检查通过"
            return 0
        fi

        echo -n "."
        attempt=$((attempt + 1))
        sleep 2
    done

    echo ""
    error "健康检查失败"
    return 1
}

# ---- 查看状态 ----
show_status() {
    log "${ENVIRONMENT} 服务状态:"

    cd "${PROJECT_DIR}"
    docker compose -f "${COMPOSE_FILE}" ps
}

# ---- 清理 ----
cleanup() {
    log "清理旧镜像和缓存..."

    cd "${PROJECT_DIR}"

    docker system prune -f --filter "until=24h" 2>/dev/null || true
    docker image prune -f 2>/dev/null || true

    success "清理完成"
}

# ---- 主流程 ----
main() {
    log "=========================================="
    log "  AI多Agent教材编写系统 - 部署脚本"
    log "  环境: ${ENVIRONMENT}"
    log "  服务: ${SERVICE}"
    log "=========================================="

    check_env

    case "${ENVIRONMENT}" in
        staging|production)
            export GIT_BRANCH="${ENVIRONMENT}"
            ;;
        *)
            error "未知环境: ${ENVIRONMENT}"
            echo "用法: $0 [staging|production] [api|frontend|all]"
            exit 1
            ;;
    esac

    backup
    pull_code
    build_images
    push_images
    run_migrations
    restart_services

    if health_check; then
        success "部署成功!"
    else
        error "部署完成但健康检查失败，请手动检查"
    fi

    show_status
    cleanup

    log "=========================================="
    log "  部署完成!"
    log "=========================================="
}

# ---- 单独迁移 ----
migrate_only() {
    log "仅运行数据库迁移..."
    check_env
    run_migrations
}

# ---- 单独回滚 ----
rollback() {
    local backup_file="${1:-}"

    if [ -z "${backup_file}" ]; then
        ls -lt "${PROJECT_DIR}/backups/" | head -5
        echo ""
        read -p "请选择要恢复的备份文件: " backup_file
    fi

    if [ ! -f "${backup_file}" ]; then
        error "备份文件不存在: ${backup_file}"
        exit 1
    fi

    log "从备份恢复: ${backup_file}"

    cd "${PROJECT_DIR}"
    docker compose -f "${COMPOSE_FILE}" down

    tar -xzf "${backup_file}" -C "${PROJECT_DIR}"

    success "恢复完成，请手动启动服务"
}

# ---- 帮助 ----
usage() {
    cat << EOF
用法: $0 <命令> [选项]

命令:
    deploy [env] [service]    部署服务
    migrate                   仅运行迁移
    rollback [file]           回滚到指定备份
    status                    查看服务状态
    logs [service]            查看服务日志
    backup                    创建备份
    help                      显示帮助

环境:
    staging                   部署到 staging 环境
    production                部署到 production 环境

服务:
    api                       仅部署 API
    frontend                  仅部署 Frontend
    all                       部署所有服务

示例:
    $0 deploy staging api        # 部署 staging 环境的 API
    $0 deploy production all    # 部署 production 环境的所有服务
    $0 migrate                  # 运行迁移
    $0 rollback                 # 列出可用的备份
    $0 status                   # 查看服务状态

EOF
}

# ---- 命令路由 ----
case "${1:-deploy}" in
    deploy)
        main
        ;;
    migrate)
        migrate_only
        ;;
    rollback)
        rollback "${2:-}"
        ;;
    status)
        cd "${PROJECT_DIR}" && docker compose -f "${COMPOSE_FILE}" ps
        ;;
    logs)
        cd "${PROJECT_DIR}" && docker compose -f "${COMPOSE_FILE}" logs -f --tail=100 "${2:-}"
        ;;
    backup)
        check_env
        backup
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        error "未知命令: ${1}"
        usage
        exit 1
        ;;
esac
