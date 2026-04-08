# GitHub Secrets 配置指南

## 必需配置

进入仓库 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

### 1. 阿里云容器镜像服务 (ACR)

| Secret Name | Value | 获取方式 |
|-------------|-------|----------|
| `ACR_REGISTRY` | `registry.cn-hangzhou.aliyuncs.com` | 阿里云控制台 → 容器镜像服务 → 默认实例 → 登录 ACR |
| `ACR_USERNAME` | 你的阿里云账号 | 同上，登录命令中的 username |
| `ACR_PASSWORD` | ACR 登录密码 | 同上，登录命令中的 password（固定密码，非登录密码） |

**获取 ACR 密码步骤：**
1. 登录阿里云控制台
2. 进入 **容器镜像服务 ACR**
3. 点击 **默认实例**（或个人实例）
4. 点击 **访问凭证**
5. 设置/查看 **固定密码**（不是登录密码！）

### 2. 阿里云访问密钥 (AK)

| Secret Name | Value | 获取方式 |
|-------------|-------|----------|
| `ALIYUN_AK_ID` | `LTAI5t...` | 阿里云控制台 → RAM 访问控制 → 用户 → 创建用户 → 获取 AK |
| `ALIYUN_AK_SECRET` | `xxx-xxx-xxx` | 同上，创建时显示，只出现一次 |

**创建 RAM 用户步骤：**
1. 登录阿里云控制台
2. 进入 **RAM 访问控制**
3. 左侧 **身份管理** → **用户** → **创建用户**
4. 勾选 **OpenAPI 调用访问**
5. 复制保存 AccessKey ID 和 Secret（只显示一次！）

### 3. ECS 配置

| Secret Name | Value | 获取方式 |
|-------------|-------|----------|
| `ALIYUN_REGION` | `cn-hangzhou` | ECS 所在地域，如杭州、北京等 |
| `ECS_INSTANCE_ID` | `i-bp1234567890abcdef` | ECS 控制台 → 实例列表 → 实例 ID |

**获取 ECS Instance ID：**
```bash
# 方法 1: 阿里云 CLI
aliyun ecs DescribeInstances --RegionId cn-hangzhou

# 方法 2: 控制台
ECS 控制台 → 实例与镜像 → 实例 → 找到你的实例 → 实例 ID
```

### 4. RAM 权限策略

确保 RAM 用户有以下权限：

```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecs:InvokeCommand",
        "ecs:DescribeInvocations",
        "ecs:DescribeInvocationResults"
      ],
      "Resource": "*"
    }
  ]
}
```

## 验证配置

创建测试 workflow：

```yaml
name: Test Secrets
on: workflow_dispatch

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Test ACR
        run: echo "ACR Registry: ${{ secrets.ACR_REGISTRY }}"
      
      - name: Test Aliyun CLI
        uses: aliyun/aliyun-cli-action@v1
        with:
          access-key-id: ${{ secrets.ALIYUN_AK_ID }}
          access-key-secret: ${{ secrets.ALIYUN_AK_SECRET }}
          region-id: ${{ secrets.ALIYUN_REGION }}
      
      - name: List ECS
        run: aliyun ecs DescribeInstances --RegionId ${{ secrets.ALIYUN_REGION }}
```

## 安全提醒

⚠️ **重要：**
- 永远不要提交 AK/SK 到代码仓库
- 定期轮换 AccessKey
- 使用 RAM 子账号，不用主账号
- 遵循最小权限原则
