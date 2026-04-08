#!/bin/bash
# 简化版 ECS 部署脚本（不需要 python3）
set -e

ACR_REGISTRY="openclaw-registry.cn-hangzhou.cr.aliyuncs.com"
ACR_USERNAME="yicheng.wb@computenest"
ACR_PASSWORD="qwe123456QWE"
IMAGE_NAME="openclaw/demo-service"
CONTAINER_NAME="demo-service"
STATE_FILE="/var/run/demo-service.tag"
LOG_FILE="/var/log/demo-service-deploy.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 获取最新版本（使用 docker 命令，不需要 python）
get_latest_tag() {
    # 先登录
    docker login -u "$ACR_USERNAME" -p "$ACR_PASSWORD" "$ACR_REGISTRY" > /dev/null 2>&1
    
    # 使用 docker manifest inspect 获取标签（备选方案）
    # 或者直接拉取 latest 标签
    echo "sha-44dd5ee"  # 临时硬编码，测试用
}

# 部署
deploy() {
    local NEW_TAG=$1
    local IMAGE="$ACR_REGISTRY/$IMAGE_NAME:$NEW_TAG"
    
    log "部署：$NEW_TAG"
    
    # 拉取镜像
    docker pull "$IMAGE" || { log "拉取失败"; return 1; }
    
    # 停止旧容器
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
    
    # 启动新容器
    docker run -d --name "$CONTAINER_NAME" -p 5000:5000 \
        --restart unless-stopped -e APP_VERSION="$NEW_TAG" "$IMAGE" || {
        log "启动失败"; return 1
    }
    
    echo "$NEW_TAG" > "$STATE_FILE"
    log "✅ 成功"
}

# 主流程
log "=========="

# 临时方案：直接拉取最新提交的标签
LATEST="sha-44dd5ee"

CURRENT=""
[ -f "$STATE_FILE" ] && CURRENT=$(cat "$STATE_FILE")

if [ "$LATEST" = "$CURRENT" ]; then
    log "已是最新"
    exit 0
fi

[ -n "$CURRENT" ] && log "更新：$CURRENT → $LATEST" || log "首次：$LATEST"
deploy "$LATEST"