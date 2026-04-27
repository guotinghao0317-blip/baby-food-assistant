#!/usr/bin/env python3
"""
测试meal_type去重逻辑
"""
import sqlite3
import json
from collections import defaultdict

# 连接数据库
db_path = "/Users/jiayindeng/baby-food-assistant/backend/babyfood.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查询最近的recipe_id
cursor.execute("""
    SELECT id FROM recipe_details
    ORDER BY id DESC
    LIMIT 100
""")
recent_recipes = cursor.fetchall()

if not recent_recipes:
    print("❌ 数据库中没有recipe数据")
    exit(1)

# 找出包含最多菜品的recipe
cursor.execute("""
    SELECT recipe_id, COUNT(*) as dish_count
    FROM recipe_details
    GROUP BY recipe_id
    ORDER BY dish_count DESC
    LIMIT 5
""")
top_recipes = cursor.fetchall()

print("📋 最近的recipes及其菜品数量：")
for recipe_id, count in top_recipes:
    print(f"  recipe_id {recipe_id}: {count} 道菜")

# 选择菜品最多的recipe进行测试
test_recipe_id = top_recipes[0][0]
print(f"\n🔍 测试recipe_id: {test_recipe_id}")

# 查询该recipe的所有菜品
cursor.execute("""
    SELECT day_of_week, meal_type, dish_name
    FROM recipe_details
    WHERE recipe_id = ?
    ORDER BY day_of_week, meal_type
""", (test_recipe_id,))

dishes = cursor.fetchall()

if not dishes:
    print(f"❌ recipe_id {test_recipe_id} 没有菜品数据")
    exit(1)

print(f"\n✅ 找到 {len(dishes)} 道菜品")

# 检查去重情况
day_meal_dishes = defaultdict(list)
dish_names = set()
duplicates_found = False
day_meal_duplicates = []

for day, meal_type, dish_name in dishes:
    key = (day, meal_type)
    day_meal_dishes[key].append(dish_name)

    # 检查菜名重复
    if dish_name in dish_names:
        duplicates_found = True
    dish_names.add(dish_name)

print("\n📊 检查结果：")

# 检查每天每餐是否只有一道菜
print("\n【检查1】每天每餐去重情况：")
for day in range(1, 8):
    for meal in ['breakfast', 'lunch', 'dinner', "snack"]:
        key = (day, meal)
        dishes_for_meal = day_meal_dishes.get(key, [])
        if len(dishes_for_meal) > 1:
            print(f"❌ 第{day}天{meal}: 发现 {len(dishes_for_meal)} 道菜 - {dishes_for_meal}")
            day_meal_duplicates.append((day, meal, dishes_for_meal))
            duplicates_found = True
        elif len(dishes_for_meal) == 1:
            print(f"✅ 第{day}天{meal}: 1道菜")
        else:
            print(f"⚠️  第{day}天{meal}: 无菜品")

# 检查菜品名称重复
print(f"\n【检查2】菜品名称重复：{'✅ 无重复' if not duplicates_found else '❌ 发现重复'}")

# 统计信息
print(f"\n📈 统计信息：")
print(f"- 总菜品数：{len(dishes)}")
print(f"- 唯一菜品数：{len(dish_names)}")
print(f"- 重复菜品数：{len(dishes) - len(dish_names)}")

# 检查是否有7天的数据
days = set(day for day, _, _ in dishes)
print(f"- 覆盖天数：{sorted(days)}")
print(f"- 天数完整性：{'✅ 7天完整' if len(days) == 7 else '❌ 只有' + str(len(days)) + '天'}")

conn.close()

# 最终结果
print("\n" + "="*50)
if duplicates_found or len(days) != 7:
    print("❌ 测试失败：发现问题")
    if day_meal_duplicates:
        print("\n详细问题：")
        for day, meal, dishes in day_meal_duplicates:
            print(f"  - 第{day}天{meal}: {len(dishes)}道菜 - {dishes}")
    exit(1)
else:
    print("✅ 测试通过：所有检查项正常")
    exit(0)
