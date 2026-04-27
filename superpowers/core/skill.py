"""
Skill Base Class
技能基类定义

所有具体技能都需要继承这个基类，并实现必要的方法。
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field


class SkillContext(BaseModel):
    """技能执行上下文
    
    包含执行技能所需的环境信息：
    - 当前工作目录
    - 项目信息
    - 对话历史
    - 其他元数据
    """
    working_dir: str = Field(description="当前工作目录")
    project_info: Dict[str, Any] = Field(default_factory=dict, description="项目信息")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="对话历史")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="其他元数据")


class SkillResult(BaseModel):
    """技能执行结果
    
    统一的返回格式，包含：
    - 是否成功
    - 结果数据
    - 消息/错误信息
    - 后续建议技能
    """
    success: bool = Field(description="执行是否成功")
    data: Optional[Dict[str, Any]] = Field(default=None, description="结果数据")
    message: str = Field(default="", description="返回消息/错误信息")
    suggested_next_skills: List[str] = Field(default_factory=list, description="建议下一步执行的技能")


class Skill(ABC):
    """技能基类
    
    所有具体技能必须继承此类并实现抽象方法。
    """
    
    # 技能元数据
    name: str = ""              # 技能唯一名称
    description: str = ""       # 技能描述
    version: str = "1.0.0"     # 版本
    author: str = ""           # 作者
    tags: List[str] = []       # 标签，用于分类和搜索
    
    @classmethod
    @abstractmethod
    def get_name(cls) -> str:
        """获取技能名称"""
        return cls.name
    
    @classmethod
    @abstractmethod
    def get_description(cls) -> str:
        """获取技能描述"""
        return cls.description
    
    @abstractmethod
    async def can_execute(self, context: SkillContext, **kwargs) -> bool:
        """检查是否可以执行此技能
        
        可以根据当前上下文和参数判断技能是否适用于当前情况。
        """
        return True
    
    @abstractmethod
    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """执行技能
        
        Args:
            context: 执行上下文
            **kwargs: 技能参数
            
        Returns:
            SkillResult: 执行结果
        """
        pass
    
    def __str__(self) -> str:
        return f"{self.name} v{self.version}: {self.description}"
