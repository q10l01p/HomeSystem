---
title: 华为云部署指南
id: DOC-TBD
type: deployment
created: 2025-11-29
updated: 2025-11-29
owner: community
modules: [deploy]
upstream: []
status: draft
superseded_by: null
deprecated_reason: null
---

# HomeSystem 华为云部署指南

本指南介绍如何在华为云 ECS 上部署 HomeSystem，使用 MinerU API 进行 OCR，硅基流动作为 LLM 服务。

## 前置要求

- 华为云 ECS 实例（推荐 2核4G 以上）
- Docker 20.10+ 和 Docker Compose 2.0+
- MinerU API Key：https://mineru.net/apiManage/docs
- 硅基流动 API Key：https://siliconflow.cn

## 快速部署步骤

### 1. 准备服务器

```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh
sudo systemctl enable docker
sudo systemctl start docker

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. 克隆项目

```bash
git clone https://github.com/yangtao121/homesystem.git
cd homesystem
```

### 3. 配置环境变量

```bash
cp .env.example .env
vim .env
```

修改以下关键配置：

```env
# 数据库密码
DB_PASSWORD=your_secure_password_here

# LLM API - 硅基流动
SILICONFLOW_API_KEY=sk-your_siliconflow_api_key

# OCR 配置 - MinerU API
MINERU_API_KEY=your_mineru_api_key_here
```

### 4. 启动服务

```bash
cd deploy

# 修改 docker-compose.yml 中的配置
vim docker-compose.yml
# 设置 MINERU_API_KEY
# 设置 SILICONFLOW_API_KEY

# 启动所有服务
docker compose up -d

# 查看状态
docker compose ps
```

### 5. 配置安全组

在华为云控制台配置安全组，开放以下端口：

| 端口 | 服务 | 说明 |
|------|------|------|
| 5002 | Web 应用 | 必须开放 |
| 15432 | PostgreSQL | 可选，仅内网访问 |
| 16379 | Redis | 可选，仅内网访问 |
| 5001 | OCR 服务 | 可选，仅内网访问 |

### 6. 验证部署

```bash
# 检查服务健康状态
curl http://localhost:5002/api/health
curl http://localhost:5001/api/health

# 查看日志
docker compose logs -f paper-analysis
```

### 7. 访问应用

- Web 界面: `http://你的公网IP:5002`

## 成本优化

### 推荐配置

| 场景 | ECS 规格 | 预估月费用 |
|------|---------|-----------|
| 个人使用 | 2核4G | ~50-100元 |
| 小团队 | 4核8G | ~150-300元 |

> 💡 使用 MinerU API 无需 GPU，可以选择更低配置的服务器。

## 故障排查

### OCR 服务问题

```bash
# 检查 OCR 服务
curl http://localhost:5001/api/health
# 应返回: {"ocr_backend":"mineru",...}

# 查看日志
docker compose logs ocr-service
```

### MinerU API 错误

1. **API Key 无效** - 检查 MINERU_API_KEY 是否正确
2. **网络超时** - 检查服务器是否能访问 mineru.net

### LLM API 错误

1. **API Key 无效** - 检查 SILICONFLOW_API_KEY 是否正确
2. **网络问题** - 检查是否能访问 api.siliconflow.cn

## 更新升级

```bash
cd homesystem
git pull
docker compose pull
docker compose up -d
```

## 相关文档

- [部署指南](../deploy/README.md)
- [常见问题](../FAQ.md)
