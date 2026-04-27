"""
测试配置和公共fixture
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from typing import Generator, AsyncGenerator

import sys
import os

# 添加backend目录到Python路径
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

# 导入main模块
main_module_path = os.path.join(backend_dir, 'main.py')
if os.path.exists(main_module_path):
    from main import app
else:
    # Fallback - create a minimal app for testing
    from fastapi import FastAPI
    app = FastAPI()
from app.database import Base, get_db
from app.models import User, Baby, NutritionRequirement, Recipe, RecipeDetail

# 使用内存SQLite数据库进行测试
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """创建测试数据库会话"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()
        # 删除所有表
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session) -> TestClient:
    """创建测试客户端"""
    # 重写依赖项
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    user = User(
        email="test@example.com",
        password_hash="hashed_password123"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_baby(db_session, test_user):
    """创建测试宝宝"""
    baby = Baby(
        user_id=test_user.id,
        name="测试宝宝",
        age_months=12,
        weight=10.5,
        height=75.0,
        feeding_stage="软块状食物，可咀嚼",
        teething_status="已出8颗牙",
        months_since_weaning=6,
        allergies=["牛奶", "鸡蛋"],
        liked_ingredients=["南瓜", "胡萝卜", "鸡肉"],
        disliked_ingredients=["西兰花"],
        family_diet_style="中餐为主，荤素搭配"
    )
    db_session.add(baby)
    db_session.commit()
    db_session.refresh(baby)
    return baby


@pytest.fixture
def test_nutrition_requirement(db_session, test_baby):
    """创建测试营养需求"""
    nutrition = NutritionRequirement(
        baby_id=test_baby.id,
        calories_per_day=800.0,
        protein_g=20.0,
        iron_mg=10.0,
        calcium_mg=500.0
    )
    db_session.add(nutrition)
    db_session.commit()
    db_session.refresh(nutrition)
    return nutrition


@pytest.fixture
def test_recipe(db_session, test_user, test_baby):
    """创建测试食谱（空的，状态为generating）"""
    recipe = Recipe(
        baby_id=test_baby.id,
        user_id=test_user.id,
        week_start_date=datetime.now(),
        status="generating"
    )
    db_session.add(recipe)
    db_session.commit()
    db_session.refresh(recipe)
    return recipe


@pytest.fixture
def sample_dish_data():
    """示例菜品数据"""
    return {
        "dish_name": "南瓜小米粥",
        "ingredients": [
            {"name": "南瓜", "amount": "50g"},
            {"name": "小米", "amount": "20g"},
            {"name": "清水", "amount": "200ml"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "小米提前浸泡30分钟"},
            {"step": 2, "description": "南瓜去皮切小丁"},
            {"step": 3, "description": "加水煮开后放入小米，煮20分钟"},
            {"step": 4, "description": "加入南瓜丁，再煮10分钟至软烂"}
        ],
        "nutrition_info": {"calories": 85, "protein": 2.1, "iron": 0.8}
    }


@pytest.fixture
def mock_volcengine_client(mocker):
    """Mock火山引擎API客户端"""
    mock_client = mocker.patch("app.services.volcengine_client.get_volcengine_client")
    mock_instance = mocker.MagicMock()
    mock_instance.is_configured = True
    mock_instance.model_name = "test-model"
    mock_client.return_value = mock_instance
    return mock_instance


@pytest.fixture
def mock_volcengine_stream_response():
    """Mock流式响应数据"""
    async def mock_stream(*args, **kwargs):
        chunks = ['{"', 'day_of_week', '": 1,', '"details":', '[']
        for chunk in chunks:
            yield chunk

    return mock_stream
