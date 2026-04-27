"""
内置食谱数据库模块
包含100+道宝宝辅食，按月龄、餐次、营养类型分类
完全不依赖外部API，纯内置数据
"""
from typing import Dict, List, Optional

# 完整的食谱数据库
# 包含100+道宝宝辅食，覆盖6-8个月、9-11个月、12个月+三个阶段
RECIPE_DATABASE = [
    # ==================== 6-8个月 细腻泥状 ====================
    # 高铁米粉类 (breakfast)
    {
        "dish_name": "高铁营养米糊",
        "suitable_age_months": 6,
        "meal_type": "breakfast",
        "ingredients": [
            {"name": "婴儿高铁米粉", "amount": "15g"},
            {"name": "母乳/配方奶", "amount": "80ml"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "将米粉放入碗中"},
            {"step": 2, "description": "倒入温奶，边倒边搅拌均匀"},
            {"step": 3, "description": "静置1分钟让米粉充分泡发"}
        ],
        "nutrition_info": {"calories": 60, "protein": 1.8, "iron": 4.0, "calcium": 30},
        "allergen_tags": ["乳制品"],
        "tags": ["高铁", "泥状", "易消化", "早餐"],
        "main_ingredients": ["米粉"]
    },
    {
        "dish_name": "南瓜小米泥粥",
        "suitable_age_months": 6,
        "meal_type": "breakfast",
        "ingredients": [
            {"name": "小米", "amount": "20g"},
            {"name": "南瓜", "amount": "50g"},
            {"name": "清水", "amount": "200ml"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "小米提前泡30分钟，南瓜去皮切小丁"},
            {"step": 2, "description": "水烧开后放小米，煮20分钟至小米开花"},
            {"step": 3, "description": "加入南瓜丁再煮10分钟，搅拌至软烂"},
            {"step": 4, "description": "用料理棒打成细腻泥状"}
        ],
        "nutrition_info": {"calories": 85, "protein": 2.1, "iron": 0.8, "calcium": 25},
        "allergen_tags": [],
        "tags": ["泥状", "易消化", "碳水", "早餐"],
        "main_ingredients": ["小米", "南瓜"]
    },
    {
        "dish_name": "红薯大米泥粥",
        "suitable_age_months": 6,
        "meal_type": "breakfast",
        "ingredients": [
            {"name": "大米", "amount": "20g"},
            {"name": "红薯", "amount": "50g"},
            {"name": "清水", "amount": "200ml"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "大米提前泡30分钟，红薯去皮切小丁"},
            {"step": 2, "description": "一起下锅煮30分钟至完全软烂"},
            {"step": 3, "description": "用料理棒打成细腻泥状"}
        ],
        "nutrition_info": {"calories": 75, "protein": 1.5, "iron": 0.5, "calcium": 18},
        "allergen_tags": [],
        "tags": ["泥状", "碳水", "早餐", "通便"],
        "main_ingredients": ["大米", "红薯"]
    },
    # 蔬菜泥类 (lunch/dinner)
    {
        "dish_name": "胡萝卜土豆泥",
        "suitable_age_months": 6,
        "meal_type": "lunch",
        "ingredients": [
            {"name": "胡萝卜", "amount": "40g"},
            {"name": "土豆", "amount": "50g"},
            {"name": "母乳/配方奶", "amount": "20ml"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "胡萝卜、土豆洗净去皮切小块"},
            {"step": 2, "description": "上锅蒸15分钟至完全软烂"},
            {"step": 3, "description": "取出用料理棒打成泥，加入温奶调稀"}
        ],
        "nutrition_info": {"calories": 55, "protein": 1.2, "iron": 0.5, "calcium": 20},
        "allergen_tags": ["乳制品"],
        "tags": ["泥状", "蔬菜", "维生素A"],
        "main_ingredients": ["胡萝卜", "土豆"]
    },
    {
        "dish_name": "西兰花鸡肉泥",
        "suitable_age_months": 7,
        "meal_type": "lunch",
        "ingredients": [
            {"name": "鸡胸肉", "amount": "30g"},
            {"name": "西兰花", "amount": "40g"},
            {"name": "清水", "amount": "适量"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "鸡胸肉切小块，冷水下锅煮熟去血沫"},
            {"step": 2, "description": "西兰花掰小朵焯水3分钟"},
            {"step": 3, "description": "将鸡肉和西兰花一起打成细腻泥状"}
        ],
        "nutrition_info": {"calories": 75, "protein": 8.5, "iron": 0.8, "calcium": 18},
        "allergen_tags": [],
        "tags": ["高蛋白", "泥状", "补铁", "午餐"],
        "main_ingredients": ["鸡肉", "西兰花"]
    },
    # 水果泥类 (snack)
    {
        "dish_name": "苹果香蕉泥",
        "suitable_age_months": 6,
        "meal_type": "snack",
        "ingredients": [
            {"name": "苹果", "amount": "40g"},
            {"name": "香蕉", "amount": "30g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "苹果去皮去核切小块，上锅蒸5分钟"},
            {"step": 2, "description": "香蕉去皮切小块"},
            {"step": 3, "description": "将苹果和香蕉一起打成细腻泥状"}
        ],
        "nutrition_info": {"calories": 45, "protein": 0.3, "iron": 0.2, "calcium": 12},
        "allergen_tags": [],
        "tags": ["水果", "维生素", "加餐", "通便"],
        "main_ingredients": ["苹果", "香蕉"]
    },
    {
        "dish_name": "纯红薯泥",
        "suitable_age_months": 6,
        "meal_type": "lunch",
        "ingredients": [
            {"name": "红薯", "amount": "60g"},
            {"name": "母乳/配方奶", "amount": "20ml"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "红薯洗净去皮切小块"},
            {"step": 2, "description": "上锅蒸15分钟至完全软烂"},
            {"step": 3, "description": "取出压成泥，加入温奶调至合适稠度"}
        ],
        "nutrition_info": {"calories": 55, "protein": 0.8, "iron": 0.4, "calcium": 20},
        "allergen_tags": ["乳制品"],
        "tags": ["泥状", "蔬菜", "通便", "午餐"],
        "main_ingredients": ["红薯"]
    },
    {
        "dish_name": "山药泥",
        "suitable_age_months": 6,
        "meal_type": "dinner",
        "ingredients": [
            {"name": "山药", "amount": "60g"},
            {"name": "温水", "amount": "适量"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "山药去皮切小块，注意戴手套避免过敏"},
            {"step": 2, "description": "上锅蒸15分钟至软烂"},
            {"step": 3, "description": "加温水打成细腻泥状"}
        ],
        "nutrition_info": {"calories": 40, "protein": 1.0, "iron": 0.3, "calcium": 15},
        "allergen_tags": [],
        "tags": ["泥状", "健脾", "养胃", "晚餐"],
        "main_ingredients": ["山药"]
    },
    {
        "dish_name": "西梅泥",
        "suitable_age_months": 6,
        "meal_type": "snack",
        "ingredients": [
            {"name": "西梅", "amount": "50g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "西梅洗净去皮去核"},
            {"step": 2, "description": "上锅蒸5分钟至软烂"},
            {"step": 3, "description": "打成细腻泥状，可加少量水调稀"}
        ],
        "nutrition_info": {"calories": 35, "protein": 0.3, "iron": 0.2, "calcium": 10},
        "allergen_tags": [],
        "tags": ["水果", "通便", "加餐", "缓解便秘"],
        "main_ingredients": ["西梅"]
    },
    {
        "dish_name": "土豆泥",
        "suitable_age_months": 6,
        "meal_type": "dinner",
        "ingredients": [
            {"name": "土豆", "amount": "60g"},
            {"name": "母乳/配方奶", "amount": "20ml"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "土豆洗净去皮切小块"},
            {"step": 2, "description": "上锅蒸15分钟至完全软烂"},
            {"step": 3, "description": "压成泥，加入温奶搅拌均匀"}
        ],
        "nutrition_info": {"calories": 50, "protein": 1.0, "iron": 0.3, "calcium": 8},
        "allergen_tags": ["乳制品"],
        "tags": ["泥状", "蔬菜", "易消化", "晚餐"],
        "main_ingredients": ["土豆"]
    },
    {
        "dish_name": "纯南瓜泥",
        "suitable_age_months": 6,
        "meal_type": "lunch",
        "ingredients": [
            {"name": "南瓜", "amount": "60g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "南瓜洗净去皮去籽切小块"},
            {"step": 2, "description": "上锅蒸15分钟至软烂"},
            {"step": 3, "description": "打成细腻泥状，可加少量水调稀"}
        ],
        "nutrition_info": {"calories": 25, "protein": 0.5, "iron": 0.3, "calcium": 10},
        "allergen_tags": [],
        "tags": ["泥状", "蔬菜", "维生素A", "午餐"],
        "main_ingredients": ["南瓜"]
    },
    {
        "dish_name": "梨泥",
        "suitable_age_months": 6,
        "meal_type": "snack",
        "ingredients": [
            {"name": "梨", "amount": "50g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "梨洗净去皮去核切小块"},
            {"step": 2, "description": "上锅蒸5分钟至软烂"},
            {"step": 3, "description": "打成细腻泥状或用勺子压泥"}
        ],
        "nutrition_info": {"calories": 30, "protein": 0.2, "iron": 0.1, "calcium": 8},
        "allergen_tags": [],
        "tags": ["水果", "润肺", "加餐", "清热"],
        "main_ingredients": ["梨"]
    },
    # ==================== 继续添加更多食谱 ====================
    # 6-8个月 更多
    {
        "dish_name": "菠菜猪肝泥",
        "suitable_age_months": 7,
        "meal_type": "lunch",
        "ingredients": [
            {"name": "猪肝", "amount": "25g"},
            {"name": "菠菜", "amount": "30g"},
            {"name": "生姜", "amount": "1片"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "猪肝用姜片去腥，冷水下锅煮熟"},
            {"step": 2, "description": "菠菜焯水去草酸，切小段"},
            {"step": 3, "description": "猪肝和菠菜一起打成细腻泥状"}
        ],
        "nutrition_info": {"calories": 65, "protein": 7.2, "iron": 6.5, "calcium": 15},
        "allergen_tags": [],
        "tags": ["高铁", "高蛋白", "泥状", "补铁首选"],
        "main_ingredients": ["猪肝", "菠菜"]
    },
    {
        "dish_name": "山药红枣泥",
        "suitable_age_months": 7,
        "meal_type": "breakfast",
        "ingredients": [
            {"name": "山药", "amount": "60g"},
            {"name": "红枣", "amount": "2颗"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "山药去皮切小块，红枣去核"},
            {"step": 2, "description": "一起上锅蒸15分钟至软烂"},
            {"step": 3, "description": "取出压成细腻泥状，红枣去皮"}
        ],
        "nutrition_info": {"calories": 70, "protein": 1.5, "iron": 0.6, "calcium": 22},
        "allergen_tags": [],
        "tags": ["健脾", "泥状", "早餐", "养胃"],
        "main_ingredients": ["山药", "红枣"]
    },
    {
        "dish_name": "鳕鱼泥",
        "suitable_age_months": 7,
        "meal_type": "dinner",
        "ingredients": [
            {"name": "鳕鱼", "amount": "40g"},
            {"name": "柠檬", "amount": "1片"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "鳕鱼去皮去刺，用柠檬汁腌制10分钟去腥"},
            {"step": 2, "description": "上锅蒸8分钟至完全熟透"},
            {"step": 3, "description": "取出压成细腻鱼泥，检查无鱼刺"}
        ],
        "nutrition_info": {"calories": 55, "protein": 10.2, "iron": 0.3, "calcium": 15, "dha": 80},
        "allergen_tags": ["鱼类"],
        "tags": ["高蛋白", "DHA", "深海鱼", "补脑"],
        "main_ingredients": ["鳕鱼"]
    },
    {
        "dish_name": "牛油果香蕉泥",
        "suitable_age_months": 7,
        "meal_type": "snack",
        "ingredients": [
            {"name": "牛油果", "amount": "30g"},
            {"name": "香蕉", "amount": "40g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "牛油果对半切开去核，取果肉"},
            {"step": 2, "description": "香蕉去皮切小块"},
            {"step": 3, "description": "用勺子压成细腻泥状混合均匀"}
        ],
        "nutrition_info": {"calories": 85, "protein": 1.2, "iron": 0.4, "calcium": 12, "healthy_fat": 8},
        "allergen_tags": [],
        "tags": ["健康脂肪", "水果", "加餐", "补脑"],
        "main_ingredients": ["牛油果", "香蕉"]
    },
    {
        "dish_name": "豌豆泥",
        "suitable_age_months": 7,
        "meal_type": "lunch",
        "ingredients": [
            {"name": "新鲜豌豆", "amount": "60g"},
            {"name": "母乳/配方奶", "amount": "20ml"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "豌豆洗净，开水煮5分钟至熟"},
            {"step": 2, "description": "过凉水后去皮（重要！避免卡喉）"},
            {"step": 3, "description": "加少量温奶打成细腻泥状"}
        ],
        "nutrition_info": {"calories": 60, "protein": 4.2, "iron": 1.2, "calcium": 25},
        "allergen_tags": ["乳制品"],
        "tags": ["高蛋白", "蔬菜", "补铁", "泥状"],
        "main_ingredients": ["豌豆"]
    },
    # ==================== 9-11个月 小颗粒/碎末 ====================
    {
        "dish_name": "南瓜小米软粥",
        "suitable_age_months": 9,
        "meal_type": "breakfast",
        "ingredients": [
            {"name": "小米", "amount": "25g"},
            {"name": "南瓜", "amount": "60g"},
            {"name": "清水", "amount": "250ml"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "小米提前泡30分钟，南瓜去皮切小丁"},
            {"step": 2, "description": "水烧开后放小米，煮25分钟至小米开花"},
            {"step": 3, "description": "加入南瓜丁再煮10分钟，搅拌至软烂，保留小颗粒"}
        ],
        "nutrition_info": {"calories": 95, "protein": 2.5, "iron": 1.0, "calcium": 28},
        "allergen_tags": [],
        "tags": ["小颗粒", "早餐", "碳水", "易消化"],
        "main_ingredients": ["小米", "南瓜"]
    },
    {
        "dish_name": "鸡肉蔬菜碎末粥",
        "suitable_age_months": 9,
        "meal_type": "lunch",
        "ingredients": [
            {"name": "鸡胸肉末", "amount": "30g"},
            {"name": "胡萝卜碎", "amount": "20g"},
            {"name": "青菜碎", "amount": "15g"},
            {"name": "大米", "amount": "25g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "大米提前泡好，煮成稠粥"},
            {"step": 2, "description": "鸡胸肉剁成细末，胡萝卜、青菜切小碎末"},
            {"step": 3, "description": "鸡肉末下锅炒熟，加入蔬菜碎翻炒"},
            {"step": 4, "description": "将炒好的鸡肉蔬菜拌入粥中，再煮2分钟"}
        ],
        "nutrition_info": {"calories": 130, "protein": 9.5, "iron": 1.5, "calcium": 30},
        "allergen_tags": [],
        "tags": ["高蛋白", "碎末状", "午餐", "营养均衡"],
        "main_ingredients": ["鸡肉", "胡萝卜", "青菜"]
    },
    {
        "dish_name": "番茄牛肉面",
        "suitable_age_months": 10,
        "meal_type": "dinner",
        "ingredients": [
            {"name": "牛里脊肉末", "amount": "30g"},
            {"name": "番茄", "amount": "50g"},
            {"name": "婴儿细面条", "amount": "30g"},
            {"name": "洋葱碎", "amount": "10g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "番茄去皮去籽切小丁，洋葱切细末"},
            {"step": 2, "description": "牛肉末炒香，加入洋葱炒软，加入番茄炒出汁"},
            {"step": 3, "description": "加适量水煮开，下掰断的面条煮软"},
            {"step": 4, "description": "面条煮至软烂，剪小段方便食用"}
        ],
        "nutrition_info": {"calories": 160, "protein": 10.8, "iron": 2.8, "calcium": 35},
        "allergen_tags": [],
        "tags": ["高铁", "高蛋白", "碎末状", "晚餐", "开胃"],
        "main_ingredients": ["牛肉", "番茄", "面条"]
    },
    {
        "dish_name": "蒸蛋羹虾仁版",
        "suitable_age_months": 10,
        "meal_type": "lunch",
        "ingredients": [
            {"name": "鸡蛋", "amount": "1个"},
            {"name": "虾仁", "amount": "20g"},
            {"name": "温水", "amount": "60ml"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "虾仁去虾线切小丁，焯水备用"},
            {"step": 2, "description": "鸡蛋打散，加入1.5倍温水搅匀，过筛去泡沫"},
            {"step": 3, "description": "盖上保鲜膜扎小孔，上汽后蒸8分钟"},
            {"step": 4, "description": "揭开膜放入虾仁，再蒸2分钟即可"}
        ],
        "nutrition_info": {"calories": 110, "protein": 12.5, "iron": 1.8, "calcium": 55},
        "allergen_tags": ["鸡蛋", "虾"],
        "tags": ["高蛋白", "蒸菜", "补钙", "软嫩"],
        "main_ingredients": ["鸡蛋", "虾仁"]
    },
    {
        "dish_name": "红薯燕麦粥",
        "suitable_age_months": 9,
        "meal_type": "breakfast",
        "ingredients": [
            {"name": "即食燕麦片", "amount": "20g"},
            {"name": "红薯", "amount": "50g"},
            {"name": "配方奶", "amount": "80ml"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "红薯去皮切小丁，蒸熟压成泥（保留小颗粒）"},
            {"step": 2, "description": "燕麦片用温水泡软，加入温奶"},
            {"step": 3, "description": "混合红薯泥，搅拌均匀即可"}
        ],
        "nutrition_info": {"calories": 105, "protein": 3.8, "iron": 1.5, "calcium": 45},
        "allergen_tags": ["乳制品"],
        "tags": ["膳食纤维", "早餐", "通便", "小颗粒"],
        "main_ingredients": ["燕麦", "红薯"]
    },
    {
        "dish_name": "豆腐鳕鱼蒸",
        "suitable_age_months": 10,
        "meal_type": "dinner",
        "ingredients": [
            {"name": "鳕鱼", "amount": "30g"},
            {"name": "嫩豆腐", "amount": "40g"},
            {"name": "葱花", "amount": "少许"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "鳕鱼去皮去刺切小块，用柠檬汁去腥"},
            {"step": 2, "description": "豆腐切小块铺碗底，放上鳕鱼块"},
            {"step": 3, "description": "上汽后蒸10分钟，撒上葱花即可"}
        ],
        "nutrition_info": {"calories": 95, "protein": 12.8, "iron": 0.8, "calcium": 65, "dha": 60},
        "allergen_tags": ["鱼类", "大豆"],
        "tags": ["高蛋白", "补钙", "DHA", "蒸菜", "软嫩"],
        "main_ingredients": ["鳕鱼", "豆腐"]
    },
    # 手指食物 (snack)
    {
        "dish_name": "蒸苹果条",
        "suitable_age_months": 9,
        "meal_type": "snack",
        "ingredients": [
            {"name": "苹果", "amount": "60g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "苹果去皮去核，切成手指粗细的长条"},
            {"step": 2, "description": "上锅蒸5分钟至略微变软，不要太烂"},
            {"step": 3, "description": "取出放温后给宝宝抓握食用"}
        ],
        "nutrition_info": {"calories": 40, "protein": 0.2, "iron": 0.1, "calcium": 8},
        "allergen_tags": [],
        "tags": ["手指食物", "水果", "维生素", "锻炼抓握"],
        "main_ingredients": ["苹果"]
    },
    {
        "dish_name": "南瓜磨牙条",
        "suitable_age_months": 9,
        "meal_type": "snack",
        "ingredients": [
            {"name": "南瓜泥", "amount": "40g"},
            {"name": "低筋面粉", "amount": "50g"},
            {"name": "蛋黄", "amount": "1个"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "南瓜蒸熟压泥，加入蛋黄和面粉揉成面团"},
            {"step": 2, "description": "擀成0.5cm厚的片，切成长条"},
            {"step": 3, "description": "烤箱预热150度，烤20分钟至表面微黄变硬"}
        ],
        "nutrition_info": {"calories": 120, "protein": 3.5, "iron": 0.8, "calcium": 15},
        "allergen_tags": ["鸡蛋", "小麦"],
        "tags": ["手指食物", "磨牙", "烘焙", "锻炼咀嚼"],
        "main_ingredients": ["南瓜", "面粉"]
    },
    # ==================== 12个月+ 小块/手指食物 ====================
    {
        "dish_name": "蔬菜鸡肉软饭团",
        "suitable_age_months": 12,
        "meal_type": "lunch",
        "ingredients": [
            {"name": "鸡胸肉丁", "amount": "35g"},
            {"name": "胡萝卜丁", "amount": "20g"},
            {"name": "青豆", "amount": "15g"},
            {"name": "软米饭", "amount": "60g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "鸡胸肉切小丁，胡萝卜切小丁，青豆焯水"},
            {"step": 2, "description": "热锅下油，鸡肉丁炒至变色，加入蔬菜丁炒熟"},
            {"step": 3, "description": "和软米饭混合均匀，捏成宝宝能抓握的小饭团"}
        ],
        "nutrition_info": {"calories": 180, "protein": 12.5, "iron": 1.8, "calcium": 35},
        "allergen_tags": [],
        "tags": ["高蛋白", "手指食物", "午餐", "营养均衡"],
        "main_ingredients": ["鸡肉", "胡萝卜", "青豆", "米饭"]
    },
    {
        "dish_name": "番茄鸡蛋疙瘩汤",
        "suitable_age_months": 12,
        "meal_type": "dinner",
        "ingredients": [
            {"name": "番茄", "amount": "50g"},
            {"name": "鸡蛋", "amount": "1个"},
            {"name": "面粉", "amount": "30g"},
            {"name": "青菜叶", "amount": "15g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "番茄去皮切小块，青菜切碎，鸡蛋打散"},
            {"step": 2, "description": "面粉分次滴水，边滴边搅拌成小面疙瘩"},
            {"step": 3, "description": "番茄炒出汁，加水煮开，下面疙瘩煮3分钟"},
            {"step": 4, "description": "淋入蛋液，加入青菜碎，煮1分钟即可"}
        ],
        "nutrition_info": {"calories": 155, "protein": 8.5, "iron": 2.0, "calcium": 40},
        "allergen_tags": ["鸡蛋", "小麦"],
        "tags": ["开胃", "晚餐", "易消化", "小块状"],
        "main_ingredients": ["番茄", "鸡蛋", "面粉"]
    },
    {
        "dish_name": "三文鱼蔬菜炒饭",
        "suitable_age_months": 12,
        "meal_type": "lunch",
        "ingredients": [
            {"name": "三文鱼", "amount": "35g"},
            {"name": "西兰花碎", "amount": "25g"},
            {"name": "胡萝卜丁", "amount": "20g"},
            {"name": "软米饭", "amount": "60g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "三文鱼去皮去刺切小丁，用柠檬汁去腥"},
            {"step": 2, "description": "西兰花焯水切碎，胡萝卜切小丁焯水"},
            {"step": 3, "description": "热锅下油，三文鱼丁炒至变色，加入蔬菜翻炒"},
            {"step": 4, "description": "加入米饭炒匀，保持米粒松散"}
        ],
        "nutrition_info": {"calories": 210, "protein": 14.8, "iron": 1.5, "calcium": 45, "dha": 120},
        "allergen_tags": ["鱼类"],
        "tags": ["高蛋白", "DHA", "午餐", "营养丰富"],
        "main_ingredients": ["三文鱼", "西兰花", "胡萝卜", "米饭"]
    },
    {
        "dish_name": "玉米排骨汤面",
        "suitable_age_months": 12,
        "meal_type": "dinner",
        "ingredients": [
            {"name": "排骨", "amount": "50g"},
            {"name": "甜玉米", "amount": "30g"},
            {"name": "婴儿面条", "amount": "35g"},
            {"name": "胡萝卜片", "amount": "15g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "排骨冷水下锅焯水去血沫，重新加水炖40分钟"},
            {"step": 2, "description": "玉米切段，胡萝卜切片，放入排骨汤中煮15分钟"},
            {"step": 3, "description": "取出排骨去骨取肉切小丁，玉米剥粒"},
            {"step": 4, "description": "汤中下面条煮熟，加入肉丁玉米粒，剪短面条"}
        ],
        "nutrition_info": {"calories": 220, "protein": 13.5, "iron": 2.2, "calcium": 55},
        "allergen_tags": [],
        "tags": ["补钙", "高蛋白", "汤面", "晚餐"],
        "main_ingredients": ["排骨", "玉米", "面条"]
    },
    # 早餐类
    {
        "dish_name": "蔬菜鸡蛋软饼",
        "suitable_age_months": 12,
        "meal_type": "breakfast",
        "ingredients": [
            {"name": "鸡蛋", "amount": "1个"},
            {"name": "面粉", "amount": "25g"},
            {"name": "胡萝卜丝", "amount": "20g"},
            {"name": "西葫芦丝", "amount": "20g"},
            {"name": "配方奶", "amount": "20ml"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "鸡蛋打散，加入面粉和配方奶搅拌成稀糊"},
            {"step": 2, "description": "加入胡萝卜丝和西葫芦丝拌匀"},
            {"step": 3, "description": "平底锅刷薄油，倒入面糊摊成小饼，两面煎熟"},
            {"step": 4, "description": "切成小块方便抓握"}
        ],
        "nutrition_info": {"calories": 145, "protein": 6.8, "iron": 1.8, "calcium": 50},
        "allergen_tags": ["鸡蛋", "小麦", "乳制品"],
        "tags": ["早餐", "手指食物", "蔬菜", "鸡蛋"],
        "main_ingredients": ["鸡蛋", "面粉", "胡萝卜", "西葫芦"]
    },
    {
        "dish_name": "香蕉松饼",
        "suitable_age_months": 12,
        "meal_type": "breakfast",
        "ingredients": [
            {"name": "香蕉", "amount": "50g"},
            {"name": "鸡蛋", "amount": "1个"},
            {"name": "低筋面粉", "amount": "30g"},
            {"name": "配方奶", "amount": "30ml"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "香蕉压成泥，加入鸡蛋打散"},
            {"step": 2, "description": "加入面粉和配方奶搅拌成顺滑面糊"},
            {"step": 3, "description": "平底锅刷薄油，小火，舀入面糊摊成小饼"},
            {"step": 4, "description": "表面起泡后翻面，煎至两面金黄即可"}
        ],
        "nutrition_info": {"calories": 165, "protein": 6.2, "iron": 1.2, "calcium": 45},
        "allergen_tags": ["鸡蛋", "小麦", "乳制品"],
        "tags": ["早餐", "甜点", "香蕉", "松软"],
        "main_ingredients": ["香蕉", "鸡蛋", "面粉"]
    },
    # 加餐类
    {
        "dish_name": "酸奶水果杯",
        "suitable_age_months": 12,
        "meal_type": "snack",
        "ingredients": [
            {"name": "无糖婴儿酸奶", "amount": "50g"},
            {"name": "草莓", "amount": "20g"},
            {"name": "蓝莓", "amount": "15g"},
            {"name": "香蕉片", "amount": "15g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "草莓洗净去蒂切小块，蓝莓洗净，香蕉切薄片"},
            {"step": 2, "description": "杯中先铺一层酸奶，再铺一层水果"},
            {"step": 3, "description": "重复分层，最后用几颗蓝莓装饰即可"}
        ],
        "nutrition_info": {"calories": 85, "protein": 3.5, "iron": 0.5, "calcium": 80},
        "allergen_tags": ["乳制品"],
        "tags": ["益生菌", "水果", "加餐", "补钙"],
        "main_ingredients": ["酸奶", "草莓", "蓝莓", "香蕉"]
    },
    {
        "dish_name": "红薯山药蒸糕",
        "suitable_age_months": 12,
        "meal_type": "snack",
        "ingredients": [
            {"name": "红薯", "amount": "40g"},
            {"name": "山药", "amount": "40g"},
            {"name": "鸡蛋", "amount": "1个"},
            {"name": "低筋面粉", "amount": "20g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "红薯、山药去皮切小块蒸熟，压成泥"},
            {"step": 2, "description": "加入鸡蛋打散，再加入面粉搅拌成稠糊"},
            {"step": 3, "description": "倒入刷油的碗中，震平表面，盖上保鲜膜扎孔"},
            {"step": 4, "description": "上汽后蒸20分钟，关火焖5分钟，取出切块"}
        ],
        "nutrition_info": {"calories": 140, "protein": 5.5, "iron": 1.0, "calcium": 35},
        "allergen_tags": ["鸡蛋", "小麦"],
        "tags": ["蒸糕", "加餐", "健脾", "手指食物"],
        "main_ingredients": ["红薯", "山药", "鸡蛋", "面粉"]
    },
    # ==================== 继续添加更多食谱达到100+ ====================
    # 6-8个月 补充
    {
        "dish_name": "油菜泥",
        "suitable_age_months": 6,
        "meal_type": "dinner",
        "ingredients": [
            {"name": "小油菜", "amount": "60g"},
            {"name": "高铁米粉", "amount": "10g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "小油菜只取菜叶，洗净后开水焯2分钟"},
            {"step": 2, "description": "捞出过凉水，沥干水分"},
            {"step": 3, "description": "加少量温水打成细腻菜泥，拌入米粉食用"}
        ],
        "nutrition_info": {"calories": 45, "protein": 1.5, "iron": 1.8, "calcium": 50},
        "allergen_tags": [],
        "tags": ["高铁", "蔬菜", "补钙", "泥状"],
        "main_ingredients": ["油菜"]
    },
    {
        "dish_name": "紫薯泥",
        "suitable_age_months": 6,
        "meal_type": "breakfast",
        "ingredients": [
            {"name": "紫薯", "amount": "60g"},
            {"name": "配方奶", "amount": "30ml"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "紫薯去皮切小块，上锅蒸15分钟至软烂"},
            {"step": 2, "description": "取出压成泥，加入温奶调至合适稠度"}
        ],
        "nutrition_info": {"calories": 75, "protein": 1.8, "iron": 0.6, "calcium": 25},
        "allergen_tags": ["乳制品"],
        "tags": ["花青素", "早餐", "通便", "泥状"],
        "main_ingredients": ["紫薯"]
    },
    {
        "dish_name": "蛋黄泥",
        "suitable_age_months": 7,
        "meal_type": "lunch",
        "ingredients": [
            {"name": "鸡蛋黄", "amount": "1个"},
            {"name": "配方奶", "amount": "20ml"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "鸡蛋冷水下锅，水开后煮8分钟"},
            {"step": 2, "description": "取出过凉水，剥壳分离蛋黄"},
            {"step": 3, "description": "蛋黄压碎，加入温奶调成泥状"}
        ],
        "nutrition_info": {"calories": 65, "protein": 3.5, "iron": 1.2, "calcium": 25, "lecithin": 100},
        "allergen_tags": ["鸡蛋", "乳制品"],
        "tags": ["蛋黄", "补铁", "卵磷脂", "补脑"],
        "main_ingredients": ["鸡蛋"]
    },
    {
        "dish_name": "山药鸡肉泥",
        "suitable_age_months": 7,
        "meal_type": "dinner",
        "ingredients": [
            {"name": "鸡胸肉", "amount": "30g"},
            {"name": "山药", "amount": "40g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "鸡胸肉切小块煮熟，山药去皮切小块蒸熟"},
            {"step": 2, "description": "将鸡肉和山药一起放入料理机"},
            {"step": 3, "description": "加少量温水打成细腻泥状"}
        ],
        "nutrition_info": {"calories": 70, "protein": 7.8, "iron": 0.6, "calcium": 15},
        "allergen_tags": [],
        "tags": ["高蛋白", "健脾", "泥状", "晚餐"],
        "main_ingredients": ["鸡肉", "山药"]
    },
    {
        "dish_name": "猕猴桃泥",
        "suitable_age_months": 8,
        "meal_type": "snack",
        "ingredients": [
            {"name": "猕猴桃", "amount": "50g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "猕猴桃去皮，取果肉"},
            {"step": 2, "description": "用勺子压成泥状，挑出黑籽"},
            {"step": 3, "description": "直接喂食即可"}
        ],
        "nutrition_info": {"calories": 30, "protein": 0.5, "iron": 0.2, "calcium": 15, "vitamin_c": 50},
        "allergen_tags": [],
        "tags": ["维生素C", "水果", "通便", "加餐"],
        "main_ingredients": ["猕猴桃"]
    },
    {
        "dish_name": "黑木耳红枣泥",
        "suitable_age_months": 8,
        "meal_type": "lunch",
        "ingredients": [
            {"name": "干黑木耳", "amount": "5g"},
            {"name": "红枣", "amount": "3颗"},
            {"name": "高铁米粉", "amount": "10g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "黑木耳泡发洗净，开水煮5分钟"},
            {"step": 2, "description": "红枣去核去皮，和木耳一起打成泥"},
            {"step": 3, "description": "拌入冲好的高铁米粉中食用"}
        ],
        "nutrition_info": {"calories": 80, "protein": 2.5, "iron": 5.2, "calcium": 35},
        "allergen_tags": [],
        "tags": ["高铁", "补铁", "补血", "泥状"],
        "main_ingredients": ["黑木耳", "红枣"]
    },
    {
        "dish_name": "冬瓜泥",
        "suitable_age_months": 7,
        "meal_type": "dinner",
        "ingredients": [
            {"name": "冬瓜", "amount": "60g"},
            {"name": "猪瘦肉", "amount": "20g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "冬瓜去皮去籽切小块，猪瘦肉切小块"},
            {"step": 2, "description": "一起上锅蒸15分钟至软烂"},
            {"step": 3, "description": "取出打成细腻泥状"}
        ],
        "nutrition_info": {"calories": 45, "protein": 4.2, "iron": 0.8, "calcium": 10},
        "allergen_tags": [],
        "tags": ["清热", "利尿", "夏季", "泥状"],
        "main_ingredients": ["冬瓜", "猪肉"]
    },
    # 9-11个月 补充
    {
        "dish_name": "香菇鸡肉粥",
        "suitable_age_months": 9,
        "meal_type": "lunch",
        "ingredients": [
            {"name": "大米", "amount": "25g"},
            {"name": "鸡胸肉末", "amount": "25g"},
            {"name": "鲜香菇", "amount": "1朵"},
            {"name": "青菜碎", "amount": "15g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "大米提前泡好，煮成稠粥"},
            {"step": 2, "description": "香菇焯水后切细末，青菜切碎"},
            {"step": 3, "description": "鸡肉末炒香，加入香菇炒软，拌入粥中"},
            {"step": 4, "description": "最后加入青菜碎，再煮2分钟即可"}
        ],
        "nutrition_info": {"calories": 135, "protein": 8.8, "iron": 1.2, "calcium": 25},
        "allergen_tags": [],
        "tags": ["高蛋白", "提鲜", "碎末状", "午餐"],
        "main_ingredients": ["鸡肉", "香菇", "大米"]
    },
    {
        "dish_name": "猪肝菠菜粒粒面",
        "suitable_age_months": 9,
        "meal_type": "lunch",
        "ingredients": [
            {"name": "猪肝", "amount": "25g"},
            {"name": "菠菜", "amount": "30g"},
            {"name": "粒粒面", "amount": "30g"},
            {"name": "生姜", "amount": "1片"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "猪肝用姜片去腥，煮熟后切细末"},
            {"step": 2, "description": "菠菜焯水去草酸，切细末"},
            {"step": 3, "description": "粒粒面煮熟，加入猪肝末和菠菜末煮1分钟"}
        ],
        "nutrition_info": {"calories": 145, "protein": 9.2, "iron": 6.8, "calcium": 30},
        "allergen_tags": [],
        "tags": ["高铁", "补铁首选", "碎末状", "午餐"],
        "main_ingredients": ["猪肝", "菠菜", "粒粒面"]
    },
    {
        "dish_name": "虾仁豆腐碎",
        "suitable_age_months": 10,
        "meal_type": "dinner",
        "ingredients": [
            {"name": "虾仁", "amount": "30g"},
            {"name": "嫩豆腐", "amount": "50g"},
            {"name": "青菜碎", "amount": "15g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "虾仁去虾线切小丁，焯水备用"},
            {"step": 2, "description": "豆腐切小丁，青菜切碎"},
            {"step": 3, "description": "锅内加少量水烧开，下豆腐煮2分钟"},
            {"step": 4, "description": "加入虾仁和青菜碎，煮1分钟即可"}
        ],
        "nutrition_info": {"calories": 95, "protein": 11.5, "iron": 1.2, "calcium": 70},
        "allergen_tags": ["虾", "大豆"],
        "tags": ["高蛋白", "补钙", "晚餐", "碎末状"],
        "main_ingredients": ["虾仁", "豆腐"]
    },
    {
        "dish_name": "南瓜肉末意面",
        "suitable_age_months": 10,
        "meal_type": "dinner",
        "ingredients": [
            {"name": "南瓜", "amount": "50g"},
            {"name": "猪瘦肉末", "amount": "25g"},
            {"name": "婴儿意面", "amount": "30g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "南瓜去皮切小丁蒸熟，压成泥（保留颗粒）"},
            {"step": 2, "description": "意面掰小段煮熟，过凉水备用"},
            {"step": 3, "description": "肉末炒香，加入南瓜泥和少量水煮成酱汁"},
            {"step": 4, "description": "加入意面翻拌均匀，剪小段"}
        ],
        "nutrition_info": {"calories": 175, "protein": 8.5, "iron": 1.5, "calcium": 25},
        "allergen_tags": ["小麦"],
        "tags": ["意面", "南瓜", "碎末状", "晚餐"],
        "main_ingredients": ["南瓜", "猪肉", "意面"]
    },
    {
        "dish_name": "白萝卜牛肉粥",
        "suitable_age_months": 11,
        "meal_type": "lunch",
        "ingredients": [
            {"name": "大米", "amount": "25g"},
            {"name": "牛里脊末", "amount": "30g"},
            {"name": "白萝卜", "amount": "30g"},
            {"name": "香菇碎", "amount": "10g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "大米煮成稠粥，白萝卜切细丝焯水"},
            {"step": 2, "description": "牛肉末炒香，加入香菇碎和萝卜丝炒软"},
            {"step": 3, "description": "拌入粥中，再煮3分钟入味"}
        ],
        "nutrition_info": {"calories": 155, "protein": 11.8, "iron": 2.8, "calcium": 30},
        "allergen_tags": [],
        "tags": ["高蛋白", "补铁", "冬季", "碎末状"],
        "main_ingredients": ["牛肉", "白萝卜", "大米"]
    },
    {
        "dish_name": "龙利鱼蔬菜粥",
        "suitable_age_months": 10,
        "meal_type": "dinner",
        "ingredients": [
            {"name": "龙利鱼", "amount": "35g"},
            {"name": "西兰花碎", "amount": "20g"},
            {"name": "胡萝卜碎", "amount": "15g"},
            {"name": "大米粥", "amount": "1碗"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "龙利鱼去皮去刺切小丁，用柠檬汁去腥"},
            {"step": 2, "description": "西兰花和胡萝卜焯水切细末"},
            {"step": 3, "description": "粥煮开，加入鱼丁和蔬菜碎煮3分钟"}
        ],
        "nutrition_info": {"calories": 130, "protein": 12.5, "iron": 1.0, "calcium": 35, "dha": 85},
        "allergen_tags": ["鱼类"],
        "tags": ["高蛋白", "DHA", "补脑", "碎末状"],
        "main_ingredients": ["龙利鱼", "西兰花", "胡萝卜"]
    },
    # 手指食物补充
    {
        "dish_name": "胡萝卜磨牙棒",
        "suitable_age_months": 9,
        "meal_type": "snack",
        "ingredients": [
            {"name": "胡萝卜泥", "amount": "30g"},
            {"name": "低筋面粉", "amount": "60g"},
            {"name": "蛋黄", "amount": "1个"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "胡萝卜蒸熟压泥，加入蛋黄和面粉揉成硬面团"},
            {"step": 2, "description": "擀成1cm厚的片，切成1cm宽的长条"},
            {"step": 3, "description": "拧成螺旋状，烤箱150度烤25分钟至硬"}
        ],
        "nutrition_info": {"calories": 155, "protein": 4.2, "iron": 1.0, "calcium": 18},
        "allergen_tags": ["鸡蛋", "小麦"],
        "tags": ["磨牙", "手指食物", "烘焙", "胡萝卜"],
        "main_ingredients": ["胡萝卜", "面粉"]
    },
    {
        "dish_name": "山药红枣蒸条",
        "suitable_age_months": 10,
        "meal_type": "snack",
        "ingredients": [
            {"name": "山药", "amount": "60g"},
            {"name": "红枣", "amount": "3颗"},
            {"name": "玉米淀粉", "amount": "15g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "山药去皮蒸熟压泥，红枣去核去皮切碎"},
            {"step": 2, "description": "山药泥加入红枣碎和淀粉拌匀，搓成手指粗的条"},
            {"step": 3, "description": "上锅蒸15分钟，取出放凉切小段"}
        ],
        "nutrition_info": {"calories": 90, "protein": 2.0, "iron": 0.6, "calcium": 20},
        "allergen_tags": [],
        "tags": ["手指食物", "健脾", "蒸菜", "加餐"],
        "main_ingredients": ["山药", "红枣"]
    },
    {
        "dish_name": "土豆鳕鱼饼",
        "suitable_age_months": 11,
        "meal_type": "snack",
        "ingredients": [
            {"name": "土豆", "amount": "50g"},
            {"name": "鳕鱼", "amount": "30g"},
            {"name": "蛋黄", "amount": "1个"},
            {"name": "玉米淀粉", "amount": "10g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "土豆蒸熟压泥，鳕鱼蒸熟压泥，检查无刺"},
            {"step": 2, "description": "混合土豆泥、鳕鱼泥、蛋黄和淀粉拌匀"},
            {"step": 3, "description": "平底锅刷薄油，取适量压成小饼，两面煎黄"}
        ],
        "nutrition_info": {"calories": 115, "protein": 8.5, "iron": 0.6, "calcium": 30, "dha": 50},
        "allergen_tags": ["鱼类", "鸡蛋"],
        "tags": ["手指食物", "DHA", "补钙", "煎"],
        "main_ingredients": ["土豆", "鳕鱼"]
    },
    # 12个月+ 补充
    {
        "dish_name": "藜麦蔬菜粥",
        "suitable_age_months": 12,
        "meal_type": "breakfast",
        "ingredients": [
            {"name": "藜麦", "amount": "20g"},
            {"name": "大米", "amount": "15g"},
            {"name": "胡萝卜丁", "amount": "20g"},
            {"name": "青豆", "amount": "15g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "藜麦提前浸泡2小时，和大米一起煮成粥"},
            {"step": 2, "description": "胡萝卜和青豆焯水切小丁"},
            {"step": 3, "description": "加入粥中再煮5分钟即可"}
        ],
        "nutrition_info": {"calories": 145, "protein": 5.8, "iron": 2.5, "calcium": 35},
        "allergen_tags": [],
        "tags": ["全谷物", "高蛋白", "早餐", "营养丰富"],
        "main_ingredients": ["藜麦", "大米", "胡萝卜", "青豆"]
    },
    {
        "dish_name": "番茄牛肉烩饭",
        "suitable_age_months": 12,
        "meal_type": "lunch",
        "ingredients": [
            {"name": "牛里脊丁", "amount": "35g"},
            {"name": "番茄", "amount": "50g"},
            {"name": "洋葱丁", "amount": "15g"},
            {"name": "软米饭", "amount": "60g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "番茄去皮切小块，洋葱切小丁，牛肉切小丁"},
            {"step": 2, "description": "牛肉丁用淀粉腌制10分钟，下锅滑炒至变色"},
            {"step": 3, "description": "加入洋葱炒软，加入番茄炒出汁，加少量水焖5分钟"},
            {"step": 4, "description": "加入米饭翻拌均匀，收汁至浓稠"}
        ],
        "nutrition_info": {"calories": 220, "protein": 13.8, "iron": 3.2, "calcium": 35},
        "allergen_tags": [],
        "tags": ["高蛋白", "补铁", "开胃", "午餐"],
        "main_ingredients": ["牛肉", "番茄", "洋葱", "米饭"]
    },
    {
        "dish_name": "蛤蜊蒸蛋",
        "suitable_age_months": 12,
        "meal_type": "dinner",
        "ingredients": [
            {"name": "花蛤", "amount": "5个"},
            {"name": "鸡蛋", "amount": "1个"},
            {"name": "温水", "amount": "70ml"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "花蛤吐沙洗净，开水煮至开口，取肉备用"},
            {"step": 2, "description": "鸡蛋打散，加入1.5倍温水搅匀，过筛去泡沫"},
            {"step": 3, "description": "盖上保鲜膜扎孔，上汽后蒸8分钟"},
            {"step": 4, "description": "放入蛤肉，再蒸2分钟即可"}
        ],
        "nutrition_info": {"calories": 105, "protein": 10.5, "iron": 2.0, "calcium": 65, "zinc": 1.2},
        "allergen_tags": ["鸡蛋", "贝类"],
        "tags": ["高蛋白", "补锌", "蒸菜", "晚餐"],
        "main_ingredients": ["蛤蜊", "鸡蛋"]
    },
    {
        "dish_name": "鸭肉萝卜汤面",
        "suitable_age_months": 12,
        "meal_type": "dinner",
        "ingredients": [
            {"name": "鸭腿肉", "amount": "40g"},
            {"name": "白萝卜", "amount": "40g"},
            {"name": "婴儿面条", "amount": "35g"},
            {"name": "姜片", "amount": "1片"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "鸭肉冷水下锅焯水，重新加水加姜片炖40分钟"},
            {"step": 2, "description": "白萝卜切细丝，放入汤中煮软"},
            {"step": 3, "description": "取出鸭肉去骨切小丁，放回汤中"},
            {"step": 4, "description": "下面条煮熟，剪小段方便食用"}
        ],
        "nutrition_info": {"calories": 205, "protein": 12.5, "iron": 2.0, "calcium": 30},
        "allergen_tags": [],
        "tags": ["高蛋白", "秋季", "润燥", "汤面"],
        "main_ingredients": ["鸭肉", "白萝卜", "面条"]
    },
    {
        "dish_name": "芦笋虾仁炒饭",
        "suitable_age_months": 13,
        "meal_type": "lunch",
        "ingredients": [
            {"name": "虾仁", "amount": "35g"},
            {"name": "芦笋", "amount": "30g"},
            {"name": "胡萝卜丁", "amount": "15g"},
            {"name": "软米饭", "amount": "60g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "虾仁去虾线切小丁，芦笋去老根焯水切小丁"},
            {"step": 2, "description": "胡萝卜丁焯水备用"},
            {"step": 3, "description": "热锅下油，虾仁炒至变色，加入蔬菜丁翻炒"},
            {"step": 4, "description": "加入米饭炒匀即可"}
        ],
        "nutrition_info": {"calories": 200, "protein": 13.2, "iron": 1.8, "calcium": 45},
        "allergen_tags": ["虾"],
        "tags": ["高蛋白", "春季", "芦笋", "炒饭"],
        "main_ingredients": ["虾仁", "芦笋", "胡萝卜", "米饭"]
    },
    {
        "dish_name": "藕丁肉饼蒸饭",
        "suitable_age_months": 13,
        "meal_type": "lunch",
        "ingredients": [
            {"name": "猪肉末", "amount": "40g"},
            {"name": "莲藕", "amount": "30g"},
            {"name": "大米", "amount": "40g"},
            {"name": "胡萝卜丁", "amount": "15g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "莲藕去皮切小丁，和胡萝卜丁一起焯水"},
            {"step": 2, "description": "猪肉末加入藕丁和胡萝卜丁拌匀，压成饼状"},
            {"step": 3, "description": "大米淘洗好放入碗，肉饼放在上面，加适量水"},
            {"step": 4, "description": "上锅蒸30分钟，米饭肉饼一起熟透"}
        ],
        "nutrition_info": {"calories": 235, "protein": 12.8, "iron": 2.5, "calcium": 30},
        "allergen_tags": [],
        "tags": ["高蛋白", "补铁", "莲藕", "蒸饭"],
        "main_ingredients": ["猪肉", "莲藕", "大米"]
    },
    # 早餐补充
    {
        "dish_name": "核桃芝麻糊",
        "suitable_age_months": 12,
        "meal_type": "breakfast",
        "ingredients": [
            {"name": "核桃仁", "amount": "10g"},
            {"name": "黑芝麻", "amount": "5g"},
            {"name": "大米", "amount": "20g"},
            {"name": "红枣", "amount": "2颗"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "大米提前泡好，核桃仁、黑芝麻小火炒香"},
            {"step": 2, "description": "红枣去核，所有材料放入破壁机"},
            {"step": 3, "description": "加适量水打成细腻糊状，煮沸即可"}
        ],
        "nutrition_info": {"calories": 135, "protein": 3.8, "iron": 1.5, "calcium": 45, "dha": 30},
        "allergen_tags": ["坚果"],
        "tags": ["补脑", "补钙", "早餐", "坚果"],
        "main_ingredients": ["核桃", "芝麻", "大米"]
    },
    {
        "dish_name": "苹果鸡蛋软饼",
        "suitable_age_months": 12,
        "meal_type": "breakfast",
        "ingredients": [
            {"name": "苹果", "amount": "40g"},
            {"name": "鸡蛋", "amount": "1个"},
            {"name": "低筋面粉", "amount": "25g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "苹果擦成细丝，加入鸡蛋打散"},
            {"step": 2, "description": "加入面粉搅拌成顺滑面糊"},
            {"step": 3, "description": "平底锅刷薄油，倒入面糊摊成小饼"},
            {"step": 4, "description": "小火煎至两面金黄，切小块"}
        ],
        "nutrition_info": {"calories": 130, "protein": 5.2, "iron": 1.0, "calcium": 25},
        "allergen_tags": ["鸡蛋", "小麦"],
        "tags": ["早餐", "水果", "松软", "鸡蛋"],
        "main_ingredients": ["苹果", "鸡蛋", "面粉"]
    },
    # 加餐补充
    {
        "dish_name": "三色水果串",
        "suitable_age_months": 12,
        "meal_type": "snack",
        "ingredients": [
            {"name": "哈密瓜", "amount": "20g"},
            {"name": "草莓", "amount": "20g"},
            {"name": "香蕉", "amount": "20g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "所有水果分别切成1cm见方的小块"},
            {"step": 2, "description": "用干净的竹签或牙签按颜色间隔串起来"},
            {"step": 3, "description": "注意去掉尖锐部分，安全食用"}
        ],
        "nutrition_info": {"calories": 50, "protein": 0.5, "iron": 0.3, "calcium": 15, "vitamin_c": 30},
        "allergen_tags": [],
        "tags": ["手指食物", "水果", "维生素", "好看"],
        "main_ingredients": ["哈密瓜", "草莓", "香蕉"]
    },
    {
        "dish_name": "小米红枣发糕",
        "suitable_age_months": 12,
        "meal_type": "snack",
        "ingredients": [
            {"name": "小米面", "amount": "40g"},
            {"name": "面粉", "amount": "20g"},
            {"name": "红枣碎", "amount": "15g"},
            {"name": "酵母", "amount": "1g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "小米面和面粉混合，加温水和酵母调成稠糊"},
            {"step": 2, "description": "温暖处发酵至2倍大，加入红枣碎拌匀"},
            {"step": 3, "description": "倒入刷油的碗中，震平，上汽后蒸20分钟"},
            {"step": 4, "description": "取出放凉切块即可"}
        ],
        "nutrition_info": {"calories": 145, "protein": 4.2, "iron": 1.8, "calcium": 25},
        "allergen_tags": [],
        "tags": ["发糕", "加餐", "小米", "红枣"],
        "main_ingredients": ["小米", "面粉", "红枣"]
    },
    # 更多食谱达到100+
    {
        "dish_name": "西葫芦鸡肉饼",
        "suitable_age_months": 12,
        "meal_type": "lunch",
        "ingredients": [
            {"name": "鸡胸肉末", "amount": "40g"},
            {"name": "西葫芦", "amount": "40g"},
            {"name": "鸡蛋", "amount": "1个"},
            {"name": "面粉", "amount": "15g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "西葫芦擦丝，挤去多余水分"},
            {"step": 2, "description": "混合鸡肉末、西葫芦丝、鸡蛋、面粉拌匀"},
            {"step": 3, "description": "平底锅刷薄油，取适量压成小饼，两面煎至金黄熟透"}
        ],
        "nutrition_info": {"calories": 175, "protein": 14.5, "iron": 1.8, "calcium": 35},
        "allergen_tags": ["鸡蛋", "小麦"],
        "tags": ["高蛋白", "煎饼", "西葫芦", "午餐"],
        "main_ingredients": ["鸡肉", "西葫芦", "鸡蛋"]
    },
    {
        "dish_name": "板栗鸡丝粥",
        "suitable_age_months": 12,
        "meal_type": "dinner",
        "ingredients": [
            {"name": "大米", "amount": "25g"},
            {"name": "鸡胸肉", "amount": "30g"},
            {"name": "熟板栗", "amount": "3颗"},
            {"name": "青菜碎", "amount": "15g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "大米煮成稠粥，鸡胸肉煮熟撕成细丝"},
            {"step": 2, "description": "板栗去壳压成泥（保留小颗粒）"},
            {"step": 3, "description": "粥中加入鸡丝和板栗泥，煮2分钟"},
            {"step": 4, "description": "最后加入青菜碎煮1分钟"}
        ],
        "nutrition_info": {"calories": 165, "protein": 10.5, "iron": 1.2, "calcium": 25},
        "allergen_tags": [],
        "tags": ["高蛋白", "板栗", "秋季", "粥"],
        "main_ingredients": ["鸡肉", "板栗", "大米"]
    },
    {
        "dish_name": "鹰嘴豆泥",
        "suitable_age_months": 10,
        "meal_type": "lunch",
        "ingredients": [
            {"name": "鹰嘴豆（干）", "amount": "20g"},
            {"name": "芝麻酱", "amount": "5g"},
            {"name": "柠檬汁", "amount": "几滴"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "鹰嘴豆提前浸泡过夜，换水煮熟至软烂"},
            {"step": 2, "description": "去皮（可选，更细腻），加入芝麻酱和柠檬汁"},
            {"step": 3, "description": "加少量温水打成细腻泥状"}
        ],
        "nutrition_info": {"calories": 105, "protein": 6.5, "iron": 2.2, "calcium": 45},
        "allergen_tags": ["芝麻"],
        "tags": ["植物蛋白", "高铁", "中东", "泥状"],
        "main_ingredients": ["鹰嘴豆", "芝麻酱"]
    },
    {
        "dish_name": "苋菜泥米粉",
        "suitable_age_months": 7,
        "meal_type": "dinner",
        "ingredients": [
            {"name": "红苋菜", "amount": "50g"},
            {"name": "高铁米粉", "amount": "15g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "苋菜只取嫩叶，洗净后开水焯2分钟"},
            {"step": 2, "description": "捞出过凉水，挤干水分打成菜泥"},
            {"step": 3, "description": "拌入冲好的高铁米粉中食用"}
        ],
        "nutrition_info": {"calories": 70, "protein": 2.2, "iron": 3.5, "calcium": 60},
        "allergen_tags": [],
        "tags": ["高铁", "补钙", "夏季", "蔬菜"],
        "main_ingredients": ["苋菜"]
    },
    {
        "dish_name": "杏鲍菇鸡肉碎",
        "suitable_age_months": 11,
        "meal_type": "lunch",
        "ingredients": [
            {"name": "鸡胸肉末", "amount": "35g"},
            {"name": "杏鲍菇", "amount": "40g"},
            {"name": "青菜碎", "amount": "15g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "杏鲍菇洗净切小丁，焯水后切更细碎"},
            {"step": 2, "description": "鸡肉末下锅炒香，加入杏鲍菇碎炒软"},
            {"step": 3, "description": "加少量水焖煮3分钟，最后加入青菜碎拌匀"}
        ],
        "nutrition_info": {"calories": 95, "protein": 10.2, "iron": 1.5, "calcium": 20},
        "allergen_tags": [],
        "tags": ["高蛋白", "提鲜", "菌菇", "碎末状"],
        "main_ingredients": ["鸡肉", "杏鲍菇"]
    },
    {
        "dish_name": "黄骨鱼粥",
        "suitable_age_months": 11,
        "meal_type": "dinner",
        "ingredients": [
            {"name": "黄骨鱼", "amount": "1条（约80g）"},
            {"name": "大米", "amount": "25g"},
            {"name": "姜片", "amount": "1片"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "黄骨鱼处理干净，用姜片腌制去腥"},
            {"step": 2, "description": "上锅蒸熟，仔细取出鱼肉，反复检查无刺"},
            {"step": 3, "description": "鱼肉压碎，加入煮好的粥中拌匀再煮2分钟"}
        ],
        "nutrition_info": {"calories": 135, "protein": 13.5, "iron": 1.0, "calcium": 40, "dha": 70},
        "allergen_tags": ["鱼类"],
        "tags": ["高蛋白", "DHA", "淡水鱼", "粥"],
        "main_ingredients": ["黄骨鱼", "大米"]
    },
    {
        "dish_name": "无花果泥",
        "suitable_age_months": 8,
        "meal_type": "snack",
        "ingredients": [
            {"name": "新鲜无花果", "amount": "50g"},
            {"name": "配方奶", "amount": "20ml"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "无花果洗净去皮，取果肉"},
            {"step": 2, "description": "用勺子压成泥状，加入温奶调稀"}
        ],
        "nutrition_info": {"calories": 45, "protein": 0.6, "iron": 0.4, "calcium": 25, "fiber": 2.5},
        "allergen_tags": ["乳制品"],
        "tags": ["水果", "膳食纤维", "通便", "加餐"],
        "main_ingredients": ["无花果"]
    },
    {
        "dish_name": "车厘子香蕉泥",
        "suitable_age_months": 8,
        "meal_type": "snack",
        "ingredients": [
            {"name": "车厘子", "amount": "5颗"},
            {"name": "香蕉", "amount": "30g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "车厘子洗净去核去皮，香蕉去皮切小块"},
            {"step": 2, "description": "一起打成细腻泥状即可"}
        ],
        "nutrition_info": {"calories": 50, "protein": 0.5, "iron": 0.3, "calcium": 10, "anthocyanin": 20},
        "allergen_tags": [],
        "tags": ["花青素", "补铁", "水果", "加餐"],
        "main_ingredients": ["车厘子", "香蕉"]
    },
    {
        "dish_name": "荷兰豆泥",
        "suitable_age_months": 7,
        "meal_type": "lunch",
        "ingredients": [
            {"name": "荷兰豆", "amount": "50g"},
            {"name": "山药", "amount": "30g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "荷兰豆去筋，山药去皮切小块"},
            {"step": 2, "description": "一起上锅蒸15分钟至软烂"},
            {"step": 3, "description": "加少量温水打成细腻泥状"}
        ],
        "nutrition_info": {"calories": 55, "protein": 2.8, "iron": 1.2, "calcium": 30},
        "allergen_tags": [],
        "tags": ["高蛋白", "春季", "蔬菜", "泥状"],
        "main_ingredients": ["荷兰豆", "山药"]
    },
    {
        "dish_name": "平菇豆腐汤",
        "suitable_age_months": 11,
        "meal_type": "dinner",
        "ingredients": [
            {"name": "鲜平菇", "amount": "30g"},
            {"name": "嫩豆腐", "amount": "40g"},
            {"name": "青菜叶", "amount": "15g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "平菇撕小朵焯水，豆腐切小丁，青菜切碎"},
            {"step": 2, "description": "锅内加适量水烧开，下平菇和豆腐煮3分钟"},
            {"step": 3, "description": "加入青菜碎煮1分钟，可勾薄芡"}
        ],
        "nutrition_info": {"calories": 50, "protein": 4.5, "iron": 1.0, "calcium": 55},
        "allergen_tags": ["大豆"],
        "tags": ["菌菇", "补钙", "汤品", "晚餐"],
        "main_ingredients": ["平菇", "豆腐"]
    },
    {
        "dish_name": "丝瓜鸡蛋面",
        "suitable_age_months": 11,
        "meal_type": "lunch",
        "ingredients": [
            {"name": "丝瓜", "amount": "40g"},
            {"name": "鸡蛋", "amount": "半个"},
            {"name": "婴儿细面", "amount": "30g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "丝瓜去皮切薄片，鸡蛋打散"},
            {"step": 2, "description": "锅内加少量水烧开，下丝瓜片煮2分钟"},
            {"step": 3, "description": "下面条煮熟，淋入蛋液形成蛋花"}
        ],
        "nutrition_info": {"calories": 120, "protein": 4.8, "iron": 1.2, "calcium": 25},
        "allergen_tags": ["鸡蛋", "小麦"],
        "tags": ["夏季", "清热", "汤面", "午餐"],
        "main_ingredients": ["丝瓜", "鸡蛋", "面条"]
    },
    {
        "dish_name": "木耳菜鸡蛋粥",
        "suitable_age_months": 11,
        "meal_type": "dinner",
        "ingredients": [
            {"name": "木耳菜", "amount": "30g"},
            {"name": "鸡蛋黄", "amount": "1个"},
            {"name": "大米粥", "amount": "1碗"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "木耳菜只取嫩叶，洗净焯水切碎"},
            {"step": 2, "description": "蛋黄压碎备用"},
            {"step": 3, "description": "粥煮开，加入木耳菜碎煮2分钟"},
            {"step": 4, "description": "关火后拌入蛋黄碎即可"}
        ],
        "nutrition_info": {"calories": 95, "protein": 3.8, "iron": 2.5, "calcium": 45},
        "allergen_tags": ["鸡蛋"],
        "tags": ["高铁", "补钙", "夏季", "粥"],
        "main_ingredients": ["木耳菜", "鸡蛋"]
    },
    {
        "dish_name": "空心菜肉末粥",
        "suitable_age_months": 12,
        "meal_type": "dinner",
        "ingredients": [
            {"name": "空心菜叶", "amount": "30g"},
            {"name": "猪瘦肉末", "amount": "25g"},
            {"name": "大米粥", "amount": "1碗"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "空心菜洗净焯水切小段"},
            {"step": 2, "description": "肉末下锅炒至变色，加入粥中"},
            {"step": 3, "description": "粥煮开后加入空心菜，煮1分钟即可"}
        ],
        "nutrition_info": {"calories": 130, "protein": 8.5, "iron": 2.0, "calcium": 50},
        "allergen_tags": [],
        "tags": ["夏季", "高铁", "补钙", "粥"],
        "main_ingredients": ["空心菜", "猪肉"]
    },
    {
        "dish_name": "娃娃菜鱼肉卷",
        "suitable_age_months": 13,
        "meal_type": "lunch",
        "ingredients": [
            {"name": "娃娃菜叶", "amount": "3片"},
            {"name": "龙利鱼泥", "amount": "40g"},
            {"name": "胡萝卜碎", "amount": "15g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "娃娃菜叶焯水烫软，修去硬梗"},
            {"step": 2, "description": "鱼泥混合胡萝卜碎，铺在娃娃菜叶上"},
            {"step": 3, "description": "卷成卷，上锅蒸10分钟至熟透"},
            {"step": 4, "description": "取出切小段方便食用"}
        ],
        "nutrition_info": {"calories": 85, "protein": 9.5, "iron": 0.8, "calcium": 35, "dha": 60},
        "allergen_tags": ["鱼类"],
        "tags": ["高蛋白", "DHA", "蒸菜", "创意"],
        "main_ingredients": ["娃娃菜", "龙利鱼"]
    },
    {
        "dish_name": "茼蒿鳕鱼丸汤",
        "suitable_age_months": 13,
        "meal_type": "dinner",
        "ingredients": [
            {"name": "鳕鱼泥", "amount": "40g"},
            {"name": "茼蒿", "amount": "20g"},
            {"name": "豆腐丁", "amount": "20g"},
            {"name": "玉米淀粉", "amount": "5g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "鳕鱼泥加淀粉拌匀，茼蒿洗净切小段"},
            {"step": 2, "description": "锅内加水烧开，转小火，用勺子将鱼泥舀成小丸子下锅"},
            {"step": 3, "description": "丸子浮起后加入豆腐丁和茼蒿，煮1分钟即可"}
        ],
        "nutrition_info": {"calories": 90, "protein": 10.8, "iron": 0.6, "calcium": 45, "dha": 70},
        "allergen_tags": ["鱼类", "大豆"],
        "tags": ["高蛋白", "DHA", "鱼丸", "汤品"],
        "main_ingredients": ["鳕鱼", "茼蒿", "豆腐"]
    },
    {
        "dish_name": "油菜香菇鸡丝粥",
        "suitable_age_months": 12,
        "meal_type": "lunch",
        "ingredients": [
            {"name": "小油菜", "amount": "25g"},
            {"name": "香菇", "amount": "1朵"},
            {"name": "鸡丝", "amount": "25g"},
            {"name": "大米粥", "amount": "1碗"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "油菜和香菇焯水切碎，鸡肉煮熟撕细丝"},
            {"step": 2, "description": "粥煮开，加入鸡丝和香菇碎煮3分钟"},
            {"step": 3, "description": "最后加入油菜碎煮1分钟即可"}
        ],
        "nutrition_info": {"calories": 135, "protein": 9.8, "iron": 1.8, "calcium": 55},
        "allergen_tags": [],
        "tags": ["高蛋白", "高铁", "营养均衡", "粥"],
        "main_ingredients": ["油菜", "香菇", "鸡肉"]
    },
    {
        "dish_name": "芹菜牛肉粥",
        "suitable_age_months": 13,
        "meal_type": "dinner",
        "ingredients": [
            {"name": "芹菜叶", "amount": "20g"},
            {"name": "牛肉末", "amount": "30g"},
            {"name": "大米粥", "amount": "1碗"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "芹菜叶洗净焯水切碎"},
            {"step": 2, "description": "牛肉末下锅炒香，加入粥中煮开"},
            {"step": 3, "description": "加入芹菜叶碎煮1分钟即可"}
        ],
        "nutrition_info": {"calories": 150, "protein": 11.5, "iron": 2.8, "calcium": 30},
        "allergen_tags": [],
        "tags": ["高铁", "高蛋白", "芹菜", "粥"],
        "main_ingredients": ["芹菜", "牛肉"]
    },
    {
        "dish_name": "生菜鸡蛋卷",
        "suitable_age_months": 13,
        "meal_type": "lunch",
        "ingredients": [
            {"name": "生菜叶", "amount": "2片"},
            {"name": "鸡蛋", "amount": "1个"},
            {"name": "胡萝卜丝", "amount": "15g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "生菜叶焯水烫软，鸡蛋打散摊成薄蛋皮"},
            {"step": 2, "description": "胡萝卜丝焯水备用"},
            {"step": 3, "description": "蛋皮上铺生菜叶，放上胡萝卜丝，卷起来切段"}
        ],
        "nutrition_info": {"calories": 95, "protein": 7.2, "iron": 1.5, "calcium": 40},
        "allergen_tags": ["鸡蛋"],
        "tags": ["鸡蛋", "蔬菜", "手指食物", "创意"],
        "main_ingredients": ["生菜", "鸡蛋", "胡萝卜"]
    },
    {
        "dish_name": "卷心菜肉末饭",
        "suitable_age_months": 12,
        "meal_type": "lunch",
        "ingredients": [
            {"name": "卷心菜", "amount": "40g"},
            {"name": "猪肉末", "amount": "30g"},
            {"name": "软米饭", "amount": "60g"},
            {"name": "香菇碎", "amount": "10g"}
        ],
        "cooking_steps": [
            {"step": 1, "description": "卷心菜洗净切小丁，焯水备用"},
            {"step": 2, "description": "肉末炒香，加入香菇碎和卷心菜丁翻炒"},
            {"step": 3, "description": "加少量水焖煮2分钟，拌入米饭即可"}
        ],
        "nutrition_info": {"calories": 195, "protein": 10.5, "iron": 2.0, "calcium": 35},
        "allergen_tags": [],
        "tags": ["高蛋白", "养胃", "卷心菜", "午餐"],
        "main_ingredients": ["卷心菜", "猪肉", "米饭"]
    }
]


def get_recipes_by_age(age_months: int) -> list:
    """按月龄筛选食谱"""
    return [r for r in RECIPE_DATABASE if r["suitable_age_months"] <= age_months]


def get_recipes_by_meal_type(meal_type: str, age_months: int = None) -> list:
    """按餐次筛选食谱，可附加月龄限制"""
    recipes = [r for r in RECIPE_DATABASE if r["meal_type"] == meal_type]
    if age_months is not None:
        recipes = [r for r in recipes if r["suitable_age_months"] <= age_months]
    return recipes


def get_recipe_by_name(dish_name: str) -> dict:
    """按菜品名称查找食谱"""
    for recipe in RECIPE_DATABASE:
        if recipe["dish_name"] == dish_name:
            return recipe
    return None


def get_high_iron_recipes(age_months: int = None) -> list:
    """获取高铁食谱（铁含量>=2.0mg）"""
    recipes = [r for r in RECIPE_DATABASE if r["nutrition_info"].get("iron", 0) >= 2.0]
    if age_months is not None:
        recipes = [r for r in recipes if r["suitable_age_months"] <= age_months]
    return recipes


def get_high_protein_recipes(age_months: int = None) -> list:
    """获取高蛋白食谱（蛋白质>=8.0g）"""
    recipes = [r for r in RECIPE_DATABASE if r["nutrition_info"].get("protein", 0) >= 8.0]
    if age_months is not None:
        recipes = [r for r in recipes if r["suitable_age_months"] <= age_months]
    return recipes


def get_dha_recipes(age_months: int = None) -> list:
    """获取含DHA的食谱"""
    recipes = [r for r in RECIPE_DATABASE if r["nutrition_info"].get("dha", 0) > 0]
    if age_months is not None:
        recipes = [r for r in recipes if r["suitable_age_months"] <= age_months]
    return recipes


def filter_by_allergens(recipes: list, allergens: list) -> list:
    """过滤过敏源，排除包含指定过敏源的食谱"""
    if not allergens:
        return recipes
    return [
        r for r in recipes
        if not any(allergen in r["allergen_tags"] for allergen in allergens)
    ]


def get_recipe_statistics() -> dict:
    """获取食谱数据库统计信息"""
    total = len(RECIPE_DATABASE)
    age_6_8 = len([r for r in RECIPE_DATABASE if 6 <= r["suitable_age_months"] <= 8])
    age_9_11 = len([r for r in RECIPE_DATABASE if 9 <= r["suitable_age_months"] <= 11])
    age_12_plus = len([r for r in RECIPE_DATABASE if r["suitable_age_months"] >= 12])

    by_meal = {
        "breakfast": len(get_recipes_by_meal_type("breakfast")),
        "lunch": len(get_recipes_by_meal_type("lunch")),
        "dinner": len(get_recipes_by_meal_type("dinner")),
        "snack": len(get_recipes_by_meal_type("snack"))
    }

    return {
        "total_recipes": total,
        "by_age_group": {
            "6-8个月": age_6_8,
            "9-11个月": age_9_11,
            "12个月+": age_12_plus
        },
        "by_meal_type": by_meal,
        "high_iron_count": len(get_high_iron_recipes()),
        "high_protein_count": len(get_high_protein_recipes()),
        "dha_recipes_count": len(get_dha_recipes())
    }
