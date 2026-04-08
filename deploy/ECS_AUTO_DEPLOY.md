# ECS 自动部署方案（无需 AK）

## 架构

```
GitHub Actions → 推送镜像到 ACR
                    ↓
            ECS cron 任务（每分钟）
                    ↓
            检查 ACR → 拉取 → 部署
```

## 部署步骤

### 1. 在 ECS 上创建部署脚本

```bash
# SSH 到 ECS（通过跳板机或云助手）
sudo mkdir -p /opt/demo-service
sudo vi /opt/demo-service/deploy.sh
```

脚本内容：

```bash
#!/bin/bash
# /opt/demo-service/deploy.sh
set -e

# 配置
ACR_REGISTRY="openclaw-registry.cn-hangzhou.cr.aliyuncs.com"
ACR_USERNAME="yicheng.wb@computenest"
ACR_PASSWORD="qwe123456QWE"
IMAGE_NAME="openclaw/demo-service"
CONTAINER_NAME="demo-service"
STATE_FILE="/var/run/demo-service.tag"
LOG_FILE="/var/log/demo-deploy.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 获取 ACR 最新镜像标签
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
    
    log "开始部署：$NEW_TAG"
    
    docker login -u "$ACR_USERNAME" -p "$ACR_PASSWORD" "$ACR_REGISTRY" > /dev/null 2>&1
    docker pull "$IMAGE" || { log "拉取失败"; return 1; }
    
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
    
    docker run -d --name "$CONTAINER_NAME" -p 5000:5000 \
        --restart unless-stopped -e APP_VERSION="$NEW_TAG" "$IMAGE" || {
        log "启动失败"; return 1
    }
    
    echo "$NEW_TAG" > "$STATE_FILE"
    docker image prune -f > /dev/null 2>&1
    
    log "✅ 部署成功"
}

# 主流程
log "========== 检查部署 =========="
LATEST_TAG=$(get_latest_tag)
[ -z "$LATEST_TAG" ] && { log "无法获取版本"; exit 0; }

CURRENT_TAG=""
[ -f "$STATE_FILE" ] && CURRENT_TAG=$(cat "$STATE_FILE")

if [ "$LATEST_TAG" = "$CURRENT_TAG" ]; then
    log "已是最新版本"
    exit 0
fi

[ -n "$CURRENT_TAG" ] && log "更新：$CURRENT_TAG → $LATEST_TAG" || log "首次部署：$LATEST_TAG"
deploy "$LATEST_TAG"
```

### 2. 设置执行权限

```bash
sudo chmod +x /opt/demo-service/deploy.sh
```

### 3. 添加 cron 任务

```bash
# 编辑 crontab
sudo crontab -e

# 添加一行（每分钟执行）
*/1 * * * * /opt/demo-service/deploy.sh
```

### 4. 验证

```bash
# 手动执行一次
sudo /opt/demo-service/deploy.sh

# 查看日志
tail -f /var/log/demo-deploy.log

# 检查容器
docker ps | grep demo-service
```

## 测试流程

1. **推送新代码到 GitHub**
   ```bash
   git commit --allow-empty -m "Test auto-deploy"
   git push
   ```

2. **等待 CI 完成**（~1 分钟）

3. **等待 ECS 自动部署**（1-2 分钟内）

4. **验证服务**
   ```bash
   curl http://<ECS 内网 IP>:5000/health
   ```

## 优势

✅ **无需 AK** - ECS 直接用 ACR 密码登录  
✅ **无需云助手** - 完全自治  
✅ **支持内网** - ECS 内网访问 ACR  
✅ **简单可靠** - 就一个脚本 + cron  
✅ **自动回滚** - 改脚本支持历史版本

## 监控

```bash
# 查看部署日志
tail -100 /var/log/demo-deploy.log

# 查看当前版本
cat /var/run/demo-service.tag

# 查看容器状态
docker ps | grep demo-service

# 测试服务
curl http://localhost:5000/health
```
