"""
Basic Usage Example
基本使用示例

演示如何使用 Superpowers 框架。
"""
import asyncio
from superpowers.core import SkillRegistry, SkillExecutor, SkillContext


async def main():
    # 1. 创建注册表
    registry = SkillRegistry()
    
    # 2. 自动发现技能
    count = registry.discover_skills("superpowers/skills")
    print(f"Discovered {count} skills")
    
    # 3. 列出所有技能
    print("\nAvailable skills:")
    for skill in registry.list_skills():
        print(f"  - {skill['name']}: {skill['description']}")
    
    # 4. 创建执行上下文
    context = SkillContext(
        working_dir=".",
        project_info={"name": "demo-project", "type": "python"}
    )
    
    # 5. 创建执行器
    executor = SkillExecutor(registry)
    
    # 6. 执行技能（示例：读取本文件）
    print("\nExecuting 'read_file' skill...")
    result = await executor.execute(
        "read_file",
        context,
        file_path="superpowers/examples/basic_usage.py"
    )
    
    print(f"Result: success={result.success}")
    print(f"Message: {result.message}")
    if result.success:
        print(f"Content length: {len(result.data['content'])}")
        print(f"Suggested next skills: {result.suggested_next_skills}")


if __name__ == "__main__":
    asyncio.run(main())
