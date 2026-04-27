"""
对话路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Recipe, Conversation
from app.schemas import ConversationMessage, ConversationResponse
from app.routers.auth import get_current_user

router = APIRouter()


@router.post("/{recipe_id}")
async def create_conversation(
    recipe_id: int,
    message: ConversationMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建对话消息"""
    # 验证食谱权限
    recipe = db.query(Recipe).filter(
        Recipe.id == recipe_id,
        Recipe.user_id == current_user.id
    ).first()
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # 保存用户消息
    user_msg = Conversation(
        recipe_id=recipe_id,
        user_id=current_user.id,
        message_type="user",
        content=message.content,
        extra_data=message.metadata or {}
    )
    db.add(user_msg)
    db.commit()
    
    # TODO: 这里应该调用调整服务生成助手回复
    # 暂时返回占位回复
    assistant_content = "收到您的反馈，正在为您调整食谱..."
    
    assistant_msg = Conversation(
        recipe_id=recipe_id,
        user_id=current_user.id,
        message_type="assistant",
        content=assistant_content,
        extra_data={}
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)
    
    return assistant_msg


@router.get("/{recipe_id}")
async def get_conversations(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取对话历史"""
    recipe = db.query(Recipe).filter(
        Recipe.id == recipe_id,
        Recipe.user_id == current_user.id
    ).first()
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    conversations = db.query(Conversation).filter(
        Conversation.recipe_id == recipe_id
    ).order_by(Conversation.created_at.asc()).all()
    
    return conversations
