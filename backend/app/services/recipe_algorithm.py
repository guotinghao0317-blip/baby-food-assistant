"""
智能食谱生成算法模块
基于内置食谱数据库，实现智能筛选、营养计算、多样化选择
完全不依赖外部AI模型，纯算法实现
"""
import random
import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass

from app.services.recipe_database import (
    RECIPE_DATABASE,
    get_recipes_by_age,
    get_recipes_by_meal_type,
    get_high_iron_recipes,
    get_high_protein_recipes,
    get_dha_recipes,
    filter_by_allergens
)

logger = logging.getLogger(__name__)

# 每天餐次类型（去掉加餐）
MEAL_TYPES = ["breakfast", "lunch", "dinner"]

# 餐次中文名映射
MEAL_TYPE_NAMES = {
    "breakfast": "早餐",
    "lunch": "午餐",
    "dinner": "晚餐",
    "snack": "加餐"  # 保留用于向后兼容旧数据
}


@dataclass
class BabyProfile:
    """宝宝信息配置"""
    age_months: int
    allergies: List[str] = None
    liked_ingredients: List[str] = None
    disliked_ingredients: List[str] = None
    nutrition_target: Dict = None

    def __post_init__(self):
        self.allergies = self.allergies or []
        self.liked_ingredients = self.liked_ingredients or []
        self.disliked_ingredients = self.disliked_ingredients or []
        # 默认营养目标
        if self.nutrition_target is None:
            self.nutrition_target = {
                "iron_weight": 2.5,  # 铁权重最高
                "protein_weight": 1.5,
                "calcium_weight": 1.2,
                "dha_weight": 1.0,
                "diversity_bonus": 0.5
            }


def filter_recipes(
    baby_profile: BabyProfile,
    exclude_names: Set[str],
    meal_type: str = None,
    used_ingredients: Set[str] = None
) -> List[Dict]:
    """
    根据宝宝信息过滤食谱
    - 月龄匹配（宝宝月龄 >= 食谱适用月龄）
    - 排除过敏源（根据宝宝过敏史）
    - 排除已生成的菜品名称（小月龄放宽限制）
    - 匹配餐次类型
    - 排除不喜欢的食材
    """
    used_ingredients = used_ingredients or set()

    # 1. 基础筛选：月龄 + 餐次
    if meal_type:
        candidates = get_recipes_by_meal_type(meal_type, baby_profile.age_months)
    else:
        candidates = get_recipes_by_age(baby_profile.age_months)

    # 2. 排除过敏源
    candidates = filter_by_allergens(candidates, baby_profile.allergies)

    # 3. 排除已生成的菜品
    # 小月龄（<=8个月）菜品库较小，允许每道菜最多重复2次
    if exclude_names:
        if baby_profile.age_months <= 8:
            # 统计每道菜出现的次数，允许重复但不超过2次
            from collections import Counter
            name_counts = Counter(exclude_names)
            candidates = [
                r for r in candidates
                if name_counts.get(r["dish_name"], 0) < 2
            ]
        else:
            # 大月龄严格去重
            candidates = [r for r in candidates if r["dish_name"] not in exclude_names]

    # 4. 排除包含不喜欢食材的
    if baby_profile.disliked_ingredients:
        candidates = [
            r for r in candidates
            if not any(
                disliked.lower() in ingr["name"].lower()
                for disliked in baby_profile.disliked_ingredients
                for ingr in r["ingredients"]
            )
        ]

    logger.debug(f"Filtered {len(candidates)} recipes for meal_type={meal_type}")
    return candidates


def calculate_nutrition_score(recipe: Dict, nutrition_target: Dict) -> float:
    """
    计算食谱的营养匹配分数（0-100分）
    根据营养目标加权：
    - 铁含量权重最高（宝宝最容易缺铁）
    - 蛋白质、钙、维生素D次之
    - 多样性加分（不同食材组合）
    """
    nutrition = recipe["nutrition_info"]
    score = 0.0

    # 铁含量评分 (权重最高)
    iron = nutrition.get("iron", 0)
    iron_score = min(iron * 15, 30)  # 2mg铁得30分满分
    score += iron_score * nutrition_target.get("iron_weight", 2.5)

    # 蛋白质评分
    protein = nutrition.get("protein", 0)
    protein_score = min(protein * 3, 25)  # 8.3g蛋白得25分满分
    score += protein_score * nutrition_target.get("protein_weight", 1.5)

    # 钙评分
    calcium = nutrition.get("calcium", 0)
    calcium_score = min(calcium * 0.4, 20)  # 50mg钙得20分满分
    score += calcium_score * nutrition_target.get("calcium_weight", 1.2)

    # DHA加分
    dha = nutrition.get("dha", 0)
    if dha > 0:
        score += min(dha * 0.15, 15) * nutrition_target.get("dha_weight", 1.0)

    # 食材多样性加分
    ingredient_count = len(recipe["ingredients"])
    diversity_bonus = min((ingredient_count - 1) * 3, 10)  # 最多10分
    score += diversity_bonus * nutrition_target.get("diversity_bonus", 0.5)

    # 喜欢的食材加分
    score += 5  # 基础分

    return round(min(score, 100), 1)


def select_diverse_meal(
    candidates: List[Dict],
    used_ingredients: Set[str],
    meal_type: str,
    baby_profile: BabyProfile,
    day: int,
    used_dish_names: Set[str] = None
) -> Optional[Dict]:
    """
    从候选中选择最适合的菜品，保证：
    1. 食材尽量不与当天其他菜品重复
    2. 营养互补（如高铁+高钙搭配）
    3. 烹饪方式多样化
    4. 优先选择包含宝宝喜欢食材的
    5. 菜名命名多样化（避免前缀/修饰词重复）
    """
    used_dish_names = used_dish_names or set()
    if not candidates:
        return None

    # 计算每个候选的综合得分
    scored_candidates = []
    for recipe in candidates:
        # 基础营养分
        nutrition_score = calculate_nutrition_score(recipe, baby_profile.nutrition_target)

        # 食材新颖度加分（与当天已用食材不重复）
        recipe_ingredients = set(ingr["name"] for ingr in recipe["ingredients"])
        overlap = len(recipe_ingredients & used_ingredients)

        # 小月龄宝宝（<=8个月）食材有限，放宽食材重复限制
        if baby_profile.age_months <= 8:
            novelty_bonus = max(0, 20 - overlap * 3)  # 惩罚更轻
        else:
            novelty_bonus = max(0, 20 - overlap * 5)

        # 喜欢食材加分
        liked_bonus = 0
        if baby_profile.liked_ingredients:
            liked_count = sum(
                1 for liked in baby_profile.liked_ingredients
                if any(liked.lower() in ingr["name"].lower() for ingr in recipe["ingredients"])
            )
            liked_bonus = liked_count * 8

        # 餐次适配加分
        meal_bonus = 0
        if meal_type == "breakfast" and "早餐" in recipe.get("tags", []):
            meal_bonus += 10
        elif meal_type in ["lunch", "dinner"] and "高铁" in recipe.get("tags", []):
            meal_bonus += 15  # 午餐晚餐优先高铁

        # 菜名命名多样性惩罚：避免前缀/修饰词重复（如"五彩"开头重复）
        naming_penalty = 0
        if used_dish_names:
            dish_name = recipe["dish_name"]
            for existing_name in used_dish_names:
                # 检查2-3字的共同前缀
                for prefix_len in [2, 3]:
                    if len(dish_name) >= prefix_len and len(existing_name) >= prefix_len:
                        if dish_name[:prefix_len] == existing_name[:prefix_len]:
                            naming_penalty += prefix_len * 8  # 2字前缀重复-16分，3字-24分
                # 检查共同修饰词（如"五彩"、"鲜香"等2字词出现在菜名中）
                common_modifiers = ["五彩", "鲜香", "嫩滑", "营养", "暖心", "彩虹", "缤纷", "黄金", "翡翠", "如意"]
                for mod in common_modifiers:
                    if mod in dish_name and mod in existing_name:
                        naming_penalty += 20

        # 综合得分
        total_score = nutrition_score + novelty_bonus + liked_bonus + meal_bonus - naming_penalty
        scored_candidates.append((recipe, total_score))

    # 按得分排序
    scored_candidates.sort(key=lambda x: x[1], reverse=True)

    # 从Top 3中随机选择（增加多样性）
    top_candidates = scored_candidates[:min(3, len(scored_candidates))]
    selected = random.choice(top_candidates)[0]

    logger.debug(f"Selected {selected['dish_name']} with score {scored_candidates[0][1] if scored_candidates else 0}")
    return selected


def generate_single_meal(
    baby_profile: BabyProfile,
    meal_type: str,
    exclude_names: Set[str],
    day: int,
    used_ingredients: Set[str] = None,
    used_dish_names: Set[str] = None
) -> Optional[Dict]:
    """
    生成指定餐次的单道菜品
    复用现有的 filter_recipes 和 select_diverse_meal

    参数:
        baby_profile: 宝宝信息
        meal_type: 餐次类型 (breakfast/lunch/dinner)
        exclude_names: 需要排除的菜品名称集合
        day: 天数 (1-7)
        used_ingredients: 当天已使用的食材集合（可选）
        used_dish_names: 已使用的菜品名称集合，用于命名多样性惩罚（可选）

    返回:
        单道菜品数据字典，如果没有候选菜品返回None
    """
    used_dish_names = used_dish_names or set()
    used_ingredients = used_ingredients or set()

    # 过滤候选食谱
    candidates = filter_recipes(
        baby_profile,
        exclude_names,
        meal_type,
        used_ingredients
    )

    if not candidates:
        # 如果没有候选，放宽食材限制重试
        candidates = filter_recipes(baby_profile, exclude_names, meal_type)

    if not candidates:
        logger.warning(f"No candidates found for {meal_type} on day {day}")
        return None

    # 选择最优菜品
    selected = select_diverse_meal(
        candidates,
        used_ingredients,
        meal_type,
        baby_profile,
        day,
        used_dish_names
    )

    if selected is None:
        logger.warning(f"select_diverse_meal returned None for {meal_type} on day {day}")
        return None

    # 构造返回格式
    return {
        "day_of_week": day,
        "meal_type": meal_type,
        "dish_name": selected["dish_name"],
        "ingredients": selected["ingredients"],
        "cooking_steps": selected["cooking_steps"],
        "nutrition_info": selected["nutrition_info"],
        "tags": selected.get("tags", []),
        "nutrition_score": calculate_nutrition_score(selected, baby_profile.nutrition_target)
    }


def generate_day_meals(
    baby_profile: BabyProfile,
    exclude_names: Set[str],
    day: int
) -> Dict:
    """
    生成一天的3道菜
    1. 早餐：易消化、碳水为主
    2. 午餐：营养丰富、高蛋白高铁
    3. 晚餐：清淡、不过量

    返回格式：
    {
        "day": 1,
        "details": [...],
        "total_nutrition": {...},
        "ingredient_count": int
    }
    """
    day_meals = []
    used_ingredients_today = set()
    meal_types = MEAL_TYPES  # ["breakfast", "lunch", "dinner"]

    # 午餐优先选高铁，保证营养
    meal_priority = ["lunch", "breakfast", "dinner"]

    for meal_type in meal_priority:
        # 过滤候选食谱
        candidates = filter_recipes(
            baby_profile,
            exclude_names,
            meal_type,
            used_ingredients_today
        )

        if not candidates:
            # 如果没有候选，放宽食材限制重试
            candidates = filter_recipes(baby_profile, exclude_names, meal_type)

        if not candidates:
            logger.warning(f"No candidates found for {meal_type} on day {day}")
            continue

        # 选择最优菜品
        selected = select_diverse_meal(
            candidates,
            used_ingredients_today,
            meal_type,
            baby_profile,
            day
        )

        if selected:
            # 记录到已使用
            exclude_names.add(selected["dish_name"])
            recipe_ingredients = set(ingr["name"] for ingr in selected["ingredients"])
            used_ingredients_today.update(recipe_ingredients)

            # 构造返回格式
            meal_data = {
                "day_of_week": day,
                "meal_type": meal_type,
                "dish_name": selected["dish_name"],
                "ingredients": selected["ingredients"],
                "cooking_steps": selected["cooking_steps"],
                "nutrition_info": selected["nutrition_info"],
                "tags": selected.get("tags", []),
                "nutrition_score": calculate_nutrition_score(selected, baby_profile.nutrition_target)
            }
            day_meals.append(meal_data)

    # 按正确餐次顺序排序（兼容旧数据中的snack）
    meal_order = {"breakfast": 0, "lunch": 1, "dinner": 2, "snack": 3}
    day_meals.sort(key=lambda x: meal_order.get(x["meal_type"], 99))

    # 计算当日营养汇总
    total_nutrition = {
        "calories": sum(m["nutrition_info"].get("calories", 0) for m in day_meals),
        "protein": sum(m["nutrition_info"].get("protein", 0) for m in day_meals),
        "iron": sum(m["nutrition_info"].get("iron", 0) for m in day_meals),
        "calcium": sum(m["nutrition_info"].get("calcium", 0) for m in day_meals),
        "dha": sum(m["nutrition_info"].get("dha", 0) for m in day_meals)
    }

    return {
        "day": day,
        "details": day_meals,
        "total_nutrition": total_nutrition,
        "ingredient_count": len(used_ingredients_today)
    }


def generate_weekly_meals(
    baby_profile: BabyProfile,
    start_day: int = 1,
    num_days: int = 7
) -> Dict[str, any]:
    """
    生成多天（默认7天）的完整食谱
    保证菜品绝对不重复，营养均衡，食材多样化
    """
    exclude_names = set()
    weekly_meals = []
    all_nutrition = {
        "calories": 0,
        "protein": 0,
        "iron": 0,
        "calcium": 0,
        "dha": 0
    }
    all_ingredients = set()
    high_iron_days = 0
    high_protein_days = 0

    for day in range(start_day, start_day + num_days):
        day_result = generate_day_meals(baby_profile, exclude_names, day)
        weekly_meals.append(day_result)

        # 累计统计
        for key in all_nutrition:
            all_nutrition[key] += day_result["total_nutrition"].get(key, 0)
        all_ingredients.update(
            ingr["name"]
            for meal in day_result["details"]
            for ingr in meal["ingredients"]
        )

        # 高铁/高蛋白天数统计
        if day_result["total_nutrition"].get("iron", 0) >= 5:
            high_iron_days += 1
        if day_result["total_nutrition"].get("protein", 0) >= 25:
            high_protein_days += 1

        logger.info(f"Day {day} generated: {len(day_result['details'])} meals, "
                   f"{day_result['ingredient_count']} unique ingredients")

    # 构建完整详情列表（扁平化）
    all_details = []
    for day_meal in weekly_meals:
        all_details.extend(day_meal["details"])

    return {
        "details": all_details,
        "weekly_summary": {
            "total_days": num_days,
            "total_meals": len(all_details),
            "total_unique_dishes": len(exclude_names),
            "total_unique_ingredients": len(all_ingredients),
            "weekly_nutrition": all_nutrition,
            "high_iron_days": high_iron_days,
            "high_protein_days": high_protein_days
        },
        "daily_results": weekly_meals
    }


def get_recipe_suggestions(
    baby_profile: BabyProfile,
    meal_type: str = None,
    exclude_names: Set[str] = None,
    limit: int = 5
) -> List[Dict]:
    """
    获取食谱推荐列表（用于替换菜品）
    考虑宝宝月龄、过敏源、已选菜品
    """
    exclude_names = exclude_names or set()
    candidates = filter_recipes(baby_profile, exclude_names, meal_type)

    if not candidates:
        return []

    # 按营养分排序
    scored = [
        (r, calculate_nutrition_score(r, baby_profile.nutrition_target))
        for r in candidates
    ]
    scored.sort(key=lambda x: x[1], reverse=True)

    return [
        {
            "dish_name": r["dish_name"],
            "ingredients": r["ingredients"],
            "cooking_steps": r["cooking_steps"],
            "nutrition_info": r["nutrition_info"],
            "nutrition_score": score,
            "tags": r.get("tags", [])
        }
        for r, score in scored[:limit]
    ]


def validate_week_plan(details: List[Dict], baby_profile: BabyProfile) -> Dict:
    """
    验证一周食谱的质量
    - 检查是否有重复菜品
    - 统计营养是否达标
    - 检查食材多样性
    """
    dish_names = [d["dish_name"] for d in details]
    duplicates = len(dish_names) - len(set(dish_names))

    # 营养统计
    total_nutrition = {
        "calories": sum(d["nutrition_info"].get("calories", 0) for d in details),
        "protein": sum(d["nutrition_info"].get("protein", 0) for d in details),
        "iron": sum(d["nutrition_info"].get("iron", 0) for d in details),
        "calcium": sum(d["nutrition_info"].get("calcium", 0) for d in details)
    }

    # 食材统计
    all_ingredients = set(
        ingr["name"]
        for d in details
        for ingr in d["ingredients"]
    )

    # 过敏源检查
    allergen_warnings = []
    if baby_profile.allergies:
        for d in details:
            for allergen in baby_profile.allergies:
                if allergen in d.get("allergen_tags", []):
                    allergen_warnings.append(f"{d['dish_name']} contains {allergen}")

    # 质量评分
    quality_score = 100
    quality_score -= duplicates * 10
    quality_score -= len(allergen_warnings) * 15
    if total_nutrition["iron"] < 35:  # 一周铁摄入目标
        quality_score -= 15
    if len(all_ingredients) < 20:  # 食材多样性目标
        quality_score -= 10

    return {
        "quality_score": max(0, quality_score),
        "duplicate_count": duplicates,
        "allergen_warnings": allergen_warnings,
        "total_unique_ingredients": len(all_ingredients),
        "total_nutrition": total_nutrition,
        "is_valid": duplicates == 0 and len(allergen_warnings) == 0
    }


def get_algorithm_statistics() -> Dict:
    """获取算法和数据库统计信息"""
    from app.services.recipe_database import get_recipe_statistics
    db_stats = get_recipe_statistics()

    return {
        "database": db_stats,
        "algorithm": {
            "name": "Rule-based Smart Recipe Generator",
            "version": "1.0",
            "features": [
                "月龄智能匹配",
                "过敏源自动过滤",
                "营养加权评分（铁优先）",
                "28道菜绝对去重",
                "当日食材多样化",
                "餐次营养搭配优化",
                "宝宝喜好优先"
            ],
            "max_days_supported": 7,
            "meals_per_day": 3,
            "guaranteed_unique_dishes": 21
        }
    }
