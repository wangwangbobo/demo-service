#!/bin/bash
# ECS 部署脚本（使用 docker 命令，不调用 ACR API）
set -e

ACR_REGISTRY="openclaw-registry.cn-hangzhou.cr.aliyuncs.com"
ACR_USERNAME="yicheng.wb@computenest"
ACR_PASSWORD="qwe123456QWE"
IMAGE_NAME="openclaw/demo-service"
CONTAINER_NAME="demo-service"
STATE_FILE="/var/run/demo-service.tag"
LOG_FILE="/var/log/demo-service-deploy.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"; }

# 获取最新版本（通过 docker 命令）
get_latest_tag() {
    # 登录 ACR
    sudo docker login -u "$ACR_USERNAME" -p "$ACR_PASSWORD" "$ACR_REGISTRY" > /dev/null 2>&1
    
    # 尝试拉取 latest 标签，查看实际版本
    # 或者从 GitHub 获取（无需 ACR API）
    curl -s "https://api.github.com/repos/wangwangbobo/demo-service/commits?per_page=1" 2>/dev/null | \
      python3 -c "import sys,json; d=json.load(sys.stdin); print('sha-'+d[0]['sha'][:7] if d else '')" 2>/dev/null || \
      echo "sha-44dd5ee"
}

deploy() {
    local TAG=$1
    local IMAGE="$ACR_REGISTRY/$IMAGE_NAME:$TAG"
    log "部署：$TAG"
    
    sudo docker pull "$IMAGE" || { log "拉取失败"; return 1; }
    sudo docker stop "$CONTAINER_NAME" 2>/dev/null || true
    sudo docker rm "$CONTAINER_NAME" 2>/dev/null || true
    sudo docker run -d --name "$CONTAINER_NAME" -p 5000:5000 \
        --restart unless-stopped -e APP_VERSION="$TAG" "$IMAGE" || { log "启动失败"; return 1; }
    echo "$TAG" | sudo tee "$STATE_FILE" > /dev/null
    sudo docker image prune -f > /dev/null 2>&1
    log "✅ 成功"
}

log "=========="
LATEST=$(get_latest_tag)
[ -z "$LATEST" ] && LATEST="sha-44dd5ee"

log "版本：$LATEST"
CURRENT=""; [ -f "$STATE_FILE" ] && CURRENT=$(cat "$STATE_FILE")
log "当前：${CURRENT:-无}"
[ "$LATEST" = "$CURRENT" ] && { log "已是最新"; exit 0; }
[ -n "$CURRENT" ] && log "更新：$CURRENT → $LATEST" || log "首次：$LATEST"
deploy "$LATEST"