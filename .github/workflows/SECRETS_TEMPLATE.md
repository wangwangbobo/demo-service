# GitHub Secrets 配置（已填充）

## 你的配置信息

### ✅ 已自动获取

| Secret | 值 | 来源 |
|--------|-----|------|
| `ACR_REGISTRY` | `registry.cn-hangzhou.aliyuncs.com` | ACR 实例地域 |
| `ALIYUN_REGION` | `cn-hangzhou` | ECS 所在地域 |
| `ECS_INSTANCE_ID` | `i-bp16jiyygbq87h2pdvpp` | 你选择的 ECS |

### ⚠️ 需要手动获取

| Secret | 如何获取 |
|--------|----------|
| `ACR_USERNAME` | 阿里云控制台 → 容器镜像服务 → 访问凭证 → 用户名 |
| `ACR_PASSWORD` | 阿里云控制台 → 容器镜像服务 → 访问凭证 → **固定密码**（不是登录密码！） |
| `ALIYUN_AK_ID` | 阿里云控制台 → RAM 访问控制 → 用户 → 访问密钥 |
| `ALIYUN_AK_SECRET` | 同上，创建时显示（只显示一次！） |

---

## 快速配置步骤

### 1. 获取 ACR 用户名和固定密码

```bash
# 查看当前 CLI 配置的用户信息
aliyun config get
```

或者：
1. 打开 https://cr.console.aliyun.com/
2. 点击左侧 **访问凭证**
3. 记录 **用户名** 和 **固定密码**（如未设置，点击"设置固定密码"）

### 2. 获取阿里云 AK/SK

**方法 A：使用当前 CLI 已配置的 AK**
```bash
# 查看当前使用的 AK（部分隐藏）
aliyun configure show
```

**方法 B：创建新的 RAM 用户（推荐）**
1. 打开 https://ram.console.aliyun.com/
2. 左侧 **身份管理** → **用户** → **创建用户**
3. 登录名称：`github-actions-deploy`
4. 访问方式：勾选 **OpenAPI 调用访问**
5. 点击 **确定**
6. **立即复制保存** AccessKey ID 和 Secret（只显示一次！）

### 3. 配置 RAM 权限

为刚创建的用户授权：
1. 在用户列表点击刚创建的用户
2. 点击 **权限管理** → **新增授权**
3. 选择权限：
   - `AliyunCRFullAccess`（容器镜像服务完全访问）
   - `AliyunECSFullAccess`（ECS 完全访问）
   - 或自定义策略（最小权限）：
```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cr:GetAuthorizationToken",
        "cr:ListInstance"
      ],
      "Resource": "*"
    },
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

### 4. 填写 GitHub Secrets

1. 打开 https://github.com/wangwangbobo/demo-service/settings/secrets/actions
2. 点击 **New repository secret**
3. 逐个添加以下 7 个 Secret：

```
Name: ACR_REGISTRY
Value: registry.cn-hangzhou.aliyuncs.com

Name: ACR_USERNAME
Value: <你的 ACR 用户名>

Name: ACR_PASSWORD
Value: <你的 ACR 固定密码>

Name: ALIYUN_AK_ID
Value: <你的 AccessKey ID>

Name: ALIYUN_AK_SECRET
Value: <你的 AccessKey Secret>

Name: ALIYUN_REGION
Value: cn-hangzhou

Name: ECS_INSTANCE_ID
Value: i-bp16jiyygbq87h2pdvpp
```

---

## 验证配置

添加完 Secrets 后，创建一个空提交触发部署：

```bash
cd /Users/wangbo/.openclaw/workspace/demo-service
git commit --allow-empty -m "Test deployment trigger"
git push
```

然后在 GitHub Actions 查看运行状态：
https://github.com/wangwangbobo/demo-service/actions

---

## 安全提醒

⚠️ **重要安全建议：**

1. **不要分享 AK/SK** - 这是你的云资源访问凭证
2. **使用 RAM 子账号** - 不要用主账号 AK
3. **定期轮换密钥** - 建议每 90 天更换一次
4. **最小权限原则** - 只授予必要的权限
5. **启用 MFA** - 为 RAM 用户开启多因素认证
