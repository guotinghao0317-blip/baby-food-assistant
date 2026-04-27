# 🐳 Docker 启动指南

## 🚀 部署方式

本文档适用于**本地开发环境**。如需部署到线上服务器，请参考：[线上部署指南](./线上部署指南.md)

## ⚠️ 当前遇到的问题

### 1. Docker Hub 拉取速率限制

如果看到错误：`You have reached your unauthenticated pull rate limit`

**解决方案 A：登录 Docker Hub（推荐）**
```bash
docker login
# 输入你的 Docker Hub 用户名和密码
# 如果没有账号，去 https://hub.docker.com 注册一个
```

**解决方案 B：使用本地安装的 PostgreSQL 和 Redis**

如果已经通过 Homebrew 安装了 PostgreSQL 和 Redis，可以：
1. 启动本地服务（不使用 Docker）
2. 只使用 Docker 运行后端和前端

---

## 🚀 启动步骤

### 步骤 1：配置 OpenAI API Key

编辑 `backend/.env` 文件，将：
```
OPENAI_API_KEY=your-openai-api-key-here
```
替换为你的实际 API Key。

获取 API Key：https://platform.openai.com/api-keys

### 步骤 2：登录 Docker Hub（如果遇到拉取限制）

```bash
docker login
```

### 步骤 3：启动服务

**方式 A：使用 Docker 启动所有服务（推荐）**

```bash
cd /Users/jiayindeng/cursor尝试
docker-compose up -d
```

**方式 B：只启动数据库和缓存（如果已登录 Docker Hub）**

```bash
docker-compose up -d postgres redis
```

然后手动启动后端和前端（不使用 Docker）：

```bash
# 终端1：启动后端
cd /Users/jiayindeng/cursor尝试/backend
source venv/bin/activate
uvicorn main:app --reload

# 终端2：启动前端
cd /Users/jiayindeng/cursor尝试/frontend
npm run dev
```

---

## ✅ 验证服务状态

### 检查 Docker 容器
```bash
docker ps
```

应该看到：
- `postgres` 容器运行中
- `redis` 容器运行中
- `backend` 容器运行中（如果使用 Docker）
- `frontend` 容器运行中（如果使用 Docker）

### 检查服务健康
```bash
# 检查 PostgreSQL
docker-compose exec postgres pg_isready -U babyfood

# 检查 Redis
docker-compose exec redis redis-cli ping
# 应该返回：PONG

# 检查后端 API
curl http://localhost:8000/health
# 应该返回：{"status":"healthy"}

# 检查前端
curl http://localhost:3000
# 应该返回 HTML 内容
```

---

## 🔧 常用命令

### 查看日志
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 停止服务
```bash
docker-compose down
```

### 重启服务
```bash
docker-compose restart
```

### 查看服务状态
```bash
docker-compose ps
```

---

## 🐛 故障排除

### Q: 端口被占用
```bash
# 检查端口占用
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :8000  # 后端
lsof -i :3000  # 前端

# 修改 docker-compose.yml 中的端口映射
```

### Q: 数据库连接失败
```bash
# 检查数据库是否运行
docker-compose ps postgres

# 查看数据库日志
docker-compose logs postgres

# 重启数据库
docker-compose restart postgres
```

### Q: 前端无法连接后端
- 检查 `NEXT_PUBLIC_API_URL` 配置
- 确保后端服务正在运行
- 检查浏览器控制台错误

---

## 📝 下一步

服务启动成功后：
1. 访问前端：http://localhost:3000
2. 访问后端 API 文档：http://localhost:8000/docs
3. 开始使用应用！
