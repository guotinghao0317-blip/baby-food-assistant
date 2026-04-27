"""
食谱路由
"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

logger = logging.getLogger(__name__)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import AsyncGenerator

from app.database import get_db
from app.models import User, Baby, Recipe, RecipeDetail
from app.schemas import (
    RecipeGenerateRequest, RecipeResponse, RecipeAdjustRequest, ReplaceDishRequest
)
from app.routers.auth import get_current_user
from app.services.recipe_generator import (
    generate_weekly_recipe, generate_weekly_recipe_stream, generate_replace_dish_stream,
    generate_next_day_stream, generate_weekly_recipe_step_by_step
)
from app.services.recipe_adjuster import adjust_recipe
from app.services.dish_replacer import replace_dish

router = APIRouter()


@router.post("/generate", response_model=RecipeResponse)
async def generate_recipe(
    request: RecipeGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """生成一周食谱"""
    # 验证宝宝信息
    baby = db.query(Baby).filter(
        Baby.id == request.baby_id,
        Baby.user_id == current_user.id
    ).first()
    
    if not baby:
        raise HTTPException(status_code=404, detail="Baby not found")
    
    # 计算本周开始日期（周一）
    today = datetime.now().date()
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday)
    week_start_datetime = datetime.combine(week_start, datetime.min.time())
    
    # 调用生成服务
    recipe_data = await generate_weekly_recipe(baby, db)
    
    # 创建食谱记录
    recipe = Recipe(
        baby_id=baby.id,
        user_id=current_user.id,
        week_start_date=week_start_datetime,
        status="published"
    )
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    
    # 创建食谱详情
    for detail_data in recipe_data["details"]:
        detail = RecipeDetail(
            recipe_id=recipe.id,
            **detail_data
        )
        db.add(detail)
    
    db.commit()
    db.refresh(recipe)
    
    # 异步生成配图（如果还没有）
    # if background_tasks:
    #     background_tasks.add_task(generate_recipe_images, recipe.id, db)
    
    return recipe


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取食谱详情"""
    recipe = db.query(Recipe).filter(
        Recipe.id == recipe_id,
        Recipe.user_id == current_user.id
    ).first()

    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # 显式加载所有菜品数据，确保返回完整的details数组
    details = db.query(RecipeDetail).filter(
        RecipeDetail.recipe_id == recipe_id
    ).order_by(RecipeDetail.day_of_week, RecipeDetail.meal_type).all()

    logger.info(f"查询到食谱 {recipe_id} 的菜品数量: {len(details)}")

    # 验证每个detail的必需字段
    for detail in details:
        if not hasattr(detail, 'day_of_week') or detail.day_of_week is None:
            logger.warning(f"菜品 {detail.id} 缺少 day_of_week 字段")
        if not hasattr(detail, 'meal_type') or detail.meal_type is None:
            logger.warning(f"菜品 {detail.id} 缺少 meal_type 字段")
        if not hasattr(detail, 'dish_name') or detail.dish_name is None:
            logger.warning(f"菜品 {detail.id} 缺少 dish_name 字段")

    # 将details附加到recipe对象，确保序列化时包含
    recipe.details = details

    return recipe


@router.put("/{recipe_id}/adjust")
async def adjust_recipe_endpoint(
    recipe_id: int,
    request: RecipeAdjustRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """调整食谱（对话接口）"""
    recipe = db.query(Recipe).filter(
        Recipe.id == recipe_id,
        Recipe.user_id == current_user.id
    ).first()
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # 调用调整服务
    adjusted_data = await adjust_recipe(recipe, request.message, db)
    
    # 更新食谱详情
    # 这里简化处理，实际应该更智能地合并调整
    for detail_data in adjusted_data.get("details", []):
        existing_detail = db.query(RecipeDetail).filter(
            RecipeDetail.recipe_id == recipe_id,
            RecipeDetail.day_of_week == detail_data["day_of_week"],
            RecipeDetail.meal_type == detail_data["meal_type"]
        ).first()
        
        if existing_detail:
            for key, value in detail_data.items():
                if key not in ["recipe_id", "day_of_week", "meal_type"]:
                    setattr(existing_detail, key, value)
        else:
            detail = RecipeDetail(recipe_id=recipe_id, **detail_data)
            db.add(detail)
    
    db.commit()
    db.refresh(recipe)
    
    return {"message": "食谱已调整", "recipe": recipe}


@router.get("")
async def list_recipes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 10
):
    """获取历史食谱列表"""
    recipes = db.query(Recipe).filter(
        Recipe.user_id == current_user.id
    ).order_by(Recipe.created_at.desc()).offset(skip).limit(limit).all()

    return recipes


@router.post("/{recipe_id}/replace-dish", response_model=RecipeResponse)
async def replace_dish_endpoint(
    recipe_id: int,
    request: ReplaceDishRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    换一道菜功能

    保持餐次不变，生成一道营养相似但食材不同的替代菜品，更新数据库记录
    """
    # 验证食谱属于当前用户
    recipe = db.query(Recipe).filter(
        Recipe.id == recipe_id,
        Recipe.user_id == current_user.id
    ).first()

    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # 查找原菜品记录
    original_dish = db.query(RecipeDetail).filter(
        RecipeDetail.id == request.original_dish_id,
        RecipeDetail.recipe_id == recipe_id,
        RecipeDetail.day_of_week == request.day_of_week,
        RecipeDetail.meal_type == request.meal_type
    ).first()

    if not original_dish:
        raise HTTPException(status_code=404, detail="Original dish not found")

    # 获取宝宝信息
    baby = db.query(Baby).filter(
        Baby.id == recipe.baby_id,
        Baby.user_id == current_user.id
    ).first()

    if not baby:
        raise HTTPException(status_code=404, detail="Baby not found")

    # 生成替代菜品
    replacement_data = await replace_dish(original_dish, baby, db)

    # 更新现有菜品记录
    original_dish.dish_name = replacement_data["dish_name"]
    original_dish.ingredients = replacement_data["ingredients"]
    original_dish.cooking_steps = replacement_data["cooking_steps"]
    original_dish.nutrition_info = replacement_data["nutrition_info"]

    # 保存到数据库
    db.commit()
    db.refresh(recipe)

    return recipe


@router.post("/generate-stream")
async def generate_recipe_stream(
    request: RecipeGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    流式生成一周食谱 - 逐菜生成模式
    使用Server-Sent Events逐步返回生成结果，用户无需等待完整生成

    SSE事件类型:
    - started: 生成开始，返回recipe_id
    - day_started: 某天开始生成
    - dish_started: 单道菜开始生成
    - dish_stream: 单道菜流式内容（打字机效果）
    - dish_done: 单道菜生成完成，返回完整菜品数据
    - day_done: 某天所有菜品生成完成
    - finished: 全部7天完成
    - error: 生成错误
    """
    # 验证宝宝信息
    baby = db.query(Baby).filter(
        Baby.id == request.baby_id,
        Baby.user_id == current_user.id
    ).first()

    if not baby:
        raise HTTPException(status_code=404, detail="Baby not found")

    # 计算本周开始日期（周一）
    today = datetime.now().date()
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday)
    week_start_datetime = datetime.combine(week_start, datetime.min.time())

    # 创建空Recipe记录，状态为generating
    recipe = Recipe(
        baby_id=baby.id,
        user_id=current_user.id,
        week_start_date=week_start_datetime,
        status="generating"
    )
    db.add(recipe)
    db.commit()
    db.refresh(recipe)

    # 使用generate_weekly_recipe_step_by_step进行流式生成并保存
    async def final_generator():
        try:
            # 发送started事件
            yield f"data: {json.dumps({'type': 'started', 'data': {'id': recipe.id}, 'recipe_id': recipe.id}, ensure_ascii=False)}\n\n"

            # 调用分步生成主函数
            async for event in generate_weekly_recipe_step_by_step(baby, recipe.id, db):
                yield event
        except Exception as e:
            logger.error(f"Error in stream generation: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': '食谱生成失败，请重试'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        final_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/{recipe_id}/replace-dish-stream")
async def replace_dish_stream(
    recipe_id: int,
    request: ReplaceDishRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    流式生成替换菜品
    使用Server-Sent Events逐步返回生成结果
    """
    # 验证食谱属于当前用户
    recipe = db.query(Recipe).filter(
        Recipe.id == recipe_id,
        Recipe.user_id == current_user.id
    ).first()

    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # 查找原菜品记录
    original_dish = db.query(RecipeDetail).filter(
        RecipeDetail.id == request.original_dish_id,
        RecipeDetail.recipe_id == recipe_id,
        RecipeDetail.day_of_week == request.day_of_week,
        RecipeDetail.meal_type == request.meal_type
    ).first()

    if not original_dish:
        raise HTTPException(status_code=404, detail="Original dish not found")

    # 获取宝宝信息
    baby = db.query(Baby).filter(
        Baby.id == recipe.baby_id,
        Baby.user_id == current_user.id
    ).first()

    if not baby:
        raise HTTPException(status_code=404, detail="Baby not found")

    generator = generate_replace_dish_stream(recipe_id, original_dish, baby, db)
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/generate-start")
async def generate_start(
    request: RecipeGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    开始分步生成 - 创建空Recipe记录
    """
    # 验证宝宝信息
    baby = db.query(Baby).filter(
        Baby.id == request.baby_id,
        Baby.user_id == current_user.id
    ).first()

    if not baby:
        raise HTTPException(status_code=404, detail="Baby not found")

    # 计算本周开始日期（周一）
    today = datetime.now().date()
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday)
    week_start_datetime = datetime.combine(week_start, datetime.min.time())

    # 创建初始Recipe记录，状态为generating
    recipe = Recipe(
        baby_id=baby.id,
        user_id=current_user.id,
        week_start_date=week_start_datetime,
        status="generating"
    )
    db.add(recipe)
    db.commit()
    db.refresh(recipe)

    return {
        "recipe_id": recipe.id,
        "status": recipe.status,
        "baby_id": baby.id
    }


@router.get("/recipe-status/{recipe_id}")
async def get_recipe_status(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    查询食谱生成状态
    返回已生成天数和整体状态
    """
    recipe = db.query(Recipe).filter(
        Recipe.id == recipe_id,
        Recipe.user_id == current_user.id
    ).first()

    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # 统计已生成的天数 - 使用更准确的查询方式
    # 先获取所有不同的 day_of_week 值
    day_nums = db.query(RecipeDetail.day_of_week).filter(
        RecipeDetail.recipe_id == recipe_id
    ).distinct().all()

    # 转换为集合去重
    generated_day_set = set(d[0] for d in day_nums)
    generated_days = len(generated_day_set)

    # 详细日志
    logger.info(f"[Status Query] Recipe {recipe_id}: status={recipe.status}, generated_days={generated_days}, day_set={sorted(generated_day_set)}")

    # 如果数据库状态是 completed，但实际数据不足7天，重置为 generating
    if recipe.status == "completed" and generated_days < 7:
        logger.warning(f"[Status Query] Recipe {recipe_id}: 状态不一致！status=completed 但只有 {generated_days} 天数据，重置为 generating")
        recipe.status = "generating"
        db.commit()

    # 如果实际数据已满7天，但状态不是 completed，更新为 completed
    if generated_days >= 7 and recipe.status != "completed":
        logger.info(f"[Status Query] Recipe {recipe_id}: 实际数据已满7天，更新状态为 completed")
        recipe.status = "completed"
        db.commit()

    return {
        "recipe_id": recipe.id,
        "status": recipe.status,
        "generated_days": generated_days,
        "total_days": 7
    }


@router.get("/generate-next-day/{recipe_id}")
async def generate_next_day(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    流式生成下一天食谱 - SSE端点
    使用Server-Sent Events按天返回生成结果

    SSE事件类型:
    - day_started: 某天开始生成，包含day字段
    - day_done: 某天所有菜品生成完成，包含details(菜品数组)、failed_meals(失败餐次数组)、all_completed(是否全部7天完成)
    - finished: 所有7天完成，包含recipe_id
    - all_completed: 食谱已全部生成完毕
    - error: 生成错误
    """
    # 验证食谱属于当前用户
    recipe = db.query(Recipe).filter(
        Recipe.id == recipe_id,
        Recipe.user_id == current_user.id
    ).first()

    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # 检查是否已经完成
    if recipe.status == "completed":
        async def completed_generator():
            yield f"data: {json.dumps({'type': 'all_completed', 'recipe_id': recipe_id}, ensure_ascii=False)}\n\n"
        return StreamingResponse(
            completed_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )

    # 获取宝宝信息
    baby = db.query(Baby).filter(
        Baby.id == recipe.baby_id,
        Baby.user_id == current_user.id
    ).first()

    if not baby:
        raise HTTPException(status_code=404, detail="Baby not found")

    # 获取已生成的天数和菜品
    generated_details = db.query(RecipeDetail).filter(
        RecipeDetail.recipe_id == recipe_id
    ).all()

    # 找出下一天要生成的天号 (1-7)
    generated_day_nums = set(d.day_of_week for d in generated_details)
    next_day = None
    for day in range(1, 8):
        if day not in generated_day_nums:
            next_day = day
            break

    if next_day is None:
        # 所有天都生成完了，更新状态为completed
        recipe.status = "completed"
        db.commit()

        async def completed_generator():
            yield f"data: {json.dumps({'type': 'all_completed', 'recipe_id': recipe_id}, ensure_ascii=False)}\n\n"
        return StreamingResponse(
            completed_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )

    # 获取已生成菜品名称列表，用于去重
    generated_dish_names = [d.dish_name for d in generated_details]

    # 使用流式生成函数
    generator = generate_next_day_stream(
        recipe_id=recipe_id,
        day=next_day,
        baby=baby,
        generated_dish_names=generated_dish_names,
        db=db
    )

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/generate-step-by-step")
async def generate_recipe_step_by_step(
    request: RecipeGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    分步生成一周食谱 - 按天生成模式
    使用Server-Sent Events，按天流式返回：
    - started: 已创建recipe记录
    - day_started: 开始生成第N天，包含day字段
    - day_done: 第N天所有菜品生成完成，包含details(菜品数组)、failed_meals(失败餐次数组)
    - finished: 全部7天完成，包含recipe_id和total_dishes
    - error: 发生错误
    """
    # 验证宝宝信息
    baby = db.query(Baby).filter(
        Baby.id == request.baby_id,
        Baby.user_id == current_user.id
    ).first()

    if not baby:
        raise HTTPException(status_code=404, detail="Baby not found")

    # 计算本周开始日期（周一）
    today = datetime.now().date()
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday)
    week_start_datetime = datetime.combine(week_start, datetime.min.time())

    # 先创建空Recipe记录，状态为generating
    recipe = Recipe(
        baby_id=baby.id,
        user_id=current_user.id,
        week_start_date=week_start_datetime,
        status="generating"
    )
    db.add(recipe)
    db.commit()
    db.refresh(recipe)

    # 包装生成器，先发送started事件
    async def final_generator():
        try:
            # 发送started事件
            yield f"data: {json.dumps({'type': 'started', 'recipe_id': recipe.id})}\n\n"

            # 调用分步生成主函数
            async for event in generate_weekly_recipe_step_by_step(baby, recipe.id, db):
                yield event
        except Exception as e:
            logger.error(f"Error in step-by-step generation: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': '食谱生成失败，请重试'})}\n\n"

    return StreamingResponse(
        final_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
