"""
营养需求计算服务
"""
from app.models import Baby
from typing import Dict


def calculate_nutrition_requirements(baby: Baby) -> Dict:
    """
    根据宝宝信息计算营养需求
    
    参考标准：
    - WHO 婴幼儿营养指南
    - 中国营养学会 0-2岁婴幼儿喂养指南
    """
    age_months = baby.age_months
    
    # 基础营养需求（根据月龄）
    if age_months < 6:
        # 0-6个月：主要靠母乳/配方奶
        return {
            "calories_per_day": None,  # 主要来自奶
            "protein_g": None,
            "fat_g": None,
            "carbs_g": None,
            "iron_mg": 0.27,  # 来自母乳或配方奶
            "calcium_mg": 200,
            "vitamin_d_iu": 400
        }
    elif age_months < 12:
        # 6-12个月：辅食补充
        # 能量需求：约800-1000 kcal/天（包括奶和辅食）
        # 辅食部分约占30-50%
        calories_from_food = 300  # 辅食部分
        return {
            "calories_per_day": calories_from_food,
            "protein_g": 15,  # 辅食部分约5-8g
            "fat_g": 20,  # 辅食部分约5-10g
            "carbs_g": 80,  # 辅食部分约30-50g
            "iron_mg": 10,  # 关键！需要强化铁
            "calcium_mg": 400,
            "vitamin_d_iu": 400
        }
    else:
        # 12-24个月：更多依赖辅食
        calories_from_food = 600  # 辅食部分
        return {
            "calories_per_day": calories_from_food,
            "protein_g": 20,  # 辅食部分约10-15g
            "fat_g": 30,  # 辅食部分约15-20g
            "carbs_g": 120,  # 辅食部分约60-80g
            "iron_mg": 7,
            "calcium_mg": 600,
            "vitamin_d_iu": 600
        }
