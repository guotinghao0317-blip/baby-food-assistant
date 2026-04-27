"""
食谱生成服务
**优先使用火山引擎 CodingPlan API 动态生成**，失败时自动降级到内置算法

特点：
- 基于 CodingPlan (火山引擎大模型) 动态生成，每次内容不同
- 根据宝宝信息个性化定制（月龄、过敏源、进食能力等）
- 失败时自动降级到内置算法，保证可用性
- 内置100+道宝宝辅食数据库作为降级方案
- 月龄智能匹配，过敏源自动过滤
- 28道菜绝对不重复
- 营养均衡计算（铁优先）
- 食材多样化保证
- 支持流式输出，逐步返回生成结果
- 支持分步生成，一天一天生成
"""
import json
import logging
import asyncio
from typing import Dict, List, AsyncGenerator, Optional

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session
from app.models import Baby, NutritionRequirement, RecipeDetail

# 火山引擎 CodingPlan API 客户端
from app.services.volcengine_client import volcengine_client, is_api_available

# 导入新的智能算法模块（降级使用）
from app.services.recipe_algorithm import (
    BabyProfile,
    generate_day_meals,
    generate_weekly_meals,
    get_recipe_suggestions,
    validate_week_plan,
    calculate_nutrition_score,
    generate_single_meal,
    MEAL_TYPES
)

# 生成源标记
GENERATION_SOURCE_CODINGPLAN = "codingplan"  # 火山引擎动态生成
GENERATION_SOURCE_ALGORITHM = "algorithm"    # 内置算法降级


def clean_json_output(content: str) -> str:
    """
    清理JSON输出（保留用于向后兼容）
    """
    start = content.find('{')
    end = content.rfind('}')
    if start != -1 and end != -1 and end > start:
        return content[start:end+1]
    return content


def baby_to_profile(baby: Baby, nutrition: NutritionRequirement = None) -> BabyProfile:
    """
    将Baby对象转换为算法使用的BabyProfile
    """
    nutrition_target = None
    if nutrition:
        nutrition_target = {
            "iron_weight": 2.5,
            "protein_weight": 1.5,
            "calcium_weight": 1.2,
            "target_calories": nutrition.calories_per_day or 400
        }

    return BabyProfile(
        age_months=baby.age_months,
        allergies=baby.allergies or [],
        liked_ingredients=baby.liked_ingredients or [],
        disliked_ingredients=baby.disliked_ingredients or [],
        nutrition_target=nutrition_target
    )


async def generate_weekly_recipe(baby: Baby, db: Session) -> Dict:
    """
    生成一周食谱
    **优先使用火山引擎 CodingPlan API**，失败时自动降级到内置算法
    """
    # 获取营养需求
    nutrition = db.query(NutritionRequirement).filter(
        NutritionRequirement.baby_id == baby.id
    ).first()

    baby_profile = baby_to_profile(baby, nutrition)

    logger.info(f"Generating weekly recipe for {baby.age_months} months baby")
    logger.info(f"Allergies: {baby.allergies}, Liked: {baby.liked_ingredients}")

    # 第一步：优先尝试使用 CodingPlan API 动态生成
    if is_api_available():
        logger.info("[CodingPlan] 尝试使用火山引擎动态生成...")
        result = await volcengine_client.generate_weekly_recipe(
            baby=baby,
            nutrition=nutrition,
            start_day=1,
            num_days=7
        )

        if result and "details" in result:
            logger.info(f"[CodingPlan] SUCCESS: 成功生成 {len(result['details'])} 道菜")
            # 标记生成源
            result["generation_source"] = GENERATION_SOURCE_CODINGPLAN
            return result
        else:
            logger.warning("[CodingPlan] API调用失败，将降级使用内置算法")
    else:
        logger.warning("[CodingPlan] API未配置，使用内置算法")

    # 第二步：降级到内置算法
    logger.info(f"[Algorithm] 使用内置智能算法生成")
    result = generate_weekly_meals(baby_profile, start_day=1, num_days=7)

    logger.info(f"[Algorithm] Generated {len(result['details'])} dishes total")

    # 清理输出格式
    for detail in result["details"]:
        detail.pop("nutrition_score", None)
        detail.pop("tags", None)

    result["generation_source"] = GENERATION_SOURCE_ALGORITHM
    return result


async def generate_weekly_recipe_stream(
    baby: Baby,
    db: Session
) -> AsyncGenerator[str, None]:
    """
    流式生成一周食谱
    逐天返回生成结果，让用户逐步看到内容
    模拟流式输出效果，实际上使用内置算法
    """
    # 获取营养需求
    nutrition = db.query(NutritionRequirement).filter(
        NutritionRequirement.baby_id == baby.id
    ).first()

    baby_profile = baby_to_profile(baby, nutrition)

    logger.info(f"[Algorithm Stream] Generating weekly recipe stream")

    # 分步生成每一天，模拟流式效果
    all_details = []
    exclude_names = set()

    for day in range(1, 8):
        # 模拟"正在生成"的效果
        day_result = generate_day_meals(baby_profile, exclude_names, day)
        all_details.extend(day_result["details"])

        # 模拟流式输出进度
        progress_msg = f"Day {day} generated: {len(day_result['details'])} meals"
        full_content = json.dumps({"progress": progress_msg, "current_day": day}, ensure_ascii=False)

        yield f"data: {json.dumps({'type': 'chunk', 'content': progress_msg, 'full_content': full_content}, ensure_ascii=False)}\n\n"

        # 模拟处理延迟，让用户能看到进度变化
        await asyncio.sleep(0.1)

    # 生成完成
    result = {"details": all_details}
    yield f"data: {json.dumps({'type': 'done', 'data': result}, ensure_ascii=False)}\n\n"


async def generate_replace_dish_stream(
    recipe_id: int,
    original_dish,
    baby: Baby,
    db: Session
) -> AsyncGenerator[str, None]:
    """
    生成替换菜品
    **优先使用火山引擎 CodingPlan API**，失败时自动降级到内置算法
    """
    # 获取营养需求
    nutrition = db.query(NutritionRequirement).filter(
        NutritionRequirement.baby_id == baby.id
    ).first()

    baby_profile = baby_to_profile(baby, nutrition)

    logger.info(f"[Replace] 替换菜品: {original_dish.dish_name}, 餐次: {original_dish.meal_type}")

    # 获取已存在的菜品名称，避免重复
    existing_dishes = db.query(RecipeDetail).filter(
        RecipeDetail.recipe_id == recipe_id
    ).all()
    exclude_names = list(set(d.dish_name for d in existing_dishes))
    exclude_names.append(original_dish.dish_name)

    # 第一步：优先尝试使用 CodingPlan API 动态生成
    new_dish_data = None

    if is_api_available():
        logger.info(f"[CodingPlan Replace] 尝试使用火山引擎动态生成替换菜品...")

        # 调用流式替换API
        full_content = ""
        async for chunk in volcengine_client.generate_replace_dish_stream(
            original_dish=original_dish,
            baby=baby,
            exclude_names=exclude_names
        ):
            # 转发流式输出
            yield chunk

            # 累积内容用于最后解析
            chunk_data = json.loads(chunk.split("data: ")[1].strip())
            if chunk_data.get("type") == "done":
                # 流式完成，解析结果
                new_dish_data = chunk_data.get("data")
                if new_dish_data and "dish_name" in new_dish_data:
                    logger.info(f"[CodingPlan Replace] SUCCESS: 成功生成替换菜品: {new_dish_data['dish_name']}")
                    # 补全天和餐次信息
                    new_dish_data["day_of_week"] = original_dish.day_of_week
                    new_dish_data["meal_type"] = original_dish.meal_type

        # 检查是否成功
        if new_dish_data and "dish_name" in new_dish_data:
            # 成功，继续处理保存
            pass
        else:
            logger.warning(f"[CodingPlan Replace] 生成失败，降级使用内置算法")

    # 第二步：API不可用或失败，降级到内置算法
    if new_dish_data is None or "dish_name" not in new_dish_data:
        logger.info(f"[Algorithm Replace] 使用内置算法推荐替换菜品")

        # 获取推荐菜品
        suggestions = get_recipe_suggestions(
            baby_profile,
            meal_type=original_dish.meal_type,
            exclude_names=exclude_names,
            limit=3
        )

        if not suggestions:
            yield f"data: {json.dumps({'type': 'error', 'message': '没有找到合适的替代菜品'}, ensure_ascii=False)}\n\n"
            return

        # 选择评分最高的
        selected = suggestions[0]

        # 模拟流式输出
        yield f"data: {json.dumps({'type': 'chunk', 'content': '正在为您推荐最佳替代菜品...'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)

        new_dish_data = {
            "day_of_week": original_dish.day_of_week,
            "meal_type": original_dish.meal_type,
            "dish_name": selected["dish_name"],
            "ingredients": selected["ingredients"],
            "cooking_steps": selected["cooking_steps"],
            "nutrition_info": selected["nutrition_info"]
        }

    # 保存到数据库：删除原菜品，创建新菜品
    db.delete(original_dish)

    new_dish = RecipeDetail(
        recipe_id=recipe_id,
        **new_dish_data
    )
    db.add(new_dish)
    db.commit()

    # 返回完整的新菜品数据
    result_data = {
        "id": new_dish.id,
        **new_dish_data
    }

    logger.info(f"[Replace] 替换成功: '{original_dish.dish_name}' -> '{new_dish_data['dish_name']}'")
    yield f"data: {json.dumps({'type': 'done', 'data': result_data}, ensure_ascii=False)}\n\n"


async def generate_next_day_stream(
    recipe_id: int,
    day: int,
    baby: Baby,
    generated_dish_names: List[str],
    db: Session
) -> AsyncGenerator[str, None]:
    """
    流式生成单一天的食谱 - 按天生成模式
    **优先使用火山引擎 CodingPlan API**，失败时自动降级到内置算法

    SSE事件类型:
    - day_started: 某天开始生成
    - day_done: 某天所有菜品生成完成，包含完整菜品数据和失败餐次
    - finished: 所有7天完成
    - error: 生成错误
    """
    # 获取营养需求
    nutrition = db.query(NutritionRequirement).filter(
        NutritionRequirement.baby_id == baby.id
    ).first()

    baby_profile = baby_to_profile(baby, nutrition)

    logger.info(f"[Stream Day {day}] 开始流式生成当天食谱（按天模式）")

    # 通知前端开始生成当天
    yield f"data: {json.dumps({'type': 'day_started', 'day': day})}\n\n"

    # 清除该天已有的菜品记录，避免重新生成时因重复而失败
    existing_details = db.query(RecipeDetail).filter(
        RecipeDetail.recipe_id == recipe_id,
        RecipeDetail.day_of_week == day
    ).all()
    if existing_details:
        for detail in existing_details:
            # 从 generated_dish_names 中移除被删除菜品的名称，避免误排除
            if detail.dish_name in generated_dish_names:
                generated_dish_names.remove(detail.dish_name)
            db.delete(detail)
        db.commit()
        logger.info(f"[Stream Day {day}] 清除了 {len(existing_details)} 条已有菜品记录")

    day_saved_details: List[Dict] = []
    failed_meals: List[str] = []
    used_ingredients_today: set = set()
    mealtypes_for_day: set = set()
    total_dishes = 0

    # 逐菜生成：依次生成早餐、午餐、晚餐
    for meal_type in MEAL_TYPES:
        dish_data = None
        generation_source = GENERATION_SOURCE_CODINGPLAN

        # 第一步：优先尝试使用 CodingPlan API 流式生成单道菜
        if is_api_available():
            logger.info(f"[CodingPlan Stream Day {day} {meal_type}] 尝试使用火山引擎流式生成...")

            full_content = ""
            stream_success = False

            try:
                async for chunk in volcengine_client.generate_single_meal_stream(
                    baby=baby,
                    nutrition=nutrition,
                    meal_type=meal_type,
                    day=day,
                    exclude_dish_names=generated_dish_names
                ):
                    full_content += chunk

                # 流式完成，解析JSON
                if full_content:
                    cleaned = volcengine_client.clean_json_output(full_content)
                    parsed = json.loads(cleaned)
                    # LLM返回的格式可能有嵌套，尝试解析detail字段
                    if "detail" in parsed:
                        dish_data = parsed["detail"]
                    elif "dish_name" in parsed:
                        dish_data = parsed

                    if dish_data and "dish_name" in dish_data:
                        dish_data["day_of_week"] = day
                        dish_data["meal_type"] = meal_type
                        stream_success = True
                        logger.info(f"[CodingPlan Stream Day {day} {meal_type}] SUCCESS: 生成菜品 {dish_data.get('dish_name')}")
                    else:
                        logger.warning(f"[CodingPlan Stream Day {day} {meal_type}] 返回数据缺少dish_name字段")
            except json.JSONDecodeError as e:
                logger.warning(f"[CodingPlan Stream Day {day} {meal_type}] JSON解析失败: {e}")
            except Exception as e:
                logger.warning(f"[CodingPlan Stream Day {day} {meal_type}] 流式生成异常: {e}")

            if not stream_success:
                logger.warning(f"[CodingPlan Stream Day {day} {meal_type}] API生成失败，将降级使用内置算法")
                dish_data = None

        # 第二步：降级到内置算法
        if dish_data is None:
            generation_source = GENERATION_SOURCE_ALGORITHM
            logger.info(f"[Algorithm Stream Day {day} {meal_type}] 使用内置算法生成")

            exclude_names = set(generated_dish_names)
            dish_data = generate_single_meal(
                baby_profile, meal_type, exclude_names, day, used_ingredients_today, generated_dish_names
            )

            if dish_data is None:
                logger.warning(f"[Algorithm Stream Day {day} {meal_type}] 无法生成菜品，跳过")
                failed_meals.append(meal_type)
                continue

            if dish_data is not None:
                # 保留适当延迟，后端仍需要节奏控制
                await asyncio.sleep(0.3)

        # 数据有效性检查
        if "dish_name" not in dish_data or not dish_data["dish_name"]:
            logger.warning(f"[Stream Day {day} {meal_type}] 菜品数据无效，缺少dish_name")
            failed_meals.append(meal_type)
            continue

        # 清理算法内部字段
        dish_data.pop("nutrition_score", None)
        dish_data.pop("tags", None)
        dish_data["day_of_week"] = day
        dish_data["meal_type"] = meal_type

        # 检查菜品名称是否重复（全局去重）
        existing_dish = db.query(RecipeDetail).filter(
            RecipeDetail.recipe_id == recipe_id,
            RecipeDetail.dish_name == dish_data["dish_name"]
        ).first()

        if existing_dish:
            duplicate_name = dish_data["dish_name"]
            logger.warning(f"[Stream Day {day}] 菜品名称已存在: {duplicate_name}，跳过")
            failed_meals.append(meal_type)
            continue

        # 检查同一天同一餐次是否重复
        existing_mealtype = db.query(RecipeDetail).filter(
            RecipeDetail.recipe_id == recipe_id,
            RecipeDetail.day_of_week == day,
            RecipeDetail.meal_type == meal_type
        ).first()

        if existing_mealtype:
            existing_meal_name = existing_mealtype.dish_name
            logger.warning(f"[Stream Day {day}] 餐次 {meal_type} 已存在菜品: {existing_meal_name}，跳过")
            failed_meals.append(meal_type)
            continue

        # 保存到数据库
        detail = RecipeDetail(
            recipe_id=recipe_id,
            **dish_data
        )
        db.add(detail)
        db.flush()
        db.refresh(detail)
        db.commit()

        # 构造返回数据
        saved_detail = {
            "id": detail.id,
            **dish_data
        }
        day_saved_details.append(saved_detail)
        generated_dish_names.append(dish_data["dish_name"])
        mealtypes_for_day.add(meal_type)
        total_dishes += 1

        # 更新已使用食材（用于算法路径的后续菜品选择）
        if "ingredients" in dish_data:
            for ingr in dish_data["ingredients"]:
                used_ingredients_today.add(ingr.get("name", ""))

        logger.info(f"[Stream Day {day} {meal_type}] 保存菜品: {dish_data['dish_name']}")

        # 每道菜生成完立即推送 dish_done 事件，让前端逐菜展示
        yield f"data: {json.dumps({'type': 'dish_done', 'day': day, 'meal_type': meal_type, 'detail': saved_detail}, ensure_ascii=False)}\n\n"

    # 通知前端当天所有菜品生成完成
    # 检查是否所有天都生成完成
    day_nums = db.query(RecipeDetail.day_of_week).filter(
        RecipeDetail.recipe_id == recipe_id
    ).distinct().all()
    generated_day_set = set(d[0] for d in day_nums)
    total_generated_days = len(generated_day_set)

    from app.models import Recipe
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    all_completed = False

    if total_generated_days >= 7:
        recipe.status = "completed"
        db.commit()
        all_completed = True
        logger.info(f"[Stream Day {day}] All 7 days completed!")

    yield f"data: {json.dumps({'type': 'day_done', 'day': day, 'details': day_saved_details, 'failed_meals': failed_meals, 'all_completed': all_completed}, ensure_ascii=False)}\n\n"

    if all_completed:
        yield f"data: {json.dumps({'type': 'finished', 'recipe_id': recipe_id}, ensure_ascii=False)}\n\n"


async def generate_weekly_recipe_step_by_step(
    baby: Baby,
    recipe_id: int,
    db: Session
) -> AsyncGenerator[str, None]:
    """
    分步生成一周食谱的主函数 - 按天生成模式
    **优先使用火山引擎 CodingPlan API**，失败时自动降级到内置算法
    每天统一推送 day_started → day_done，SSE事件粒度为天级别

    通过SSE流式返回：day_started, day_done, finished, error
    """
    # 初始化已生成菜品名称列表，用于去重
    generated_dish_names: List[str] = []
    total_dishes = 0

    # 获取营养需求
    nutrition = db.query(NutritionRequirement).filter(
        NutritionRequirement.baby_id == baby.id
    ).first()

    baby_profile = baby_to_profile(baby, nutrition)

    logger.info(f"[Step-by-Step] 开始分步生成一周食谱，按天生成模式")

    try:
        # 循环生成每一天
        for day in range(1, 8):
            # 通知前端开始生成当天
            yield f"data: {json.dumps({'type': 'day_started', 'day': day})}\n\n"

            logger.info(f"[Step-by-Step Day {day}] 开始生成当天食谱")

            # 清除该天已有的菜品记录，避免重新生成时因重复而失败
            existing_details = db.query(RecipeDetail).filter(
                RecipeDetail.recipe_id == recipe_id,
                RecipeDetail.day_of_week == day
            ).all()
            if existing_details:
                for detail in existing_details:
                    # 从 generated_dish_names 中移除被删除菜品的名称，避免误排除
                    if detail.dish_name in generated_dish_names:
                        generated_dish_names.remove(detail.dish_name)
                    db.delete(detail)
                db.commit()
                logger.info(f"[Step-by-Step Day {day}] 清除了 {len(existing_details)} 条已有菜品记录")

            day_saved_details = []
            failed_meals: List[str] = []
            used_ingredients_today = set()
            mealtypes_for_day = set()

            # 逐菜生成：依次生成早餐、午餐、晚餐
            for meal_type in MEAL_TYPES:
                dish_data = None
                generation_source = GENERATION_SOURCE_CODINGPLAN

                # 第一步：优先尝试使用 CodingPlan API 流式生成单道菜
                if is_api_available():
                    logger.info(f"[CodingPlan Day {day} {meal_type}] 尝试使用火山引擎流式生成...")

                    full_content = ""
                    stream_success = False

                    try:
                        async for chunk in volcengine_client.generate_single_meal_stream(
                            baby=baby,
                            nutrition=nutrition,
                            meal_type=meal_type,
                            day=day,
                            exclude_dish_names=generated_dish_names
                        ):
                            full_content += chunk

                        # 流式完成，解析JSON
                        if full_content:
                            cleaned = volcengine_client.clean_json_output(full_content)
                            parsed = json.loads(cleaned)
                            # LLM返回的格式可能有嵌套，尝试解析detail字段
                            if "detail" in parsed:
                                dish_data = parsed["detail"]
                            elif "dish_name" in parsed:
                                dish_data = parsed

                            if dish_data and "dish_name" in dish_data:
                                dish_data["day_of_week"] = day
                                dish_data["meal_type"] = meal_type
                                stream_success = True
                                logger.info(f"[CodingPlan Day {day} {meal_type}] SUCCESS: 生成菜品 {dish_data.get('dish_name')}")
                            else:
                                logger.warning(f"[CodingPlan Day {day} {meal_type}] 返回数据缺少dish_name字段")
                    except json.JSONDecodeError as e:
                        logger.warning(f"[CodingPlan Day {day} {meal_type}] JSON解析失败: {e}")
                    except Exception as e:
                        logger.warning(f"[CodingPlan Day {day} {meal_type}] 流式生成异常: {e}")

                    if not stream_success:
                        logger.warning(f"[CodingPlan Day {day} {meal_type}] API生成失败，将降级使用内置算法")
                        dish_data = None

                # 第二步：降级到内置算法
                if dish_data is None:
                    generation_source = GENERATION_SOURCE_ALGORITHM
                    logger.info(f"[Algorithm Day {day} {meal_type}] 使用内置算法生成")

                    exclude_names = set(generated_dish_names)
                    dish_data = generate_single_meal(
                        baby_profile, meal_type, exclude_names, day, used_ingredients_today
                    )

                    if dish_data is None:
                        logger.warning(f"[Algorithm Day {day} {meal_type}] 无法生成菜品，跳过")
                        failed_meals.append(meal_type)
                        continue

                    if dish_data is not None:
                        # 保留适当延迟，后端仍需要节奏控制
                        await asyncio.sleep(0.3)

                # 数据有效性检查
                if "dish_name" not in dish_data or not dish_data["dish_name"]:
                    logger.warning(f"[Step-by-Step Day {day} {meal_type}] 菜品数据无效，缺少dish_name")
                    failed_meals.append(meal_type)
                    continue

                # 清理算法内部字段
                dish_data.pop("nutrition_score", None)
                dish_data.pop("tags", None)
                dish_data["day_of_week"] = day
                dish_data["meal_type"] = meal_type

                # 检查菜品名称是否重复（全局去重）
                existing_dish = db.query(RecipeDetail).filter(
                    RecipeDetail.recipe_id == recipe_id,
                    RecipeDetail.dish_name == dish_data["dish_name"]
                ).first()

                if existing_dish:
                    duplicate_name = dish_data["dish_name"]
                    logger.warning(f"[Step-by-Step Day {day}] 菜品名称已存在: {duplicate_name}，跳过")
                    failed_meals.append(meal_type)
                    continue

                # 检查同一天同一餐次是否重复
                existing_mealtype = db.query(RecipeDetail).filter(
                    RecipeDetail.recipe_id == recipe_id,
                    RecipeDetail.day_of_week == day,
                    RecipeDetail.meal_type == meal_type
                ).first()

                if existing_mealtype:
                    existing_meal_name = existing_mealtype.dish_name
                    logger.warning(f"[Step-by-Step Day {day}] 餐次 {meal_type} 已存在菜品: {existing_meal_name}，跳过")
                    failed_meals.append(meal_type)
                    continue

                # 保存到数据库
                detail = RecipeDetail(
                    recipe_id=recipe_id,
                    **dish_data
                )
                db.add(detail)
                db.flush()
                db.refresh(detail)
                db.commit()

                # 构造返回数据
                saved_detail = {
                    "id": detail.id,
                    **dish_data
                }
                day_saved_details.append(saved_detail)
                generated_dish_names.append(dish_data["dish_name"])
                mealtypes_for_day.add(meal_type)
                total_dishes += 1

                # 更新已使用食材（用于算法路径的后续菜品选择）
                if "ingredients" in dish_data:
                    for ingr in dish_data["ingredients"]:
                        used_ingredients_today.add(ingr.get("name", ""))

                logger.info(f"[Step-by-Step Day {day} {meal_type}] 保存菜品: {dish_data['dish_name']}")

                # 每道菜生成完立即推送 dish_done 事件，让前端逐菜展示
                yield f"data: {json.dumps({'type': 'dish_done', 'day': day, 'meal_type': meal_type, 'detail': saved_detail}, ensure_ascii=False)}\n\n"

            # 通知前端当天所有菜品生成完成
            yield f"data: {json.dumps({'type': 'day_done', 'day': day, 'details': day_saved_details, 'failed_meals': failed_meals}, ensure_ascii=False)}\n\n"

            logger.info(f"[Step-by-Step Day {day}] Saved {len(day_saved_details)} dishes, total: {total_dishes}")

        # 全部7天完成，更新状态
        from app.models import Recipe
        recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
        recipe.status = "completed"
        db.commit()

        logger.info(f"[Step-by-Step] All 7 days completed! Total dishes: {total_dishes}")

        # 验证食谱质量
        validation = validate_week_plan_from_db(recipe_id, db, baby_profile)
        logger.info(f"[Step-by-Step] Recipe quality score: {validation['quality_score']}/100")

        # 通知前端全部完成
        yield f"data: {json.dumps({'type': 'finished', 'recipe_id': recipe_id, 'total_dishes': total_dishes}, ensure_ascii=False)}\n\n"

    except Exception as e:
        logger.error(f"Error in step-by-step generation: {e}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'message': '食谱生成失败，请重试'}, ensure_ascii=False)}\n\n"


def validate_week_plan_from_db(recipe_id: int, db: Session, baby_profile: BabyProfile) -> Dict:
    """
    从数据库验证一周食谱的质量
    """
    all_dishes = db.query(RecipeDetail).filter(
        RecipeDetail.recipe_id == recipe_id
    ).all()

    dish_names = [d.dish_name for d in all_dishes]
    duplicates = len(dish_names) - len(set(dish_names))

    # 统计食材多样性
    all_ingredients = set()
    for dish in all_dishes:
        for ing in dish.ingredients:
            all_ingredients.add(ing.get("name", ""))

    # 过敏源检查
    allergen_warnings = []
    if baby_profile.allergies:
        for allergen in baby_profile.allergies:
            for dish in all_dishes:
                for ing in dish.ingredients:
                    if allergen in ing.get("name", ""):
                        allergen_warnings.append(f"{dish.dish_name} 可能包含 {allergen}")

    quality_score = 100
    quality_score -= duplicates * 10
    quality_score -= len(allergen_warnings) * 15
    if len(all_ingredients) < 20:
        quality_score -= 10

    return {
        "quality_score": max(0, quality_score),
        "duplicate_count": duplicates,
        "allergen_warnings": allergen_warnings,
        "total_unique_ingredients": len(all_ingredients),
        "total_dishes": len(all_dishes)
    }


def get_default_recipe(baby: Baby) -> Dict:
    """
    基础默认食谱（保留向后兼容）
    现在使用智能算法生成
    """
    baby_profile = baby_to_profile(baby)
    result = generate_weekly_meals(baby_profile, start_day=1, num_days=7)

    # 清理输出格式
    for detail in result["details"]:
        detail.pop("nutrition_score", None)
        detail.pop("tags", None)

    return result
