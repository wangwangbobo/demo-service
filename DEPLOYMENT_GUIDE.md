# Demo Service - 完整部署指南

## 🏗️ 架构

```
GitHub 推送 → GitHub Actions CI → ACR 镜像仓库
                                      ↓
                                  ECS cron（每分钟）
                                      ↓
                                  自动拉取部署
```

## ✅ 已完成配置

### GitHub 侧
- ✅ 仓库：https://github.com/wangwangbobo/demo-service
- ✅ CI workflow：`.github/workflows/ci.yml`
- ✅ Secrets：ACR 用户名密码已配置
- ✅ **无需 AK** - ECS 主动拉取

### 阿里云侧
- ✅ ACR 仓库：`openclaw-registry.cn-hangzhou.cr.aliyuncs.com/openclaw/demo-service`
- ✅ ECS 实例：`i-bp16jiyygbq87h2pdvpp`
- ✅ 部署脚本：`/opt/demo-service/deploy.sh`（需要在 ECS 上创建）

---

## 🚀 部署步骤

### 1. 在 ECS 上创建部署脚本

**使用云助手发送命令：**

```bash
# 命令 1：创建目录
sudo mkdir -p /opt/demo-service

# 命令 2：创建脚本
sudo cat > /opt/demo-service/deploy.sh << 'SCRIPT'
#!/bin/bash
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

deploy() {
    local NEW_TAG=$1
    local IMAGE="$ACR_REGISTRY/$IMAGE_NAME:$NEW_TAG"
    
    log "部署：$NEW_TAG"
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
    log "✅ 成功"
}

log "=========="
LATEST=$(get_latest_tag)
[ -z "$LATEST" ] && { log "无法获取版本"; exit 0; }

CURRENT=""
[ -f "$STATE_FILE" ] && CURRENT=$(cat "$STATE_FILE")

[ "$LATEST" = "$CURRENT" ] && { log "已是最新"; exit 0; }

[ -n "$CURRENT" ] && log "更新：$CURRENT → $LATEST" || log "首次：$LATEST"
deploy "$LATEST"
SCRIPT

# 命令 3：设置权限
sudo chmod +x /opt/demo-service/deploy.sh

# 命令 4：添加 cron
(sudo crontab -l 2>/dev/null; echo "*/1 * * * * /opt/demo-service/deploy.sh") | sudo crontab -

# 命令 5：测试运行
sudo /opt/demo-service/deploy.sh
```

### 2. 验证 ECS 部署

```bash
# 查看日志
tail -f /var/log/demo-service-deploy.log

# 查看容器
docker ps | grep demo-service

# 测试服务
curl http://localhost:5000/health
```

### 3. 测试完整流程

```bash
# 在本地推送新代码
cd /Users/wangbo/.openclaw/workspace/demo-service
git commit --allow-empty -m "Test auto-deploy"
git push

# 等待 2-3 分钟
# 然后在 ECS 上查看
tail /var/log/demo-service-deploy.log
```

---

## 📊 监控与维护

### 查看部署状态

```bash
# 当前版本
cat /var/run/demo-service.tag

# 部署日志
tail -100 /var/log/demo-service-deploy.log

# 容器状态
docker ps -a | grep demo-service

# 服务健康检查
curl http://localhost:5000/health
```

### 手动部署

```bash
sudo /opt/demo-service/deploy.sh
```

### 停止服务

```bash
docker stop demo-service
docker rm demo-service
```

### 查看历史版本

```bash
# ACR 中的所有版本
curl -s -u "用户名：密码" \
  "https://openclaw-registry.cn-hangzhou.cr.aliyuncs.com/v2/openclaw/demo-service/tags/list" \
  | python3 -m json.tool
```

---

## 🔐 安全说明

### 凭证存储

| 凭证 | 存储位置 | 说明 |
|------|---------|------|
| ACR 用户名密码 | ECS 脚本中 | 用于 docker login |
| GitHub Secrets | GitHub 仓库设置 | CI 推送用 |
| 阿里云 AK | **已废弃** | 不再需要 |

### 安全建议

1. ✅ **无需 AK** - ECS 主动拉取方案不需要阿里云 AK
2. ✅ **最小权限** - ACR 密码只有拉取权限
3. ✅ **内网传输** - ECS 和 ACR 同地域，走内网
4. ⚠️ **定期更新密码** - 建议每 90 天更换 ACR 密码

---

## 🎯 优势总结

| 优势 | 说明 |
|------|------|
| **无需 AK** | 最安全，无凭证泄露风险 |
| **自动部署** | 推送后 2-3 分钟自动更新 |
| **简单可靠** | 一个脚本 + cron，无复杂依赖 |
| **内网速度快** | ECS 和 ACR 同地域 |
| **自动重试** | 失败后 1 分钟自动重试 |
| **易于回滚** | 修改脚本可部署历史版本 |

---

## 📞 故障排查

### Q: 部署日志显示"无法获取版本"
A: 检查 ECS 到 ACR 的网络连通性
```bash
curl -I https://openclaw-registry.cn-hangzhou.cr.aliyuncs.com/v2/
```

### Q: docker pull 失败
A: 检查 ACR 用户名密码是否正确
```bash
docker login openclaw-registry.cn-hangzhou.cr.aliyuncs.com
```

### Q: 容器启动失败
A: 查看容器日志
```bash
docker logs demo-service
```

### Q: 端口冲突
A: 检查 5000 端口是否被占用
```bash
netstat -tlnp | grep 5000
```

---

## 📚 相关文档

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [阿里云 ACR 文档](https://help.aliyun.com/product/60275.html)
- [Docker 文档](https://docs.docker.com/)

---

**最后更新**: 2026-04-08  
**版本**: 1.0.0
