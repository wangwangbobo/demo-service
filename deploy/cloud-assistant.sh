#!/bin/bash
# 云助手部署脚本（本地测试用）
# 在 ECS 上手动执行的版本

set -e

# 配置变量
ACR_REGISTRY="${ACR_REGISTRY:-registry.cn-hangzhou.aliyuncs.com}"
ACR_USERNAME="${ACR_USERNAME:-}"
ACR_PASSWORD="${ACR_PASSWORD:-}"
IMAGE_NAME="your-namespace/demo-service"
IMAGE_TAG="${IMAGE_TAG:-latest}"
CONTAINER_NAME="demo-service"

IMAGE="${ACR_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "========================================="
echo "Deploying Demo Service"
echo "========================================="
echo "Registry: $ACR_REGISTRY"
echo "Image: $IMAGE"
echo "Container: $CONTAINER_NAME"
echo "========================================="

# 1. 登录 ACR
echo "[1/5] Logging in to ACR..."
docker login -u "$ACR_USERNAME" -p "$ACR_PASSWORD" "$ACR_REGISTRY"

# 2. 拉取镜像
echo "[2/5] Pulling image..."
docker pull "$IMAGE"

# 3. 停止旧容器
echo "[3/5] Stopping old container..."
docker stop "$CONTAINER_NAME" 2>/dev/null || true
docker rm "$CONTAINER_NAME" 2>/dev/null || true

# 4. 启动新容器
echo "[4/5] Starting new container..."
docker run -d \
  --name "$CONTAINER_NAME" \
  -p 5000:5000 \
  --restart unless-stopped \
  -e ENVIRONMENT=production \
  -e APP_VERSION="$IMAGE_TAG" \
  "$IMAGE"

# 5. 清理
echo "[5/5] Cleaning up old images..."
docker image prune -f

echo "========================================="
echo "✅ Deployment completed!"
echo "========================================="
echo "Service URL: http://localhost:5000"
echo "Health check: http://localhost:5000/health"
echo ""
echo "Logs: docker logs -f $CONTAINER_NAME"
echo "Stop: docker stop $CONTAINER_NAME"
