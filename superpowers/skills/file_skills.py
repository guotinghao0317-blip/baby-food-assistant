"""
File Operation Skills
文件操作技能集合

演示如何在Superpowers框架中定义技能。
"""
import os
from typing import Dict, Any

from superpowers.core.skill import Skill, SkillContext, SkillResult


class ReadFileSkill(Skill):
    """读取文件技能
    
    读取指定路径的文件内容。
    """
    name = "read_file"
    description = "读取文本文件内容"
    version = "1.0.0"
    author = "superpowers"
    tags = ["file", "read", "io"]
    
    @classmethod
    def get_name(cls) -> str:
        return cls.name
    
    @classmethod
    def get_description(cls) -> str:
        return cls.description
    
    async def can_execute(self, context: SkillContext, file_path: str) -> bool:
        """检查文件是否存在且可读"""
        full_path = os.path.join(context.working_dir, file_path)
        return os.path.exists(full_path) and os.access(full_path, os.R_OK)
    
    async def execute(self, context: SkillContext, file_path: str) -> SkillResult:
        """读取文件内容"""
        full_path = os.path.join(context.working_dir, file_path)
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return SkillResult(
                success=True,
                data={
                    "file_path": file_path,
                    "content": content,
                    "size_bytes": len(content.encode('utf-8'))
                },
                message=f"Successfully read {len(content.splitlines())} lines from {file_path}",
                suggested_next_skills=["analyze_content"]
            )
        except Exception as e:
            return SkillResult(
                success=False,
                message=f"Failed to read file: {str(e)}"
            )


class WriteFileSkill(Skill):
    """写入文件技能
    
    将内容写入指定路径的文件。
    """
    name = "write_file"
    description = "写入内容到文件"
    version = "1.0.0"
    author = "superpowers"
    tags = ["file", "write", "io"]
    
    @classmethod
    def get_name(cls) -> str:
        return cls.name
    
    @classmethod
    def get_description(cls) -> str:
        return cls.description
    
    async def can_execute(self, context: SkillContext, file_path: str, content: str) -> bool:
        """检查目录是否可写"""
        full_path = os.path.join(context.working_dir, file_path)
        directory = os.path.dirname(full_path)
        return os.path.exists(directory) and os.access(directory, os.W_OK)
    
    async def execute(self, context: SkillContext, file_path: str, content: str) -> SkillResult:
        """写入文件内容"""
        full_path = os.path.join(context.working_dir, file_path)
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return SkillResult(
                success=True,
                data={
                    "file_path": file_path,
                    "bytes_written": len(content.encode('utf-8'))
                },
                message=f"Successfully wrote {len(content.encode('utf-8'))} bytes to {file_path}",
                suggested_next_skills=[]
            )
        except Exception as e:
            return SkillResult(
                success=False,
                message=f"Failed to write file: {str(e)}"
            )
