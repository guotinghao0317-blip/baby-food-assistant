"""
辅食助手后端主入口
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import auth, babies, recipes, conversations
from app.database import engine, Base

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="辅食助手 API",
    description="为2岁以下宝宝提供个性化辅食食谱规划",
    version="1.0.0"
)

# CORS配置
# 从环境变量读取允许的源，支持多个域名用逗号分隔
import os
cors_origins = os.environ.get("CORS_ALLOW_ORIGINS", "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    error_detail = {
        "detail": str(exc),
        "traceback": traceback.format_exc()
    }
    return JSONResponse(
        status_code=500,
        content=error_detail
    )

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(babies.router, prefix="/api/babies", tags=["宝宝信息"])
app.include_router(recipes.router, prefix="/api/recipes", tags=["食谱"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["对话"])


@app.get("/")
async def root():
    return {"message": "辅食助手 API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
