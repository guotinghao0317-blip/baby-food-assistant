# 辅食助手 - Baby Food Assistant

为2岁以下宝宝的宝妈提供个性化辅食食谱规划助手。

## 项目结构

```
.
├── frontend/          # Next.js 前端应用
├── backend/           # FastAPI 后端服务
├── docs/              # 文档
├── docker-compose.yml # Docker编排文件
└── README.md
```

## 快速开始

### 前置要求
- Node.js 18+
- Python 3.10+
- Docker & Docker Compose（可选）

### 开发环境启动

#### 1. 启动后端
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

#### 2. 启动前端
```bash
cd frontend
npm install
npm run dev
```

### Docker启动（推荐）
```bash
docker-compose up -d
```

## 功能特性

- ✅ 宝宝信息收集（年龄、发育阶段、过敏、偏好）
- ✅ 营养需求分析
- ✅ 一周食谱生成（含详细烹饪步骤）
- ✅ 配图生成
- ✅ 对话式食谱调整

## 技术栈

- **前端**：Next.js 14 + TypeScript + Tailwind CSS
- **后端**：FastAPI + Python
- **数据库**：PostgreSQL
- **AI模型**：OpenAI GPT-4 / 通义千问
- **图像生成**：DALL-E 3 / Stable Diffusion

## 环境变量配置

详见各子目录的 `.env.example` 文件。

## 开发计划

- [x] 架构设计
- [ ] 后端API开发
- [ ] 前端页面开发
- [ ] 模型集成
- [ ] 测试与优化

## 许可证

MIT
