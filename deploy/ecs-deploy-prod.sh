#!/bin/bash
# ECS 自动部署脚本（生产版 - 使用 ACR API）
# 功能：每分钟检查 ACR 镜像更新，自动部署最新版本
set -e

# ============ 配置区域 ============
ACR_REGISTRY="openclaw-registry.cn-hangzhou.cr.aliyuncs.com"
ACR_USERNAME="yicheng.wb@computenest"
ACR_PASSWORD="qwe123456QWE"
IMAGE_NAME="openclaw/demo-service"
CONTAINER_NAME="demo-service"
STATE_FILE="/var/run/demo-service.tag"
LOG_FILE="/var/log/demo-service-deploy.log"
# ==================================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 获取 ACR token
get_acr_token() {
    local RESPONSE
    RESPONSE=$(curl -s -u "$ACR_USERNAME:$ACR_PASSWORD" \
        "https://$ACR_REGISTRY/auth?service=registry&scope=repository:$IMAGE_NAME:pull" \
        2>/dev/null)
    
    if echo "$RESPONSE" | grep -q '"token"'; then
        echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))" 2>/dev/null
    else
        log "❌ 获取 token 失败：$RESPONSE"
        echo ""
    fi
}

# 获取最新版本标签
get_latest_tag() {
    local TOKEN
    TOKEN=$(get_acr_token)
    
    if [ -z "$TOKEN" ]; then
        log "❌ Token 为空"
        echo ""
        return
    fi
    
    local TAGS_RESPONSE
    TAGS_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
        "https://$ACR_REGISTRY/v2/$IMAGE_NAME/tags/list" \
        2>/dev/null)
    
    if echo "$TAGS_RESPONSE" | grep -q '"tags"'; then
        echo "$TAGS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    tags = data.get('tags', [])
    # 过滤出 sha 开头的标签
    sha_tags = [t for t in tags if t.startswith('sha')]
    if sha_tags:
        # 返回最新的（按字母排序）
        print(sorted(sha_tags)[-1])
    else:
        print('')
except Exception as e:
    print('')
" 2>/dev/null
    else
        log "❌ 获取标签失败：$TAGS_RESPONSE"
        echo ""
    fi
}

# 部署新版本
deploy() {
    local NEW_TAG=$1
    local IMAGE="$ACR_REGISTRY/$IMAGE_NAME:$NEW_TAG"
    
    log "开始部署：$NEW_TAG"
    log "镜像：$IMAGE"
    
    # 登录 ACR
    log "登录 ACR..."
    sudo docker login -u "$ACR_USERNAME" -p "$ACR_PASSWORD" "$ACR_REGISTRY" > /dev/null 2>&1 || {
        log "❌ 登录失败"
        return 1
    }
    
    # 拉取镜像
    log "拉取镜像..."
    sudo docker pull "$IMAGE" || {
        log "❌ 拉取失败"
        return 1
    }
    
    # 停止旧容器
    log "停止旧容器..."
    sudo docker stop "$CONTAINER_NAME" 2>/dev/null || true
    sudo docker rm "$CONTAINER_NAME" 2>/dev/null || true
    
    # 启动新容器
    log "启动新容器..."
    sudo docker run -d \
        --name "$CONTAINER_NAME" \
        -p 5000:5000 \
        --restart unless-stopped \
        -e ENVIRONMENT=production \
        -e APP_VERSION="$NEW_TAG" \
        "$IMAGE" || {
        log "❌ 启动失败"
        return 1
    }
    
    # 保存版本
    echo "$NEW_TAG" | sudo tee "$STATE_FILE" > /dev/null
    
    # 清理旧镜像
    sudo docker image prune -f > /dev/null 2>&1
    
    log "✅ 部署成功！"
    return 0
}

# ============ 主流程 ============
log "=========================================="
log "开始检查部署"
log "=========================================="

# 获取最新版本
LATEST=$(get_latest_tag)

if [ -z "$LATEST" ]; then
    log "❌ 无法获取最新版本，跳过本次检查"
    exit 0
fi

log "✅ ACR 最新版本：$LATEST"

# 获取当前运行版本
CURRENT=""
if [ -f "$STATE_FILE" ]; then
    CURRENT=$(cat "$STATE_FILE")
    log "当前运行版本：$CURRENT"
else
    log "当前运行版本：无（首次部署）"
fi

# 比较版本
if [ "$LATEST" = "$CURRENT" ]; then
    log "✅ 已是最新版本，无需部署"
    exit 0
fi

# 部署新版本
if [ -n "$CURRENT" ]; then
    log "🔄 发现新版本：$CURRENT → $LATEST"
else
    log "🚀 首次部署：$LATEST"
fi

if deploy "$LATEST"; then
    log "=========================================="
    log "部署完成"
    log "=========================================="
    exit 0
else
    log "❌ 部署失败"
    log "=========================================="
    exit 1
fi
