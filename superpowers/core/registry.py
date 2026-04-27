"""
Skill Registry
技能注册表

管理所有已注册的技能，支持自动发现和动态加载。
"""
import os
import importlib
import inspect
from typing import Dict, List, Type, Optional

from .skill import Skill


class SkillRegistry:
    """技能注册表
    
    负责：
    1. 注册技能
    2. 发现技能文件
    3. 获取技能信息
    4. 动态加载技能
    """
    
    def __init__(self):
        self._registry: Dict[str, Type[Skill]] = {}
    
    def register(self, skill_class: Type[Skill]) -> None:
        """注册一个技能类"""
        name = skill_class.get_name()
        if name in self._registry:
            print(f"Warning: Skill '{name}' already registered, overwriting")
        self._registry[name] = skill_class
        print(f"Registered skill: {name}")
    
    def get_skill(self, name: str) -> Optional[Type[Skill]]:
        """根据名称获取技能类"""
        return self._registry.get(name)
    
    def list_skills(self) -> List[Dict[str, str]]:
        """列出所有已注册技能"""
        return [
            {
                "name": skill_cls.get_name(),
                "description": skill_cls.get_description(),
                "version": getattr(skill_cls, 'version', '1.0.0'),
                "tags": getattr(skill_cls, 'tags', []),
            }
            for skill_cls in self._registry.values()
        ]
    
    def discover_skills(self, directory: str) -> int:
        """在指定目录自动发现并加载技能
        
        发现所有 .py 文件，尝试从中提取 Skill 子类并注册。
        
        Returns:
            发现并注册的技能数量
        """
        count = 0
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py") and not file.startswith("_"):
                    # 获取模块路径
                    rel_path = os.path.relpath(os.path.join(root, file), ".")
                    module_path = rel_path.replace(os.sep, ".")[:-3]
                    
                    try:
                        module = importlib.import_module(module_path)
                        # 查找模块中的所有 Skill 子类
                        for name, obj in inspect.getmembers(module):
                            if inspect.isclass(obj) and issubclass(obj, Skill) and obj != Skill:
                                if obj.get_name() and obj.get_name() != "":
                                    self.register(obj)
                                    count += 1
                    except Exception as e:
                        print(f"Error loading {module_path}: {e}")
                        continue
        return count
    
    def has_skill(self, name: str) -> bool:
        """检查技能是否存在"""
        return name in self._registry
    
    def create_skill_instance(self, name: str) -> Optional[Skill]:
        """创建技能实例"""
        skill_cls = self.get_skill(name)
        if skill_cls:
            return skill_cls()
        return None
