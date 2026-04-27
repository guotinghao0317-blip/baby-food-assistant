"""
宝宝信息路由
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Baby, NutritionRequirement
from app.schemas import BabyCreate, BabyResponse, NutritionRequirementResponse
from app.routers.auth import get_current_user
from app.services.nutrition import calculate_nutrition_requirements

router = APIRouter()


@router.get("", response_model=List[BabyResponse])
async def list_babies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的所有宝宝信息"""
    babies = db.query(Baby).filter(Baby.user_id == current_user.id).all()
    return babies


@router.post("", response_model=BabyResponse)
async def create_baby(
    baby_data: BabyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建宝宝信息"""
    db_baby = Baby(user_id=current_user.id, **baby_data.dict())
    db.add(db_baby)
    db.commit()
    db.refresh(db_baby)
    
    # 自动计算营养需求
    nutrition = calculate_nutrition_requirements(db_baby)
    db_nutrition = NutritionRequirement(baby_id=db_baby.id, **nutrition)
    db.add(db_nutrition)
    db.commit()
    
    return db_baby


@router.get("/{baby_id}", response_model=BabyResponse)
async def get_baby(
    baby_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取宝宝信息"""
    baby = db.query(Baby).filter(
        Baby.id == baby_id,
        Baby.user_id == current_user.id
    ).first()
    
    if not baby:
        raise HTTPException(status_code=404, detail="Baby not found")
    
    return baby


@router.put("/{baby_id}", response_model=BabyResponse)
async def update_baby(
    baby_id: int,
    baby_data: BabyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新宝宝信息"""
    baby = db.query(Baby).filter(
        Baby.id == baby_id,
        Baby.user_id == current_user.id
    ).first()
    
    if not baby:
        raise HTTPException(status_code=404, detail="Baby not found")
    
    # 更新字段
    for key, value in baby_data.dict().items():
        setattr(baby, key, value)
    
    db.commit()
    db.refresh(baby)
    
    # 重新计算营养需求
    nutrition = calculate_nutrition_requirements(baby)
    existing_nutrition = db.query(NutritionRequirement).filter(
        NutritionRequirement.baby_id == baby_id
    ).first()
    
    if existing_nutrition:
        for key, value in nutrition.items():
            setattr(existing_nutrition, key, value)
    else:
        db_nutrition = NutritionRequirement(baby_id=baby.id, **nutrition)
        db.add(db_nutrition)
    
    db.commit()
    
    return baby


@router.get("/{baby_id}/nutrition", response_model=NutritionRequirementResponse)
async def get_nutrition_requirements(
    baby_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取营养需求"""
    baby = db.query(Baby).filter(
        Baby.id == baby_id,
        Baby.user_id == current_user.id
    ).first()
    
    if not baby:
        raise HTTPException(status_code=404, detail="Baby not found")
    
    nutrition = db.query(NutritionRequirement).filter(
        NutritionRequirement.baby_id == baby_id
    ).first()
    
    if not nutrition:
        # 如果不存在，计算并创建
        nutrition_data = calculate_nutrition_requirements(baby)
        nutrition = NutritionRequirement(baby_id=baby.id, **nutrition_data)
        db.add(nutrition)
        db.commit()
        db.refresh(nutrition)
    
    return nutrition
