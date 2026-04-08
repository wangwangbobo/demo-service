#!/bin/bash
# ECS 自动部署脚本
# 功能：每分钟检查 ACR 镜像更新，有新版本则自动部署
# 使用方式：crontab -e 添加 */1 * * * * /opt/demo-deploy-check.sh

set -e

# ============ 配置区域 ============
ACR_REGISTRY="openclaw-registry.cn-hangzhou.cr.aliyuncs.com"
ACR_USERNAME="yicheng.wb@computenest"
ACR_PASSWORD="qwe123456QWE"
IMAGE_NAME="openclaw/demo-service"
CONTAINER_NAME="demo-service"
PORT="5000"
STATE_FILE="/var/run/demo-service.tag"
LOG_FILE="/var/log/demo-deploy.log"
# ==================================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 获取 ACR 最新镜像标签
get_latest_tag() {
    # 使用 ACR API 获取最新镜像标签
    curl -s -u "$ACR_USERNAME:$ACR_PASSWORD" \
        "https://$ACR_REGISTRY/v2/$IMAGE_NAME/tags/list" \
        2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    tags = data.get('tags', [])
    # 过滤出 sha 开头的标签
    sha_tags = [t for t in tags if t.startswith('sha')]
    if sha_tags:
        print(sorted(sha_tags)[-1])  # 返回最新的
    else:
        print('')
except:
    print('')
" 2>/dev/null
}

# 部署新版本
deploy() {
    local NEW_TAG=$1
    local IMAGE="$ACR_REGISTRY/$IMAGE_NAME:$NEW_TAG"
    
    log "开始部署新版本：$NEW_TAG"
    
    # 登录 ACR
    docker login -u "$ACR_USERNAME" -p "$ACR_PASSWORD" "$ACR_REGISTRY" > /dev/null 2>&1
    
    # 拉取新镜像
    log "拉取镜像：$IMAGE"
    docker pull "$IMAGE" || {
        log "❌ 拉取镜像失败"
        return 1
    }
    
    # 停止旧容器
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
    
    # 启动新容器
    log "启动容器：$CONTAINER_NAME"
    docker run -d \
        --name "$CONTAINER_NAME" \
        -p $PORT:5000 \
        --restart unless-stopped \
        -e ENVIRONMENT=production \
        -e APP_VERSION="$NEW_TAG" \
        "$IMAGE" || {
        log "❌ 启动容器失败"
        return 1
    }
    
    # 保存当前版本
    echo "$NEW_TAG" > "$STATE_FILE"
    
    # 清理旧镜像
    docker image prune -f > /dev/null 2>&1
    
    log "✅ 部署成功！"
}

# ============ 主流程 ============
log "========== 检查部署 =========="

# 获取最新版本
LATEST_TAG=$(get_latest_tag)
if [ -z "$LATEST_TAG" ]; then
    log "⚠️  无法获取最新版本，跳过"
    exit 0
fi

log "ACR 最新版本：$LATEST_TAG"

# 获取当前版本
if [ -f "$STATE_FILE" ]; then
    CURRENT_TAG=$(cat "$STATE_FILE")
    log "当前运行版本：$CURRENT_TAG"
else
    CURRENT_TAG=""
    log "当前运行版本：无（首次部署）"
fi

# 比较版本
if [ "$LATEST_TAG" = "$CURRENT_TAG" ]; then
    log "✅ 已是最新版本，无需部署"
    exit 0
fi

# 部署新版本
if [ -n "$CURRENT_TAG" ]; then
    log "🔄 发现新版本：$CURRENT_TAG → $LATEST_TAG"
else
    log "🚀 首次部署：$LATEST_TAG"
fi

deploy "$LATEST_TAG"

log "========== 检查完成 =========="
