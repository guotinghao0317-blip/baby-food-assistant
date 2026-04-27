"""
菜品缓存降级服务
当火山引擎API不可用时，从数据库按分类随机采样菜品
所有生成的菜品已经保存在RecipeDetail表中，直接复用
"""
import logging
import random
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import not_
from app.models import RecipeDetail

logger = logging.getLogger(__name__)


class DishCacheService:
    """菜品缓存服务，处理降级随机采样"""

    def __init__(self, db: Session):
        self.db = db

    def random_sample_dish(
        self,
        nutrition_type: str,
        exclude_dish_ids: List[int] = None
    ) -> Optional[Dict]:
        """
        按营养类型随机采样一道菜品
        - nutrition_type: 营养类型分类 (iron_red_meat, protein_poultry, seafood_fish, porridge, vegetable_fruit, iron_rice)
        - exclude_dish_ids: 排除已使用过的菜品ID，避免重复
        """
        from app.services.dish_replacer import classify_dish_nutrition_type

        all_dishes = self.db.query(RecipeDetail).all()

        # 分类过滤
        exclude_dish_ids = exclude_dish_ids or []
        candidates = [
            dish for dish in all_dishes
            if classify_dish_nutrition_type(dish) == nutrition_type
            and dish.id not in exclude_dish_ids
        ]

        if not candidates:
            # 如果该分类没有找到，尝试不排除（可能排除太多了）
            candidates = [
                dish for dish in all_dishes
                if classify_dish_nutrition_type(dish) == nutrition_type
            ]

        if not candidates:
            return None

        # 随机选择一道
        selected = random.choice(candidates)
        return self._dish_to_dict(selected)

    def random_sample_dishes_by_meal(
        self,
        day_of_week: int,
        meal_type: str,
        exclude_ids: List[int] = None,
        exclude_names: List[str] = None
    ) -> Dict:
        """
        按餐次随机采样一道菜品
        用于完整7天生成降级
        - 保持餐次不变（早餐还是早餐）
        - 根据餐次猜测营养类型，保证营养均衡
        - 排除已使用的ID和菜名
        """
        from app.services.dish_replacer import classify_dish_nutrition_type

        exclude_ids = exclude_ids or []
        exclude_names = exclude_names or []

        # 先尝试直接按餐次过滤
        query = self.db.query(RecipeDetail).filter(
            RecipeDetail.meal_type == meal_type
        )
        if exclude_ids:
            query = query.filter(not_(RecipeDetail.id.in_(exclude_ids)))

        all_dishes = query.all()

        # 按名称过滤
        if exclude_names:
            all_dishes = [d for d in all_dishes if d.dish_name not in exclude_names]

        if not all_dishes:
            # fallback: 根据餐次猜大概营养类型分类
            all_dishes_all = self.db.query(RecipeDetail).all()
            # 排除ID和名称
            all_dishes_all = [d for d in all_dishes_all if d.id not in exclude_ids and d.dish_name not in exclude_names]

            if meal_type in ["breakfast"]:
                # 早餐多是粥/米糊
                candidates = [
                    d for d in all_dishes_all
                    if classify_dish_nutrition_type(d) in ["porridge", "iron_rice"]
                ]
            elif meal_type in ["lunch", "dinner"]:
                # 午餐晚餐多是主菜
                candidates = [
                    d for d in all_dishes_all
                    if classify_dish_nutrition_type(d) in ["iron_red_meat", "protein_poultry", "seafood_fish"]
                ]
            else:
                # 加餐多是蔬果
                candidates = [
                    d for d in all_dishes_all
                    if classify_dish_nutrition_type(d) == "vegetable_fruit"
                ]

            if not candidates:
                candidates = all_dishes_all

            if not candidates:
                # 极端情况，返回任意一道（排除已使用的ID和名称）
                query = self.db.query(RecipeDetail)
                if exclude_ids:
                    query = query.filter(not_(RecipeDetail.id.in_(exclude_ids)))
                all_dishes_candidates = query.all()
                if exclude_names:
                    all_dishes_candidates = [d for d in all_dishes_candidates if d.dish_name not in exclude_names]
                selected = all_dishes_candidates[0] if all_dishes_candidates else None
                # 注意：这里不再fallback到不排除名称的情况！
                # 如果排除后还是没有，selected仍然是None，会触发下面的默认值返回
            else:
                selected = random.choice(candidates)
        else:
            selected = random.choice(all_dishes)

        # 最后安全检查：selected仍然可能为None
        # 比如数据库为空，或者所有候选都被排除了
        if selected is None:
            logger.warning(f"No dish found for meal_type={meal_type}, returning default")
            return {
                "day_of_week": day_of_week,
                "meal_type": meal_type,
                "dish_name": "南瓜小米粥",
                "ingredients": [{"name": "南瓜", "amount": "50g"}, {"name": "小米", "amount": "30g"}],
                "cooking_steps": [{"step": 1, "description": "南瓜蒸熟，小米煮粥，混合均匀"}],
                "nutrition_info": {"calories": 80, "protein": 2.5, "iron": 1.2}
            }

        return self._dish_to_dict(selected)

    def sample_weekly_recipe(
        self,
        exclude_ids: List[int] = None
    ) -> Dict[str, List[Dict]]:
        """
        采样生成完整7天食谱降级
        每天4餐 × 7天 = 28道菜
        每道菜排除已选过的ID，避免重复
        """
        details = []
        used_ids = set(exclude_ids or [])

        for day in range(1, 8):
            for meal_type in ["breakfast", "lunch", "dinner", "snack"]:
                dish = self.random_sample_dishes_by_meal(
                    day_of_week=day,
                    meal_type=meal_type,
                    exclude_ids=list(used_ids)
                )
                # 确保day_of_week和meal_type正确
                dish["day_of_week"] = day
                dish["meal_type"] = meal_type
                details.append(dish)
                if "id" in dish:
                    used_ids.add(dish["id"])

        return {
            "details": details
        }

    def sample_single_day(
        self,
        day_of_week: int,
        exclude_ids: List[int] = None,
        exclude_names: List[str] = None
    ) -> Dict[str, List[Dict]]:
        """
        采样生成单一天的食谱降级
        一天4道菜，排除已选过的ID和名称，避免重复
        """
        details = []
        used_ids = set(exclude_ids or [])
        used_names = set(exclude_names or [])

        logger.info(f"Cache sampling for day {day_of_week}, exclude_ids count={len(used_ids)}, exclude_names count={len(used_names)}")
        logger.debug(f"Excluded names: {list(used_names)[:10]}...")

        for meal_type in ["breakfast", "lunch", "dinner", "snack"]:
            dish = self.random_sample_dishes_by_meal(
                day_of_week=day_of_week,
                meal_type=meal_type,
                exclude_ids=list(used_ids),
                exclude_names=list(used_names)
            )
            # 确保day_of_week和meal_type正确
            dish["day_of_week"] = day_of_week
            dish["meal_type"] = meal_type

            # 严格检查：如果菜品名称在排除列表中，记录警告但仍然添加（后续会被上层去重过滤）
            if dish["dish_name"] in used_names:
                logger.warning(f"Cache sampling returned duplicate dish: {dish['dish_name']} for meal {meal_type}")

            details.append(dish)
            if "id" in dish:
                used_ids.add(dish["id"])
            if "dish_name" in dish:
                used_names.add(dish["dish_name"])

        logger.info(f"Cache sampling for day {day_of_week} completed: {len(details)} dishes")
        logger.debug(f"Sampled dish names: {[d['dish_name'] for d in details]}")

        return {
            "day_of_week": day_of_week,
            "details": details
        }

    def get_statistics(self) -> Dict[str, int]:
        """获取缓存统计信息（用于监控）"""
        total = self.db.query(RecipeDetail).count()
        return {"total_dishes": total}

    def _dish_to_dict(self, dish: RecipeDetail) -> Dict:
        """将RecipeDetail转换为字典格式"""
        return {
            "day_of_week": dish.day_of_week,
            "meal_type": dish.meal_type,
            "dish_name": dish.dish_name,
            "ingredients": dish.ingredients,
            "cooking_steps": dish.cooking_steps,
            "nutrition_info": dish.nutrition_info,
            "id": dish.id
        }
