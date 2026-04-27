"""
换一道菜替换服务
重构：优先调用火山引擎大模型动态生成替代菜品，失败自动降级缓存采样
根据原菜品生成一道营养相似但食材不同的替代菜品
"""
import random
from typing import Dict, List
from sqlalchemy.orm import Session
from app.models import Baby, RecipeDetail
from app.services.volcengine_client import volcengine_client
from app.services.dish_cache import DishCacheService


# 内置静态替补库（降级兜底用，当数据库没有足够数据时使用）
# 替代菜品库 - 按营养类型分类
# 每一类包含多道营养相似但食材不同的菜品
REPLACEMENT_LIBRARY = {
    # 红肉补铁类
    "iron_red_meat": [
        {
            "name": "牛肉土豆软饭",
            "ingredients": [
                {"name": "牛肉末", "amount": "30g"},
                {"name": "土豆", "amount": "60g"},
                {"name": "米饭", "amount": "40g"}
            ],
            "steps": [
                {"step": 1, "description": "土豆去皮切小丁蒸熟"},
                {"step": 2, "description": "牛肉末炒香变色"},
                {"step": 3, "description": "所有材料混合，加少量水焖一下"},
                {"step": 4, "description": "土豆压成部分泥，保留颗粒感"}
            ],
            "nutrition": {"calories": 195, "protein": 12.5, "iron": 2.8}
        },
        {
            "name": "猪肝西兰花烩饭",
            "ingredients": [
                {"name": "猪肝", "amount": "25g"},
                {"name": "西兰花", "amount": "30g"},
                {"name": "米饭", "amount": "50g"},
                {"name": "洋葱", "amount": "10g"}
            ],
            "steps": [
                {"step": 1, "description": "猪肝去筋膜洗净切小丁，用姜片去腥"},
                {"step": 2, "description": "西兰花掰小朵焯水切碎"},
                {"step": 3, "description": "热锅下洋葱炒香，加入猪肝丁炒熟"},
                {"step": 4, "description": "加入米饭和西兰花，加少量水焖5分钟"},
                {"step": 5, "description": "保持湿润软糯，颗粒细小"}
            ],
            "nutrition": {"calories": 175, "protein": 11.8, "iron": 6.2}
        },
        {
            "name": "山药牛肉碎软面",
            "ingredients": [
                {"name": "山药", "amount": "50g"},
                {"name": "牛肉末", "amount": "25g"},
                {"name": "婴儿细面条", "amount": "30g"},
                {"name": "洋葱碎", "amount": "10g"}
            ],
            "steps": [
                {"step": 1, "description": "山药去皮切小块蒸熟压成泥"},
                {"step": 2, "description": "面条掰小段煮熟"},
                {"step": 3, "description": "牛肉末加洋葱碎炒熟"},
                {"step": 4, "description": "所有材料混合，面条剪短成小段"},
                {"step": 5, "description": "保持软嫩小块状"}
            ],
            "nutrition": {"calories": 180, "protein": 10.2, "iron": 2.5}
        },
        {
            "name": "鸭血豆腐汤饭",
            "ingredients": [
                {"name": "鸭血", "amount": "30g"},
                {"name": "嫩豆腐", "amount": "40g"},
                {"name": "青菜", "amount": "15g"},
                {"name": "米饭", "amount": "30g"}
            ],
            "steps": [
                {"step": 1, "description": "鸭血、豆腐切小丁"},
                {"step": 2, "description": "水烧开，先下鸭血煮3分钟"},
                {"step": 3, "description": "加入豆腐青菜再煮2分钟"},
                {"step": 4, "description": "浇在软米饭上食用"}
            ],
            "nutrition": {"calories": 120, "protein": 8.6, "iron": 7.8}
        }
    ],

    # 白肉/禽肉高蛋白类
    "protein_poultry": [
        {
            "name": "鸡胸肉蔬菜软饭团",
            "ingredients": [
                {"name": "鸡胸肉末", "amount": "30g"},
                {"name": "胡萝卜丁", "amount": "20g"},
                {"name": "米饭", "amount": "40g"},
                {"name": "青菜碎", "amount": "15g"}
            ],
            "steps": [
                {"step": 1, "description": "鸡胸肉洗净剁成细末"},
                {"step": 2, "description": "胡萝卜、青菜切小碎块"},
                {"step": 3, "description": "鸡胸肉下锅炒熟，加入蔬菜丁一起翻炒"},
                {"step": 4, "description": "和煮熟的米饭混合均匀"},
                {"step": 5, "description": "捏成宝宝能抓握的小饭团"}
            ],
            "nutrition": {"calories": 160, "protein": 12.5, "iron": 1.8}
        },
        {
            "name": "鸡肉蘑菇焖饭",
            "ingredients": [
                {"name": "鸡胸肉", "amount": "40g"},
                {"name": "鲜蘑菇", "amount": "30g"},
                {"name": "大米", "amount": "35g"}
            ],
            "steps": [
                {"step": 1, "description": "鸡肉切小丁，蘑菇切小丁"},
                {"step": 2, "description": "鸡肉炒香，加入蘑菇翻炒"},
                {"step": 3, "description": "和大米一起放电饭煲焖熟"},
                {"step": 4, "description": "煮好后翻松，颗粒适中"}
            ],
            "nutrition": {"calories": 220, "protein": 14.6, "iron": 2.1}
        },
        {
            "name": "猪肉胡萝卜小云吞",
            "ingredients": [
                {"name": "猪瘦肉", "amount": "40g"},
                {"name": "胡萝卜", "amount": "25g"},
                {"name": "馄饨皮", "amount": "6片"}
            ],
            "steps": [
                {"step": 1, "description": "猪肉和胡萝卜一起剁成细末"},
                {"step": 2, "description": "馄饨皮切小块，包成小云吞"},
                {"step": 3, "description": "水烧开下云吞，煮5分钟至浮起"},
                {"step": 4, "description": "捞起放温，云吞皮剪碎方便食用"}
            ],
            "nutrition": {"calories": 180, "protein": 13.2, "iron": 2.1}
        },
        {
            "name": "青豆玉米烩鸡肉",
            "ingredients": [
                {"name": "鸡胸肉", "amount": "40g"},
                {"name": "青豆", "amount": "20g"},
                {"name": "玉米", "amount": "20g"},
                {"name": "米饭", "amount": "40g"}
            ],
            "steps": [
                {"step": 1, "description": "鸡肉切小丁，青豆玉米洗净"},
                {"step": 2, "description": "青豆提前焯水"},
                {"step": 3, "description": "鸡肉炒至变色，加入青豆玉米焖熟"},
                {"step": 4, "description": "烩好后浇在软米饭上"}
            ],
            "nutrition": {"calories": 205, "protein": 14.8, "iron": 1.9}
        }
    ],

    # 鱼虾水产类
    "seafood_fish": [
        {
            "name": "鳕鱼豆腐蒸蛋",
            "ingredients": [
                {"name": "鳕鱼", "amount": "30g"},
                {"name": "嫩豆腐", "amount": "40g"},
                {"name": "鸡蛋", "amount": "1个"}
            ],
            "steps": [
                {"step": 1, "description": "鳕鱼去皮去刺切小块"},
                {"step": 2, "description": "豆腐压碎"},
                {"step": 3, "description": "鸡蛋打散，加一倍温水搅匀"},
                {"step": 4, "description": "放入鳕鱼豆腐，上汽后蒸8分钟"},
                {"step": 5, "description": "蒸好后放凉切块"}
            ],
            "nutrition": {"calories": 155, "protein": 16.3, "iron": 1.5}
        },
        {
            "name": "蔬菜鱼肉粥",
            "ingredients": [
                {"name": "龙利鱼", "amount": "30g"},
                {"name": "胡萝卜", "amount": "20g"},
                {"name": "大米", "amount": "25g"},
                {"name": "青菜", "amount": "15g"}
            ],
            "steps": [
                {"step": 1, "description": "龙利鱼去刺切小丁"},
                {"step": 2, "description": "胡萝卜青菜切碎"},
                {"step": 3, "description": "大米煮成粥"},
                {"step": 4, "description": "加入鱼丁蔬菜煮5分钟，煮熟即可"}
            ],
            "nutrition": {"calories": 150, "protein": 10.4, "iron": 1.1}
        },
        {
            "name": "虾仁西兰花炒饭",
            "ingredients": [
                {"name": "虾仁", "amount": "40g"},
                {"name": "西兰花", "amount": "30g"},
                {"name": "米饭", "amount": "50g"},
                {"name": "玉米碎", "amount": "15g"}
            ],
            "steps": [
                {"step": 1, "description": "虾仁去虾线切小丁"},
                {"step": 2, "description": "西兰花焯水切碎"},
                {"step": 3, "description": "热锅下虾仁炒熟，加蔬菜玉米翻炒"},
                {"step": 4, "description": "加入米饭炒匀，保持米粒松散"}
            ],
            "nutrition": {"calories": 190, "protein": 13.8, "iron": 1.6}
        }
    ],

    # 粥类主食
    "porridge": [
        {
            "name": "南瓜小米软粥",
            "ingredients": [
                {"name": "南瓜", "amount": "60g"},
                {"name": "小米", "amount": "20g"},
                {"name": "清水", "amount": "200ml"}
            ],
            "steps": [
                {"step": 1, "description": "小米提前泡30分钟"},
                {"step": 2, "description": "南瓜去皮切小丁"},
                {"step": 3, "description": "水烧开后放小米，煮20分钟至小米开花"},
                {"step": 4, "description": "加入南瓜丁再煮10分钟，搅拌至软烂"},
                {"step": 5, "description": "煮成稀稠合适的软粥"}
            ],
            "nutrition": {"calories": 85, "protein": 2.1, "iron": 0.8}
        },
        {
            "name": "红薯大米粥",
            "ingredients": [
                {"name": "红薯", "amount": "70g"},
                {"name": "大米", "amount": "20g"},
                {"name": "清水", "amount": "250ml"}
            ],
            "steps": [
                {"step": 1, "description": "大米淘洗干净提前泡"},
                {"step": 2, "description": "红薯去皮切小丁"},
                {"step": 3, "description": "大米煮20分钟，加入红薯煮15分钟"},
                {"step": 4, "description": "煮至软烂粘稠"}
            ],
            "nutrition": {"calories": 90, "protein": 1.5, "iron": 0.5}
        },
        {
            "name": "红枣小米粥",
            "ingredients": [
                {"name": "小米", "amount": "20g"},
                {"name": "红枣", "amount": "2颗"},
                {"name": "清水", "amount": "250ml"}
            ],
            "steps": [
                {"step": 1, "description": "小米提前泡好，红枣去核切碎"},
                {"step": 2, "description": "小米煮20分钟开花"},
                {"step": 3, "description": "加入红枣碎再煮10分钟"},
                {"step": 4, "description": "煮至软烂，红枣压碎"}
            ],
            "nutrition": {"calories": 88, "protein": 1.8, "iron": 1.0}
        },
        {
            "name": "山药小米粥",
            "ingredients": [
                {"name": "山药", "amount": "50g"},
                {"name": "小米", "amount": "20g"},
                {"name": "红枣", "amount": "1颗"}
            ],
            "steps": [
                {"step": 1, "description": "山药去皮切小丁，小米泡好"},
                {"step": 2, "description": "红枣去核切碎"},
                {"step": 3, "description": "一起下锅煮30分钟至软烂"},
                {"step": 4, "description": "煮成稀稠合适的粥"}
            ],
            "nutrition": {"calories": 95, "protein": 2.0, "iron": 0.6}
        },
        {
            "name": "青菜香菇粥",
            "ingredients": [
                {"name": "大米", "amount": "25g"},
                {"name": "青菜", "amount": "20g"},
                {"name": "鲜香菇", "amount": "1朵"}
            ],
            "steps": [
                {"step": 1, "description": "大米煮成稀粥"},
                {"step": 2, "description": "青菜香菇洗净切碎"},
                {"step": 3, "description": "放入粥中再煮5分钟"},
                {"step": 4, "description": "调味只用天然鲜味，不加盐"}
            ],
            "nutrition": {"calories": 100, "protein": 3.2, "iron": 1.0}
        }
    ],

    # 蔬果泥/蔬果块
    "vegetable_fruit": [
        {
            "name": "南瓜泥",
            "ingredients": [
                {"name": "南瓜", "amount": "50g"},
                {"name": "清水", "amount": "适量"}
            ],
            "steps": [
                {"step": 1, "description": "南瓜洗净去皮，切成小块"},
                {"step": 2, "description": "上锅蒸15分钟至完全软烂"},
                {"step": 3, "description": "取出用料理棒打成细腻泥糊状，可加少量清水调稀"}
            ],
            "nutrition": {"calories": 20, "protein": 0.5, "iron": 0.3}
        },
        {
            "name": "胡萝卜泥",
            "ingredients": [
                {"name": "胡萝卜", "amount": "40g"},
                {"name": "清水", "amount": "适量"}
            ],
            "steps": [
                {"step": 1, "description": "胡萝卜洗净去皮切小块"},
                {"step": 2, "description": "蒸15分钟至软烂"},
                {"step": 3, "description": "打成细腻泥状"}
            ],
            "nutrition": {"calories": 18, "protein": 0.4, "iron": 0.2}
        },
        {
            "name": "红薯泥",
            "ingredients": [
                {"name": "红薯", "amount": "50g"},
                {"name": "清水", "amount": "适量"}
            ],
            "steps": [
                {"step": 1, "description": "红薯洗净去皮切小块"},
                {"step": 2, "description": "上锅蒸20分钟至软烂"},
                {"step": 3, "description": "取出压成泥状，加适量水调稠"}
            ],
            "nutrition": {"calories": 30, "protein": 0.6, "iron": 0.3}
        },
        {
            "name": "山药泥",
            "ingredients": [
                {"name": "山药", "amount": "50g"},
                {"name": "清水", "amount": "适量"}
            ],
            "steps": [
                {"step": 1, "description": "山药洗净去皮切小块"},
                {"step": 2, "description": "蒸15分钟至软烂"},
                {"step": 3, "description": "取出压成细腻泥状"}
            ],
            "nutrition": {"calories": 28, "protein": 0.4, "iron": 0.2}
        },
        {
            "name": "苹果泥",
            "ingredients": [
                {"name": "新鲜苹果", "amount": "50g"},
                {"name": "温水", "amount": "少量"}
            ],
            "steps": [
                {"step": 1, "description": "苹果去皮去核切小块"},
                {"step": 2, "description": "用研磨碗磨成泥状，或用料理机打细"},
                {"step": 3, "description": "即刻食用，避免氧化变色"}
            ],
            "nutrition": {"calories": 26, "protein": 0.1, "iron": 0.1}
        },
        {
            "name": "香蕉泥",
            "ingredients": [
                {"name": "香蕉", "amount": "30g"}
            ],
            "steps": [
                {"step": 1, "description": "香蕉去皮"},
                {"step": 2, "description": "用勺子刮成泥状"},
                {"step": 3, "description": "直接喂食"}
            ],
            "nutrition": {"calories": 32, "protein": 0.4, "iron": 0.1}
        },
        {
            "name": "蒸苹果小块",
            "ingredients": [
                {"name": "苹果", "amount": "60g"}
            ],
            "steps": [
                {"step": 1, "description": "苹果去皮去核切小块"},
                {"step": 2, "description": "上锅蒸5分钟至略微变软"},
                {"step": 3, "description": "取出放温直接给宝宝抓着吃"}
            ],
            "nutrition": {"calories": 45, "protein": 0.2, "iron": 0.1}
        }
    ],

    # 高铁米糊
    "iron_rice": [
        {
            "name": "高铁米糊",
            "ingredients": [
                {"name": "婴儿高铁米粉", "amount": "10g"},
                {"name": "母乳/配方奶", "amount": "60ml"}
            ],
            "steps": [
                {"step": 1, "description": "将米粉放入碗中"},
                {"step": 2, "description": "倒入温奶，边倒边搅拌均匀"},
                {"step": 3, "description": "静置1分钟让米粉充分泡发"}
            ],
            "nutrition": {"calories": 40, "protein": 1.2, "iron": 2.5}
        },
        {
            "name": "稀释高铁米糊",
            "ingredients": [
                {"name": "婴儿高铁米粉", "amount": "10g"},
                {"name": "母乳/配方奶", "amount": "70ml"}
            ],
            "steps": [
                {"step": 1, "description": "米粉加奶搅拌均匀"},
                {"step": 2, "description": "静置1分钟"},
                {"step": 3, "description": "调稀后喂食"}
            ],
            "nutrition": {"calories": 40, "protein": 1.2, "iron": 2.5}
        },
        {
            "name": "高铁稠米糊",
            "ingredients": [
                {"name": "婴儿高铁米粉", "amount": "15g"},
                {"name": "母乳/配方奶", "amount": "80ml"}
            ],
            "steps": [
                {"step": 1, "description": "米粉倒入碗中"},
                {"step": 2, "description": "加温奶搅拌均匀"},
                {"step": 3, "description": "静置1分钟即可"}
            ],
            "nutrition": {"calories": 60, "protein": 1.8, "iron": 4.0}
        },
        {
            "name": "燕麦奶粉糊",
            "ingredients": [
                {"name": "即食燕麦片", "amount": "20g"},
                {"name": "配方奶", "amount": "100ml"}
            ],
            "steps": [
                {"step": 1, "description": "燕麦片用温水泡软"},
                {"step": 2, "description": "加入温配方奶搅拌均匀"},
                {"step": 3, "description": "煮2分钟至粘稠放凉"}
            ],
            "nutrition": {"calories": 95, "protein": 3.5, "iron": 1.2}
        }
    ]
}


def classify_dish_nutrition_type(dish: RecipeDetail) -> str:
    """
    根据菜品信息判断其营养类型
    返回对应的分类key
    """
    dish_name = dish.dish_name.lower()
    ingredients = [ing["name"].lower() for ing in dish.ingredients] if dish.ingredients else []

    # 检查是否红肉补铁
    if any(ing in ["牛肉", "猪肝", "鸭血", "红肉"] for ing in ingredients) or \
       (dish.nutrition_info and dish.nutrition_info.get("iron", 0) >= 2.5):
        return "iron_red_meat"

    # 检查是否禽肉高蛋白
    elif any(ing in ["鸡胸", "鸡肉", "猪肉", "瘦肉"] for ing in ingredients):
        return "protein_poultry"

    # 检查是否鱼虾水产
    elif any(ing in ["鳕鱼", "龙利鱼", "虾仁", "鱼", "虾"] for ing in ingredients):
        return "seafood_fish"

    # 检查是否粥类
    elif "粥" in dish_name or any(ing in ["小米", "大米", "粥"] for ing in ingredients):
        return "porridge"

    # 检查是否高铁米糊
    elif "米糊" in dish_name or "米粉" in dish_name:
        return "iron_rice"

    # 检查是否蔬果
    elif "泥" in dish_name or any(ing in ["苹果", "香蕉", "南瓜", "胡萝卜", "红薯", "山药"] for ing in ingredients):
        return "vegetable_fruit"

    # 默认归到粥类
    return "porridge"


def generate_replace_prompt(
    original_dish: RecipeDetail,
    baby: Baby
) -> str:
    """生成替换菜品的提示词"""
    original_iron = original_dish.nutrition_info.get("iron", 0) if original_dish.nutrition_info else 0
    original_calories = original_dish.nutrition_info.get("calories", 0) if original_dish.nutrition_info else 0
    original_protein = original_dish.nutrition_info.get("protein", 0) if original_dish.nutrition_info else 0

    original_ingredients = ", ".join([ing["name"] for ing in original_dish.ingredients]) if original_dish.ingredients else "无"

    return f"""
你是一位专业的婴幼儿营养师，请为现有菜品生成一道**营养相似但食材不同**的替代菜品。

## 宝宝信息
- 年龄：{baby.age_months}个月
- 进食能力：{baby.feeding_stage}
- 过敏源：{', '.join(baby.allergies) if baby.allergies else '无'}

## 原菜品信息
- 菜品名称：{original_dish.dish_name}
- 餐次：{original_dish.meal_type}
- 原营养信息：热量 {original_calories} kcal, 蛋白质 {original_protein} g, 铁 {original_iron} mg
- 原食材：{original_ingredients}

## 要求
1. **必须使用不同的食材**，不能和原菜品主要食材重复
2. **必须生成与以往不同的新颖组合**，禁止使用常见的重复搭配
3. **保持相同餐次**，营养成分（热量、蛋白质、铁含量）与原菜品相似，波动范围不超过±20%
4. 严格规避过敏源
5. 食材质地符合宝宝进食能力阶段：{baby.feeding_stage}
6. 大胆尝试多样化的食材组合，可以选用一些不那么常规但适合宝宝的食材
7. 请直接输出JSON，不要有其他说明文字

## 输出格式
{{
  "dish_name": "新菜品名称",
  "ingredients": [
    {{"name": "食材名", "amount": "50g"}},
    ...
  ],
  "cooking_steps": [
    {{"step": 1, "description": "步骤描述"}},
    ...
  ],
  "nutrition_info": {{
    "calories": XXX,
    "protein": XXX,
    "iron": XXX
  }}
}}
"""


def get_different_ingredient_replacement(original_dish: RecipeDetail, baby_feeding_stage: str) -> Dict:
    """
    从静态库获取一道营养相似但食材不同的替代菜品（兜底降级使用）
    """
    # 判断原菜品营养类型
    nutrition_type = classify_dish_nutrition_type(original_dish)

    # 获取该类型的所有候选菜
    candidates = REPLACEMENT_LIBRARY.get(nutrition_type, REPLACEMENT_LIBRARY["porridge"])

    # 过滤掉与原菜品同名的候选
    filtered_candidates = [
        c for c in candidates
        if c["name"] != original_dish.dish_name
    ]

    # 如果过滤后为空，使用全部候选
    if not filtered_candidates:
        filtered_candidates = candidates

    # 随机选择一道
    selected = random.choice(filtered_candidates)

    # 根据宝宝进食阶段微调（这里保持已有数据结构）
    return {
        "dish_name": selected["name"],
        "ingredients": selected["ingredients"],
        "cooking_steps": selected["steps"],
        "nutrition_info": selected["nutrition"]
    }


async def replace_dish(
    original_dish: RecipeDetail,
    baby: Baby,
    db: Session
) -> Dict:
    """
    生成一道替代菜品：营养相似，食材不同
    优先尝试火山引擎API动态生成，失败自动降级
    """
    # 优先尝试火山引擎API生成
    from app.services.volcengine_client import get_volcengine_client
    client = get_volcengine_client()
    if client.is_configured:
        system_prompt = "你是一位专业的婴幼儿营养师，请严格按照JSON格式输出。"
        user_prompt = generate_replace_prompt(original_dish, baby)

        try:
            result = await client.generate_json(system_prompt, user_prompt, temperature=0.8)
            if result and "dish_name" in result and "ingredients" in result:
                # API生成成功，直接返回
                # 保留原有的餐次和日期信息
                result["day_of_week"] = original_dish.day_of_week
                result["meal_type"] = original_dish.meal_type
                return result
            # 格式不对，触发降级
            print(f"Volcengine replace response format incorrect, falling back.")
        except Exception as e:
            print(f"Error calling Volcengine API for replace: {e}, falling back.")

    # 降级：先用DishCache从数据库采样
    print("Volcengine API not available for replace, falling back to cache sampling.")
    cache_service = DishCacheService(db)
    nutrition_type = classify_dish_nutrition_type(original_dish)
    cached = cache_service.random_sample_dish(
        nutrition_type=nutrition_type,
        exclude_dish_ids=[original_dish.id]
    )
    if cached:
        # 从缓存采样成功
        cached["day_of_week"] = original_dish.day_of_week
        cached["meal_type"] = original_dish.meal_type
        cached.pop("id", None)  # 移除id避免冲突
        return cached

    # 最后兜底：使用静态内置库
    print("Cache sampling failed, falling back to static replacement library.")
    replacement = get_different_ingredient_replacement(
        original_dish,
        baby.feeding_stage
    )
    # 保留原有的餐次信息
    replacement["day_of_week"] = original_dish.day_of_week
    replacement["meal_type"] = original_dish.meal_type

    return replacement
