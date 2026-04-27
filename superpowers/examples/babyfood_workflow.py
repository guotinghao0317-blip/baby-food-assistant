"""
Baby Food Assistant Workflow Example
宝宝辅食助手完整工作流示例

演示如何使用 Superpowers 框架串联宝宝辅食生成流程。
"""
import asyncio
from superpowers.core import SkillRegistry, SkillExecutor, SkillContext


async def baby_recipe_generation_workflow(baby_info: dict, working_dir: str):
    """宝宝食谱生成完整工作流
    
    流程：
    1. 分析宝宝信息 → 计算营养需求
    2. 根据营养需求生成一周食谱
    3. 展示食谱总结
    """
    # 初始化框架
    registry = SkillRegistry()
    registry.discover_skills("superpowers/skills")
    executor = SkillExecutor(registry)
    
    # 创建上下文
    context = SkillContext(
        working_dir=working_dir,
        project_info={"name": "baby-food-assistant"}
    )
    
    # 链式执行：分析 -> 生成
    results = await executor.execute_chain(
        initial_skill="analyze_baby_info",
        context=context,
        max_steps=5,
        baby_info=baby_info
    )
    
    # 输出结果
    print("\n=== Workflow Complete ===")
    for i, result in enumerate(results):
        print(f"Step {i+1}: {result.message} (success={result.success})")
    
    return results


if __name__ == "__main__":
    # 示例宝宝信息
    sample_baby = {
        "name": "小明",
        "age_months": 8,
        "weight": 8.5,
        "height": 70,
        "feeding_stage": "可吃泥糊状",
        "teething_status": "已出2颗牙",
        "allergies": ["牛奶"],
        "liked_ingredients": ["南瓜", "胡萝卜"]
    }
    
    asyncio.run(baby_recipe_generation_workflow(sample_baby, "."))
