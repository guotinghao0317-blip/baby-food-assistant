#!/bin/bash
# 远程部署脚本 - 通过SSH执行命令

SSH_PASSWORD="@qie8023"
SERVER_IP="170.106.110.237"
SERVER_USER="ubuntu"

# 使用sshpass如果可用，否则使用expect
if command -v sshpass >/dev/null 2>&1; then
    echo "Using sshpass"
    sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP << 'EOF'
    cd ~/baby-food-assistant
    git pull origin main

    # 导出环境变量
    export OPENAI_API_KEY=c27412f1-239d-453f-a0b9-5e5bd296b027
    export SECRET_KEY=58122a33830a7540724586ca76836f1590762c5711d65b5aff7e3df4fd7d8159
    export POSTGRES_USER=babyfood
    export POSTGRES_PASSWORD=babyfood123
    export POSTGRES_DB=babyfood_db
    export ENVIRONMENT=production
    export NEXT_PUBLIC_API_URL=http://170.106.110.237:8000

    docker-compose -f deploy-production.yml up -d --build
    echo "=== Deployment complete, showing status ==="
    docker-compose -f deploy-production.yml ps
    echo "=== Checking backend health ==="
    sleep 10
    curl -s http://localhost:8000/health || echo "Backend not responding yet"
EOF
else
    echo "sshpass not found, using direct SSH with password prompt"
    exit 1
fi
