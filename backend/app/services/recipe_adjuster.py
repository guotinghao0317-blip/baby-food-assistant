"""
食谱调整服务（对话式）
重构：不依赖外部 OpenAI API，保留接口结构
"""
import json
from typing import Dict
from sqlalchemy.orm import Session
from app.models import Recipe, RecipeDetail


async def adjust_recipe(recipe: Recipe, user_message: str, db: Session) -> Dict:
    """
    根据用户反馈调整食谱

    用户消息示例：
    - "宝宝不喜欢胡萝卜"
    - "太淡了，能不能加点味道"
    - "这个吃不完，份量减少一点"

    重构说明：现在由 Claude AI 手动调整，这里返回空列表表示无自动调整
    用户可以通过 Claude 对话来生成调整后的数据
    """
    # 当前不做自动调整，返回空列表
    # 在需要时，可以由 Claude 根据用户消息生成调整后的数据
    print(f"Recipe adjustment requested: {user_message}")
    print("Please use Claude AI to manually generate adjusted recipe data")
    return {"details": []}
