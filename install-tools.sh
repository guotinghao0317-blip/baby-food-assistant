#!/bin/bash

# 辅食助手 - 工具安装脚本
# 适用于 macOS

set -e

echo "🍼 辅食助手 - 工具安装脚本"
echo "================================"
echo ""

# 检查是否已安装 Homebrew
if ! command -v brew &> /dev/null; then
    echo "📦 正在安装 Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # 添加 Homebrew 到 PATH（如果是 Apple Silicon Mac）
    if [ -f /opt/homebrew/bin/brew ]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
else
    echo "✅ Homebrew 已安装"
fi

echo ""
echo "📦 更新 Homebrew..."
brew update

echo ""
echo "🐍 检查 Python..."
if ! command -v python3 &> /dev/null || ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
    echo "正在安装 Python 3.11..."
    brew install python@3.11
    echo "✅ Python 3.11 已安装"
    echo "提示：如果系统默认 Python 版本仍为旧版本，请使用 python3.11 命令"
else
    PYTHON_VERSION=$(python3 --version)
    echo "✅ Python 已安装: $PYTHON_VERSION"
fi

echo ""
echo "🐘 检查 PostgreSQL..."
if ! command -v psql &> /dev/null; then
    echo "正在安装 PostgreSQL..."
    brew install postgresql@15
    brew services start postgresql@15
    echo "✅ PostgreSQL 15 已安装并启动"
    echo "提示：创建数据库命令: createdb babyfood_db"
else
    echo "✅ PostgreSQL 已安装"
fi

echo ""
echo "🔴 检查 Redis..."
if ! command -v redis-server &> /dev/null; then
    echo "正在安装 Redis..."
    brew install redis
    brew services start redis
    echo "✅ Redis 已安装并启动"
else
    echo "✅ Redis 已安装"
fi

echo ""
echo "🐳 检查 Docker..."
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker 未安装"
    echo "Docker 需要从官网下载安装：https://www.docker.com/products/docker-desktop/"
    echo "或者使用以下命令安装（需要先安装 Docker Desktop）："
    echo "  brew install --cask docker"
else
    echo "✅ Docker 已安装"
fi

echo ""
echo "================================"
echo "✅ 安装完成！"
echo ""
echo "📋 已安装的工具："
echo "  - Node.js: $(node --version 2>/dev/null || echo '未安装')"
echo "  - Python: $(python3 --version 2>/dev/null || echo '未安装')"
echo "  - PostgreSQL: $(psql --version 2>/dev/null || echo '未安装')"
echo "  - Redis: $(redis-server --version 2>/dev/null || echo '未安装')"
echo "  - Docker: $(docker --version 2>/dev/null || echo '未安装')"
echo ""
echo "🚀 下一步："
echo "  1. 如果 Docker 未安装，请先安装 Docker Desktop"
echo "  2. 运行: cd backend && cp .env.example .env"
echo "  3. 编辑 backend/.env，填入 OPENAI_API_KEY"
echo "  4. 运行: docker-compose up -d"
echo ""
