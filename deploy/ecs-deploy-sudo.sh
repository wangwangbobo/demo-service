#!/bin/bash
# ECS 部署脚本（带 sudo）
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

# 获取最新版本
get_latest_tag() {
    curl -s -u "$ACR_USERNAME:$ACR_PASSWORD" \
        "https://$ACR_REGISTRY/v2/$IMAGE_NAME/tags/list" \
        2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    tags = data.get('tags', [])
    sha_tags = [t for t in tags if t.startswith('sha')]
    if sha_tags:
        print(sorted(sha_tags)[-1])
except:
    pass
" 2>/dev/null
}

# 部署
deploy() {
    local NEW_TAG=$1
    local IMAGE="$ACR_REGISTRY/$IMAGE_NAME:$NEW_TAG"
    
    log "部署：$NEW_TAG"
    
    # 登录（带 sudo）
    sudo docker login -u "$ACR_USERNAME" -p "$ACR_PASSWORD" "$ACR_REGISTRY" > /dev/null 2>&1
    
    # 拉取镜像
    sudo docker pull "$IMAGE" || { log "拉取失败"; return 1; }
    
    # 停止旧容器
    sudo docker stop "$CONTAINER_NAME" 2>/dev/null || true
    sudo docker rm "$CONTAINER_NAME" 2>/dev/null || true
    
    # 启动新容器
    sudo docker run -d --name "$CONTAINER_NAME" -p 5000:5000 \
        --restart unless-stopped -e APP_VERSION="$NEW_TAG" "$IMAGE" || {
        log "启动失败"; return 1
    }
    
    echo "$NEW_TAG" > "$STATE_FILE"
    sudo docker image prune -f > /dev/null 2>&1
    log "✅ 成功"
}

# 主流程
log "=========="
LATEST=$(get_latest_tag)
[ -z "$LATEST" ] && { log "无法获取版本"; exit 0; }

log "ACR 最新版本：$LATEST"

CURRENT=""
[ -f "$STATE_FILE" ] && CURRENT=$(cat "$STATE_FILE")
log "当前版本：${CURRENT:-无}"

[ "$LATEST" = "$CURRENT" ] && { log "已是最新"; exit 0; }

[ -n "$CURRENT" ] && log "更新：$CURRENT → $LATEST" || log "首次：$LATEST"
deploy "$LATEST"