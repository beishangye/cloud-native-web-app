
# 🐳 云原生 Web 应用容器化 + K8s 部署

> 第二周项目：Docker 容器化 + Kubernetes 部署实践

## 📌 项目简介

本项目是一个 Python Flask Web 应用的容器化与 K8s 部署实践。通过 Docker 多阶段构建优化镜像体积，并在 Minikube 集群中实现 3 副本高可用部署。

## 🎯 核心成果

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 镜像体积 | 500MB | **200MB** | **↓ 60%** |
| QPS (吞吐量) | 254 req/s | **319 req/s** | **↑ 25%** |
| 平均响应时间 | 393ms | **314ms** | **↓ 20%** |

## 🛠️ 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.11 + Flask | Web 应用 |
| Docker (多阶段构建) | 容器化，镜像体积优化 60% |
| Minikube | 本地 K8s 集群 |
| Kubernetes (Deployment/Service/Ingress) | 容器编排，3 副本高可用 |
| Gunicorn | 生产级 WSGI 服务器（替代 Flask 开发服务器） |
| 阿里云 ACR | 私有镜像仓库 |
| GitHub Actions | CI/CD 自动化流水线 |
| 阿里云 ACK | 托管 K8s 集群（生产部署） |

## 📂 项目结构

```
cloud-native-web-app/
├── app/
│   ├── app.py              # Flask 应用
│   ├── Dockerfile          # 多阶段构建
│   └── requirements.txt
├── k8s/
│   ├── deployment.yaml     # 3 副本 Deployment
│   ├── service.yaml        # ClusterIP Service
│   └── ingress.yaml        # Nginx Ingress
├── .github/
│   └── workflows/
│       └── ci-cd.yml       # GitHub Actions CI/CD 流水线
├── .gitignore
└── README.md
```

## 🚀 快速开始

### 1. 构建 Docker 镜像

```bash
cd app
docker build -t my-web-app:v1.1 .
```
![构建成功](docs/images/successful.png)
### 2. 推送到 ACR

```bash
docker tag my-web-app:v1.1 crpi-6dyxb1942h81dqrf.cn-hangzhou.personal.cr.aliyuncs.com/devops-project777/web-app:v1.1
docker push crpi-6dyxb1942h81dqrf.cn-hangzhou.personal.cr.aliyuncs.com/devops-project777/web-app:v1.1
```
![](docs/images/tag-push.png)
### 3. 部署到 K8s

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

### 4. 启用 Ingress 并访问

```bash
minikube addons enable ingress
curl http://$(minikube ip)
```
![](docs/images/curl-test.png)
## 📊 性能测试

```bash
ab -n 1000 -c 100 http://192.168.49.2:80/
```
**测试结果：**
```
Requests per second:    318.94 [#/sec] (mean)
Time per request:       313.543 [ms] (mean)
Failed requests:        0
```
![压力测试](docs/images/press_test.png)

## 🔄 CI/CD 自动化部署（第三周）

本项目通过 **GitHub Actions + 阿里云 ACK 实现完整 CI/CD 流水线。代码推送至 `main` 分支后自动完成：镜像构建 → 推送 ACR → 部署 ACK 托管集群 → 业务可用性验证。

### 流水线架构

```
Git Push main → GitHub Actions → Docker Build → Push 阿里云 ACR → kubectl Deploy → ACK 集群运行 3 副本 → NodePort/Ingress 暴露业务
```

工作流文件：[.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml)

---

### 1. GitHub Actions 流水线执行

push 代码到 `main` 分支后自动触发流水线，全流程耗时约 1 分 40 秒。

![GitHub Actions 流水线概览](docs/images/cicd/06-github-actions-overview.png)

流水线完整步骤全绿通过：代码拉取 → Docker 构建 → 推送 ACR → 安装 kubectl → 配置 kubeconfig → 部署 ACK → 部署校验。

![GitHub Actions 流水线执行详情](docs/images/cicd/05-github-actions-detail.png)

---

### 2. 阿里云 ACK 集群准备

ACK 托管版 Pro 集群 `web-app-cluster`，K8s 版本 v1.36.1-aliyun.1，运行状态正常，共 2 台 Worker 节点。

![阿里云 ACK 集群列表控制台](docs/images/cicd/08-ack-cluster-list.png)

初始阶段 1 台 Worker 节点就绪：

```bash
[user01@master01 ~]$ kubectl get nodes
NAME                              STATUS  ROLES   AGE  VERSION
cn-hangzhou.10.23.88.126         Ready   <none>  15m  v1.36.1-aliyun.1
```
![kubectl get nodes 单节点就绪](docs/images/cicd/01-kubectl-get-nodes-single.png)

扩容后 2 台 Worker 节点就绪，3 个业务 Pod 均 Running：

![扩容后 2 节点 + Pod 实时监控](docs/images/cicd/02-kubectl-pods-w-nodes-expanded.png)

---

### 3. 部署结果验证（ACK 控制台）

CI/CD 自动部署完成后，在 ACK 控制台查看资源状态。

**Deployment 无状态应用**：3/3 副本全部就绪，镜像为 ACR 仓库自动推送版本。

![ACK Deployment 详情](docs/images/cicd/09-ack-deployment-detail.png)

**Pod 容器组**：3 个 web-app Pod 全部 Running、重启次数 0。

![ACK Pod 详情](docs/images/cicd/10-ack-pods-detail.png)

---

### 4. 终端命令行验证

master 节点执行综合查询所有核心资源，状态全部正常：

```bash
kubectl get pods          # 3 业务 Pod 1/1 Running 0
kubectl get deployments  # web-app 3/3 READY
kubectl get svc          # web-app-service ClusterIP 80→5000
kubectl get ingress        # web-app-ingress Nginx → NLB 公网
```

![kubectl 综合验证所有资源](docs/images/cicd/11-kubectl-verify-all.png)

Service Endpoints 正确绑定 3 个后端 Pod IP + 5000 端口，`curl` 公网地址返回业务内容。

![Endpoints + curl 访问验证](docs/images/cicd/04-endpoints-curl-verify.png)

---

### 5. 公网业务访问验证

浏览器公网访问验证业务可用性。NodePort 31386 暴露成功：

![公网访问业务页面（IP1 + NodePort）](docs/images/cicd/03-browser-access-public-ip1.png)

另一公网入口 IP 同样正常返回。业务页面：

![公网访问业务页面（IP2）](docs/images/cicd/07-browser-access-public-ip2.png)

---

### 核心特性总结

| 特性 | 实现方式 |
|------|---------|
| 🔁 自动化触发 | main 分支 push 即触发全流程 |
| 📝 版本可追溯 | 镜像标签使用 `${{ github.sha }}` |
| 🚀 ACK 托管集群 | 2 Worker 节点运行 3 副本业务 |
| ⚖️ 负载均衡 | Service 轮询 3 个后端 Pod |
| 🌐 公网暴露 | NodePort + Ingress (NLB) 双入口 |

## 🤔 踩坑记录

### 1. 镜像拉取失败 (ImagePullBackOff)
- **原因**：ACR 私有仓库未配置 `imagePullSecrets`
- **解决**：创建 Secret 并在 Deployment 中引用

### 2. 健康检查导致 Pod 不断重启
- **原因**：livenessProbe 端口配置错误（3000 vs 5000）
- **解决**：修改端口为 5000，或删除健康检查

### 3. 代理导致镜像拉取超时
- **原因**：Minikube 配置了不可用的代理
- **解决**：移除代理配置，或确保代理地址正确

## 📝 后续规划

- [x] 第三周：CI/CD 流水线（GitHub Actions + ACK 自动化部署）
- [ ] 第四周：监控告警体系（Prometheus + Grafana）


---

⭐ 如果这个项目对你有帮助，欢迎 Star！
