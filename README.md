# Demo Service

简单的 Flask API 服务，用于演示 **GitHub Actions + 阿里云 ACR + ECS 云助手** 完整 CICD 流程。

## 🏗️ 架构

```
GitHub 代码推送
    ↓
GitHub Actions CI
    ↓
构建 Docker 镜像 → 推送到阿里云 ACR
    ↓
GitHub Actions CD
    ↓
调用阿里云云助手 API
    ↓
内网 ECS 拉取镜像并部署
```

## 📁 项目结构

```
demo-service/
├── src/
│   └── app.py              # Flask 应用代码
├── .github/workflows/
│   ├── ci.yml              # CI: 测试 + 构建 + 推送 ACR
│   └── deploy.yml          # CD: 云助手部署到 ECS
├── deploy/
│   └── cloud-assistant.sh  # 本地部署脚本
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 🚀 快速开始

### 本地开发

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行服务
python src/app.py

# 3. 访问服务
curl http://localhost:5000/health

# 4. 运行测试
pip install pytest
pytest tests/ -v
```

### Docker 本地测试

```bash
# 构建
docker build -t demo-service:local .

# 运行
docker run -d -p 5000:5000 --name demo demo-service:local

# 测试
curl http://localhost:5000/api/info

# 停止
docker stop demo && docker rm demo
```

## ⚙️ GitHub Actions 配置

### 1. 创建 ACR 仓库

```bash
# 阿里云容器镜像服务控制台创建个人实例
# 或使用企业版实例
```

### 2. 配置 GitHub Secrets

进入仓库 **Settings → Secrets and variables → Actions**，添加：

| Secret | 说明 | 示例 |
|--------|------|------|
| `ACR_REGISTRY` | ACR 注册地址 | `registry.cn-hangzhou.aliyuncs.com` |
| `ACR_USERNAME` | ACR 用户名 | `your-aliyun-account` |
| `ACR_PASSWORD` | ACR 密码 | `xxx-xxx-xxx` |
| `ALIYUN_AK_ID` | 阿里云 AccessKey ID | `LTAI5t...` |
| `ALIYUN_AK_SECRET` | 阿里云 AccessKey Secret | `xxx-xxx-xxx` |
| `ALIYUN_REGION` | ECS 地域 | `cn-hangzhou` |
| `ECS_INSTANCE_ID` | ECS 实例 ID | `i-bp1234567890` |

### 3. 获取 AccessKey

```bash
# 方法 1: 阿里云控制台 → RAM 访问控制 → 创建用户 → 获取 AK
# 方法 2: 使用已有账号的 AK（不推荐生产环境）
```

### 4. 获取 ECS Instance ID

```bash
# 使用阿里云 CLI
aliyun ecs DescribeInstances --RegionId cn-hangzhou

# 或在 ECS 控制台查看
```

### 5. 配置 RAM 权限

确保 AK 有以下权限：
- `ecs:InvokeCommand` - 云助手调用
- `ecs:DescribeInvocations` - 查看执行状态

## 📊 CI/CD 流程

### CI 流程（ci.yml）

1. **Checkout** - 拉取代码
2. **Test** - 运行测试（当前为占位符）
3. **Build** - 构建 Docker 镜像
4. **Push** - 推送到阿里云 ACR

### CD 流程（deploy.yml）

1. **Trigger** - CI 成功后自动触发
2. **Install Aliyun CLI** - 安装阿里云 CLI
3. **InvokeCommand** - 调用云助手 API
4. **Deploy** - ECS 执行部署脚本

## 🔍 监控与调试

### 查看云助手执行状态

```bash
# 查看执行记录
aliyun ecs DescribeInvocations \
  --RegionId cn-hangzhou \
  --CommandName deploy-demo-service

# 查看具体执行详情
aliyun ecs DescribeInvocationResults \
  --RegionId cn-hangzhou \
  --InvokeId <InvokeId>
```

### 查看 ECS 容器日志

```bash
# SSH 到 ECS（如有跳板机）
docker logs -f demo-service

# 或通过云助手查看输出
aliyun ecs DescribeInvocationResults --InvokeId <id>
```

### GitHub Actions 日志

- 进入仓库 **Actions** 标签
- 查看对应 workflow 运行记录
- 展开各步骤查看详细输出

## 🛠️ 常见问题

### Q: 云助手命令执行失败？
A: 检查 ECS 是否安装云助手插件（云助手客户端）

### Q: Docker 拉取镜像慢？
A: 确保 ECS 和 ACR 在同一地域（内网访问）

### Q: 如何回滚？
A: 修改 workflow 中的 IMAGE_TAG 为历史版本，重新触发部署

## 📝 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 欢迎信息 + 版本信息 |
| `/health` | GET | 健康检查 |
| `/api/info` | GET | 服务详细信息 |

## 🔐 安全建议

1. **使用 RAM 子账号 AK**，不要使用主账号
2. **最小权限原则**，只授予必要权限
3. **定期轮换 AK**
4. **生产环境使用 HTTPS**
5. **敏感信息存入 GitHub Secrets**

## 📄 License

MIT
