
# 远程执行的命令

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

echo "Starting docker-compose build and up..."
docker-compose -f deploy-production.yml up -d --build
echo "=== Deployment complete, showing status ==="
docker-compose -f deploy-production.yml ps
echo "=== Checking backend health ==="
sleep 15
curl -s http://localhost:8000/health || echo "Backend not responding yet"
echo "=== All done ==="
