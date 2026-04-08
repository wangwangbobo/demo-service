# CICD 完整配置清单

## ✅ 已完成

- [x] Demo 项目代码（Flask API）
- [x] Dockerfile
- [x] docker-compose.yml
- [x] GitHub Actions CI workflow（构建 + 推送 ACR）
- [x] GitHub Actions CD workflow（云助手部署到 ECS）
- [x] 本地部署脚本（deploy/cloud-assistant.sh）
- [x] README 文档
- [x] Secrets 配置指南

## 📋 需要你手动配置的内容

### 1. GitHub 仓库创建

```bash
cd /Users/wangbo/.openclaw/workspace/demo-service

# 初始化 Git
git init
git add .
git commit -m "Initial commit: demo-service with CICD"

# 创建 GitHub 仓库（需要先 gh auth login）
gh auth login  # 如果还没认证

# 创建仓库并推送
gh repo create demo-service --public --source=. --push
```

### 2. 阿里云 ACR 配置

```bash
# 登录阿里云 ACR（获取固定密码）
docker login registry.cn-hangzhou.aliyuncs.com

# 记录以下信息用于 GitHub Secrets：
# - Registry: registry.cn-hangzhou.aliyuncs.com
# - Username: 你的阿里云账号
# - Password: 固定密码（不是登录密码）
```

### 3. 阿里云 RAM 配置

```bash
# 创建 RAM 用户（阿里云控制台 → RAM 访问控制）
# 1. 创建用户，勾选 OpenAPI 调用访问
# 2. 保存 AccessKey ID 和 Secret
# 3. 授权策略：ecs:InvokeCommand, ecs:DescribeInvocations
```

### 4. ECS 信息获取

```bash
# 查看 ECS 实例 ID
aliyun ecs DescribeInstances --RegionId cn-hangzhou

# 记录：
# - Region: cn-hangzhou（你的 ECS 地域）
# - Instance ID: i-xxxxxxxxx
```

### 5. GitHub Secrets 配置

进入仓库 → Settings → Secrets and variables → Actions → New repository secret

添加以下 7 个 Secret：

| Secret | 示例值 |
|--------|--------|
| `ACR_REGISTRY` | `registry.cn-hangzhou.aliyuncs.com` |
| `ACR_USERNAME` | `your-aliyun-account` |
| `ACR_PASSWORD` | `your-acr-fixed-password` |
| `ALIYUN_AK_ID` | `LTAI5txxxxxxxxxxxx` |
| `ALIYUN_AK_SECRET` | `xxxxxxxxxxxxxxxxxxxxxxxx` |
| `ALIYUN_REGION` | `cn-hangzhou` |
| `ECS_INSTANCE_ID` | `i-bp1234567890abcdef` |

### 6. 验证部署

```bash
# 推送代码触发 CI/CD
git commit --allow-empty -m "Trigger deployment"
git push

# 查看 GitHub Actions 状态
gh run list --repo wangbo/demo-service

# 查看云助手执行状态
aliyun ecs DescribeInvocations \
  --RegionId cn-hangzhou \
  --CommandName deploy-demo-service
```

## 🔍 故障排查

### CI 失败
- 检查 ACR 密码是否正确（固定密码，非登录密码）
- 检查 ACR 仓库是否存在

### CD 失败
- 检查 AK 权限（ECS 云助手调用权限）
- 检查 ECS Instance ID 是否正确
- 检查 ECS 是否安装云助手插件

### 部署后服务不可访问
- ECS 安全组是否开放 5000 端口
- 容器是否正常启动：`docker ps`
- 查看容器日志：`docker logs demo-service`

## 🎯 下一步

1. **添加测试** - 在 CI 中加入真实的 pytest 测试
2. **多环境部署** - 区分 dev/staging/prod
3. **健康检查** - 添加部署后自动验证
4. **回滚机制** - 保留历史版本，支持一键回滚
5. **监控告警** - 集成阿里云监控
