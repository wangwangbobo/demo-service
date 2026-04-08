# 部署目标配置

## 选定的 ECS 实例

| 配置项 | 值 |
|--------|-----|
| **实例 ID** | `i-bp16jiyygbq87h2pdvpp` |
| **地域** | `cn-hangzhou` |
| **可用区** | 待确认 |
| **内网 IP** | 待确认 |
| **状态** | Running |

## ACR 配置

| 配置项 | 值 |
|--------|-----|
| **实例 ID** | `cri-41blvwg0hoj8y5tj` |
| **实例名称** | `openclaw` |
| **Registry** | `registry.cn-hangzhou.aliyuncs.com` |
| **规格** | `Enterprise_Basic` |

## 部署后的访问方式

由于 ECS 无公网 IP（NAT 网络），部署后可通过以下方式访问：

### 方式 1：VPC 内网访问
```bash
# 从同 VPC 的其他 ECS 访问
curl http://<内网IP>:5000/health
```

### 方式 2：云助手查看日志
```bash
aliyun ecs DescribeInvocationResults \
  --RegionId cn-hangzhou \
  --InvokeId <执行 ID>
```

### 方式 3：SSH 跳板机（如有）
```bash
# 通过跳板机访问内网 ECS
ssh -J <跳板机 IP> root@<内网 IP>
docker logs -f demo-service
```

### 方式 4：阿里云控制台
1. 打开 ECS 控制台
2. 找到实例 `i-bp16jiyygbq87h2pdvpp`
3. 点击 **远程连接**
4. 查看容器状态：`docker ps`
5. 查看日志：`docker logs demo-service`

## 验证部署成功

部署后在 GitHub Actions 查看日志，确认：
- ✅ 镜像成功推送到 ACR
- ✅ 云助手命令执行成功
- ✅ ECS 成功拉取镜像
- ✅ 容器正常启动

然后可以通过云助手执行健康检查：

```bash
aliyun ecs InvokeCommand \
  --RegionId cn-hangzhou \
  --Type RunShellScript \
  --CommandContent "curl -s http://localhost:5000/health" \
  --InstanceId.1 i-bp16jiyygbq87h2pdvpp \
  --Name health-check
```
