# HomeSystem 云端镜像部署指南

> 🌟 **推荐部署方式**：使用预构建的Docker镜像，无需克隆代码，快速启动

## 📋 前置要求

### 系统要求
- Docker 20.10+ 和 Docker Compose 2.0+
- 2GB+ 内存（一体化部署）

### API 密钥
- MinerU API Key（OCR 服务）：https://mineru.net/apiManage/docs
- 硅基流动 API Key（LLM 服务）：https://siliconflow.cn

## 📋 部署方式概览

| 部署方式 | 适用场景 | 配置复杂度 | 资源要求 |
|---------|---------|-----------|----------|
| **一体化部署** | 快速体验、小规模使用 | ⭐ 简单 | 单机 2GB+ 内存 |
| **分离部署** | 生产环境、资源优化 | ⭐⭐ 中等 | 多机分布式 |

## 🚀 一体化部署（推荐）

### 快速开始

```bash
# 1. 创建项目目录
mkdir homesystem && cd homesystem

# 2. 下载配置文件
curl -o docker-compose.yml https://raw.githubusercontent.com/yangtao121/homesystem/main/deploy/docker-compose.yml

# 3. 修改配置（重要！）
vim docker-compose.yml
# 必须修改：
# - POSTGRES_PASSWORD: 设置安全的数据库密码
# - MINERU_API_KEY: 填写您的 MinerU API 密钥
# - SILICONFLOW_API_KEY: 填写您的硅基流动 API 密钥

# 4. 启动服务
docker compose up -d

# 5. 检查服务状态
docker compose ps
```

### 服务访问地址

- **Web应用**: http://localhost:5002
- **数据库**: localhost:15432 (用户: homesystem)
- **Redis**: localhost:16379
- **OCR服务**: http://localhost:5001

### 管理界面（可选）

```bash
# 启动数据库和Redis管理界面
docker compose --profile tools up -d

# 访问地址：
# - pgAdmin: http://localhost:8080 (admin@homesystem.local / admin123)
# - Redis Commander: http://localhost:8081
```

## 🏗️ 分离部署（高级用户）

适合多机器部署，优化资源利用和性能。

### 部署架构

```
机器A (数据库)          机器B (OCR)           机器C (Web)
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ PostgreSQL:15432│◄───┼─OCR Service:5001│◄───┼─PaperAnalysis   │
│ Redis:16379     │    │ (MinerU API)    │    │ :5002           │
└─────────────────┘    └─────────────────┘    └─────────────────┘
   192.168.1.100        192.168.1.101         192.168.1.102
```

### 1. 部署数据库服务 (机器A)

```bash
curl -o docker-compose.database.yml https://raw.githubusercontent.com/yangtao121/homesystem/main/deploy/docker-compose.database.yml

# 修改密码配置
vim docker-compose.database.yml

# 启动数据库服务
docker compose -f docker-compose.database.yml up -d
```

### 2. 部署OCR服务 (机器B)

```bash
curl -o docker-compose.ocr-mineru.yml https://raw.githubusercontent.com/yangtao121/homesystem/main/deploy/docker-compose.ocr-mineru.yml

# 创建环境变量文件
echo "MINERU_API_KEY=your_api_key_here" > .env

# 启动 OCR 服务
docker compose -f docker-compose.ocr-mineru.yml up -d

# 验证服务
curl http://localhost:5001/api/health
```

### 3. 部署Web服务 (机器C)

```bash
curl -o docker-compose.web.yml https://raw.githubusercontent.com/yangtao121/homesystem/main/deploy/docker-compose.web.yml

# 修改连接配置
vim docker-compose.web.yml
# 必须修改：
# - DB_HOST: 192.168.1.100 (数据库服务器IP)
# - REDIS_HOST: 192.168.1.100 (Redis服务器IP)
# - REMOTE_OCR_ENDPOINT: http://192.168.1.101:5001 (OCR服务器地址)
# - SILICONFLOW_API_KEY: sk-xxx (您的API密钥)

# 启动Web服务
docker compose -f docker-compose.web.yml up -d
```

## ⚙️ 配置说明

### LLM API 配置

```yaml
# 硅基流动 (SiliconFlow)
SILICONFLOW_API_KEY: sk-xxx
SILICONFLOW_BASE_URL: https://api.siliconflow.cn/v1
```

### OCR 配置

```yaml
# MinerU API
MINERU_API_KEY: your_api_key
MINERU_BASE_URL: https://mineru.net
MINERU_TIMEOUT: 600
```

### 可选服务配置

```yaml
# Dify 知识库
DIFY_BASE_URL: http://192.168.1.105/v1
DIFY_KB_API_KEY: xxx

# SiYuan 笔记
SIYUAN_API_URL: http://192.168.1.106:6806
SIYUAN_API_TOKEN: xxx
```

## 🔧 常用操作

### 查看服务状态

```bash
docker compose ps
docker compose logs paper-analysis
```

### 更新服务

```bash
docker compose pull
docker compose up -d
```

### 备份数据

```bash
docker compose exec postgres pg_dump -U homesystem homesystem > backup.sql
```

### 清理环境

```bash
docker compose down
docker compose down -v  # ⚠️ 清理数据
```

## 🐛 故障排查

### 常见问题

1. **服务无法启动**
   ```bash
   docker compose logs -f 服务名
   ```

2. **OCR服务异常**
   ```bash
   curl http://localhost:5001/api/health
   docker compose logs ocr-service
   ```

3. **LLM API 调用失败**
   - 检查 SILICONFLOW_API_KEY 是否正确
   - 确认网络能访问 api.siliconflow.cn

## 📚 更多文档

- [华为云部署指南](../docs/huaweicloud-deploy-guide.md)
- [常见问题](../FAQ.md)

## 🆘 获取帮助

- QQ交流群：963812265
- GitHub Issues：[提交问题](https://github.com/yangtao121/homesystem/issues)
