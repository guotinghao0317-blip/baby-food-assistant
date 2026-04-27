"""
Skill Executor
技能执行器

负责执行技能，处理上下文管理，串联执行流程。
"""
from typing import Dict, List, Optional, Any

from .skill import Skill, SkillContext, SkillResult
from .registry import SkillRegistry


class SkillExecutor:
    """技能执行器
    
    主要职责：
    1. 创建上下文
    2. 执行技能
    3. 处理执行结果
    4. 支持链式执行（根据技能推荐执行下一个技能）
    """
    
    def __init__(self, registry: SkillRegistry):
        self.registry = registry
    
    async def execute(
        self,
        skill_name: str,
        context: SkillContext,
        **kwargs
    ) -> SkillResult:
        """执行指定技能
        
        Args:
            skill_name: 技能名称
            context: 执行上下文
            **kwargs: 技能参数
        
        Returns:
            SkillResult: 执行结果
        """
        skill = self.registry.create_skill_instance(skill_name)
        if not skill:
            return SkillResult(
                success=False,
                message=f"Skill '{skill_name}' not found in registry"
            )
        
        # 检查是否可以执行
        can_exec = await skill.can_execute(context, **kwargs)
        if not can_exec:
            return SkillResult(
                success=False,
                message=f"Skill '{skill_name}' cannot execute in current context"
            )
        
        # 执行技能
        try:
            result = await skill.execute(context, **kwargs)
            return result
        except Exception as e:
            return SkillResult(
                success=False,
                message=f"Skill '{skill_name}' execution error: {str(e)}"
            )
    
    async def execute_chain(
        self,
        initial_skill: str,
        context: SkillContext,
        max_steps: int = 10,
        **kwargs
    ) -> List[SkillResult]:
        """链式执行技能
        
        根据每个技能返回的建议下一步自动继续执行，直到完成或达到最大步数。
        
        Args:
            initial_skill: 起始技能
            context: 执行上下文
            max_steps: 最大执行步数
            **kwargs: 初始技能参数
        
        Returns:
            所有执行结果列表
        """
        results: List[SkillResult] = []
        current_skill = initial_skill
        current_kwargs = kwargs
        steps = 0
        
        while current_skill and steps < max_steps:
            result = await self.execute(current_skill, context, **current_kwargs)
            results.append(result)
            steps += 1
            
            if not result.success or not result.suggested_next_skills:
                break
            
            # 执行第一个建议的下一个技能
            current_skill = result.suggested_next_skills[0]
            current_kwargs = result.data or {}
        
        return results
    
    def list_available_skills(self) -> List[Dict[str, Any]]:
        """列出所有可用技能"""
        return self.registry.list_skills()
