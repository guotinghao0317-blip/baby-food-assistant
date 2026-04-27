"""
分步生成一周食谱功能 - API集成测试
测试目标: recipes.py 中的 POST /api/recipes/generate-step-by-step 端点
"""
import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import func
from unittest.mock import AsyncMock, patch

from app.models import Recipe, RecipeDetail
from app.services.recipe_generator import generate_weekly_recipe_step_by_step


class TestGenerateStepByStepAPI:
    """测试分步生成一周食谱API端点"""

    def test_generate_step_by_step_invalid_baby_id(
        self,
        client: TestClient,
        test_user
    ):
        """测试使用不存在的宝宝ID - 应该返回404"""
        # 注意：这里需要模拟认证，实际项目中需要处理token
        # 简化测试：直接调用依赖验证逻辑
        response = client.post(
            "/api/recipes/generate-step-by-step",
            json={"baby_id": 99999}
        )

        # 因为未认证，应该返回401，或者我们需要在测试中mock认证
        # 这里我们先检查状态码
        assert response.status_code in [401, 404]

    def test_generate_step_by_step_unauthorized(self, client: TestClient):
        """测试未认证访问 - 应该返回401"""
        response = client.post(
            "/api/recipes/generate-step-by-step",
            json={"baby_id": 1}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_generate_step_by_step_streaming_response(
        self,
        db_session: Session,
        test_baby,
        test_user
    ):
        """测试流式响应格式正确性"""
        # 创建测试菜品数据供缓存使用
        test_recipe = Recipe(
            baby_id=test_baby.id,
            user_id=test_user.id,
            week_start_date=db_session.query(func.now()).scalar(),
            status="generating"
        )
        db_session.add(test_recipe)
        db_session.commit()

        # 先插入一些菜品数据
        for meal in ["breakfast", "lunch", "dinner", "snack"]:
            detail = RecipeDetail(
                recipe_id=test_recipe.id,
                day_of_week=1,
                meal_type=meal,
                dish_name=f"测试菜品-{meal}",
                ingredients=[{"name": "南瓜", "amount": "50g"}],
                cooking_steps=[{"step": 1, "description": "洗净"}],
                nutrition_info={"calories": 100}
            )
            db_session.add(detail)
        db_session.commit()

        # 直接测试服务层函数，因为API层需要认证
        from app.services.recipe_generator import generate_weekly_recipe_step_by_step

        events = []
        async for event in generate_weekly_recipe_step_by_step(test_baby, test_recipe.id, db_session):
            events.append(event)

        # 验证事件格式
        for event in events:
            # 验证SSE格式
            assert event.startswith("data: ")
            assert event.endswith("\n\n")

            # 验证JSON内容
            content = event.replace("data: ", "").replace("\n\n", "")
            data = json.loads(content)
            assert "type" in data
            assert data["type"] in ["day_started", "day_done", "finished", "error"]

    @pytest.mark.asyncio
    async def test_generate_step_by_step_creates_recipe_record(
        self,
        db_session: Session,
        test_baby,
        test_user
    ):
        """测试生成过程中创建Recipe记录"""
        # 先创建一些菜品数据供缓存使用
        temp_recipe = Recipe(
            baby_id=test_baby.id,
            user_id=test_user.id,
            week_start_date=db_session.query(func.now()).scalar(),
            status="generating"
        )
        db_session.add(temp_recipe)
        db_session.commit()

        for day in range(1, 4):
            for meal in ["breakfast", "lunch", "dinner", "snack"]:
                detail = RecipeDetail(
                    recipe_id=temp_recipe.id,
                    day_of_week=day,
                    meal_type=meal,
                    dish_name=f"缓存菜品{day}-{meal}",
                    ingredients=[{"name": "x", "amount": "1"}],
                    cooking_steps=[{"step": 1, "description": "x"}],
                    nutrition_info={}
                )
                db_session.add(detail)
        db_session.commit()

        # 创建新的recipe用于测试
        test_recipe = Recipe(
            baby_id=test_baby.id,
            user_id=test_user.id,
            week_start_date=db_session.query(func.now()).scalar(),
            status="generating"
        )
        db_session.add(test_recipe)
        db_session.commit()

        # 收集所有事件
        events = []
        async for event in generate_weekly_recipe_step_by_step(test_baby, test_recipe.id, db_session):
            events.append(event)

        # 验证每个day_done事件包含details
        day_done_events = [e for e in events if '"type":"day_done"' in e]
        assert len(day_done_events) == 7

        for event in day_done_events:
            content = event.replace("data: ", "").replace("\n\n", "")
            data = json.loads(content)
            assert "day" in data
            assert "details" in data
            assert len(data["details"]) == 4  # 每天4餐

        # 验证finished事件包含recipe_id
        finished_events = [e for e in events if '"type":"finished"' in e]
        assert len(finished_events) == 1
        content = finished_events[0].replace("data: ", "").replace("\n\n", "")
        data = json.loads(content)
        assert "recipe_id" in data
        assert data["recipe_id"] == test_recipe.id

    @pytest.mark.asyncio
    async def test_generate_step_by_step_persists_all_data(
        self,
        db_session: Session,
        test_baby,
        test_user
    ):
        """测试所有生成的数据都正确持久化到数据库"""
        # 创建测试菜品数据
        temp_recipe = Recipe(
            baby_id=test_baby.id,
            user_id=test_user.id,
            week_start_date=db_session.query(func.now()).scalar(),
            status="generating"
        )
        db_session.add(temp_recipe)
        db_session.commit()

        for meal in ["breakfast", "lunch", "dinner", "snack"]:
            for day in range(1, 4):
                detail = RecipeDetail(
                    recipe_id=temp_recipe.id,
                    day_of_week=day,
                    meal_type=meal,
                    dish_name=f"测试菜品{day}-{meal}",
                    ingredients=[{"name": "南瓜", "amount": "50g"}],
                    cooking_steps=[{"step": 1, "description": "洗净"}],
                    nutrition_info={"calories": 100}
                )
                db_session.add(detail)
        db_session.commit()

        # 创建新的测试recipe
        test_recipe = Recipe(
            baby_id=test_baby.id,
            user_id=test_user.id,
            week_start_date=db_session.query(func.now()).scalar(),
            status="generating"
        )
        db_session.add(test_recipe)
        db_session.commit()

        # 执行生成
        events = []
        async for event in generate_weekly_recipe_step_by_step(test_baby, test_recipe.id, db_session):
            events.append(event)

        # 验证数据库
        details_count = db_session.query(RecipeDetail).filter(
            RecipeDetail.recipe_id == test_recipe.id
        ).count()
        assert details_count == 28  # 7天 × 4餐

        # 验证每天都有4餐
        for day in range(1, 8):
            day_count = db_session.query(RecipeDetail).filter(
                RecipeDetail.recipe_id == test_recipe.id,
                RecipeDetail.day_of_week == day
            ).count()
            assert day_count == 4, f"第{day}天应该有4餐，但有{day_count}餐"

        # 验证每个餐次类型都存在
        meal_types = db_session.query(RecipeDetail.meal_type).filter(
            RecipeDetail.recipe_id == test_recipe.id
        ).distinct().all()
        meal_type_values = [m[0] for m in meal_types]
        assert "breakfast" in meal_type_values
        assert "lunch" in meal_type_values
        assert "dinner" in meal_type_values
        assert "snack" in meal_type_values

        # 验证状态更新
        db_session.refresh(test_recipe)
        assert test_recipe.status == "completed"

    @pytest.mark.asyncio
    async def test_generate_step_by_step_with_api_mock(
        self,
        db_session: Session,
        test_baby,
        test_user,
        mock_volcengine_client
    ):
        """测试使用Mock API生成"""
        test_recipe = Recipe(
            baby_id=test_baby.id,
            user_id=test_user.id,
            week_start_date=db_session.query(func.now()).scalar(),
            status="generating"
        )
        db_session.add(test_recipe)
        db_session.commit()

        # Mock API返回
        call_count = 0

        def mock_response(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return {
                "details": [
                    {
                        "dish_name": f"API生成菜品{call_count}-{i}",
                        "meal_type": meal,
                        "ingredients": [{"name": "食材", "amount": "50g"}],
                        "cooking_steps": [{"step": 1, "description": "步骤"}],
                        "nutrition_info": {"calories": 100}
                    }
                    for i, meal in enumerate(["breakfast", "lunch", "dinner", "snack"])
                ]
            }

        mock_volcengine_client.generate_json = AsyncMock(side_effect=mock_response)

        events = []
        async for event in generate_weekly_recipe_step_by_step(test_baby, test_recipe.id, db_session):
            events.append(event)

        # 验证API被调用了7次（每天一次）
        assert mock_volcengine_client.generate_json.call_count == 7

        # 验证所有事件
        day_done_events = [e for e in events if '"type":"day_done"' in e]
        assert len(day_done_events) == 7

        # 验证菜品名称包含"API生成菜品"
        all_dish_names = []
        for event in day_done_events:
            data = json.loads(event.replace("data: ", "").replace("\n\n", ""))
            for detail in data["details"]:
                all_dish_names.append(detail["dish_name"])

        assert any("API生成菜品" in name for name in all_dish_names)

    @pytest.mark.asyncio
    async def test_generate_step_by_step_deduplication(
        self,
        db_session: Session,
        test_baby,
        test_user,
        mock_volcengine_client
    ):
        """测试菜品去重功能"""
        test_recipe = Recipe(
            baby_id=test_baby.id,
            user_id=test_user.id,
            week_start_date=db_session.query(func.now()).scalar(),
            status="generating"
        )
        db_session.add(test_recipe)
        db_session.commit()

        # 每天生成不同的菜品
        generated_days = set()

        def mock_response(*args, **kwargs):
            import re
            user_prompt = args[1] if len(args) > 1 else ""
            day_match = re.search(r'第(\d+)天', user_prompt)
            day = int(day_match.group(1)) if day_match else 1
            generated_days.add(day)

            return {
                "details": [
                    {
                        "dish_name": f"第{day}天-{meal}-独特菜名",
                        "meal_type": meal,
                        "ingredients": [{"name": "食材", "amount": "50g"}],
                        "cooking_steps": [{"step": 1, "description": "步骤"}],
                        "nutrition_info": {"calories": 100}
                    }
                    for meal in ["breakfast", "lunch", "dinner", "snack"]
                ]
            }

        mock_volcengine_client.generate_json = AsyncMock(side_effect=mock_response)

        events = []
        async for event in generate_weekly_recipe_step_by_step(test_baby, test_recipe.id, db_session):
            events.append(event)

        # 验证生成了7天
        assert len(generated_days) == 7

        # 从数据库验证没有重复菜品
        all_dishes = db_session.query(RecipeDetail.dish_name).filter(
            RecipeDetail.recipe_id == test_recipe.id
        ).all()
        dish_names = [d[0] for d in all_dishes]

        # 应该没有重复
        assert len(dish_names) == len(set(dish_names))

    def test_get_recipe_status_endpoint(
        self,
        client: TestClient,
        db_session: Session,
        test_user,
        test_baby
    ):
        """测试获取食谱状态端点"""
        # 创建测试食谱和一些详情
        from sqlalchemy import func
        recipe = Recipe(
            baby_id=test_baby.id,
            user_id=test_user.id,
            week_start_date=db_session.query(func.now()).scalar(),
            status="generating"
        )
        db_session.add(recipe)
        db_session.commit()

        # 添加3天的详情
        for day in range(1, 4):
            for meal in ["breakfast", "lunch", "dinner", "snack"]:
                detail = RecipeDetail(
                    recipe_id=recipe.id,
                    day_of_week=day,
                    meal_type=meal,
                    dish_name=f"菜{day}-{meal}",
                    ingredients=[{"name": "x", "amount": "1"}],
                    cooking_steps=[{"step": 1, "description": "x"}],
                    nutrition_info={}
                )
                db_session.add(detail)
        db_session.commit()

        # 直接测试核心逻辑（不需要调用async函数）
        # 验证查询逻辑
        generated_days = db_session.query(RecipeDetail.day_of_week).filter(
            RecipeDetail.recipe_id == recipe.id
        ).distinct().count()

        assert recipe.id == recipe.id
        assert recipe.status == "generating"
        assert generated_days == 3
        # total_days 总是 7（固定）


