"""
数据库模型定义
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    babies = relationship("Baby", back_populates="user")
    recipes = relationship("Recipe", back_populates="user")


class Baby(Base):
    """宝宝信息表"""
    __tablename__ = "babies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=True)  # 宝宝昵称（可选）
    
    # 基础信息
    age_months = Column(Integer, nullable=False)  # 月龄
    weight = Column(Float, nullable=True)  # 体重(kg)
    height = Column(Float, nullable=True)  # 身高(cm)
    
    # 发育阶段
    feeding_stage = Column(String, nullable=False)  # 进食能力阶段
    teething_status = Column(String, nullable=False)  # 出牙情况
    months_since_weaning = Column(Integer, nullable=True)  # 已添加辅食几个月
    
    # 健康信息
    allergies = Column(JSON, default=list)  # 过敏源列表
    dietary_needs = Column(String, nullable=True)  # 特殊饮食需求
    digestion_status = Column(String, nullable=True)  # 消化情况
    
    # 偏好信息
    liked_ingredients = Column(JSON, default=list)  # 喜欢的食材
    disliked_ingredients = Column(JSON, default=list)  # 不喜欢的食材
    family_diet_style = Column(String, nullable=True)  # 家庭饮食习惯
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="babies")
    nutrition_requirements = relationship("NutritionRequirement", back_populates="baby")
    recipes = relationship("Recipe", back_populates="baby")


class NutritionRequirement(Base):
    """营养需求表"""
    __tablename__ = "nutrition_requirements"

    id = Column(Integer, primary_key=True, index=True)
    baby_id = Column(Integer, ForeignKey("babies.id"), nullable=False)
    
    # 营养需求（每日）
    calories_per_day = Column(Float, nullable=True)
    protein_g = Column(Float, nullable=True)
    fat_g = Column(Float, nullable=True)
    carbs_g = Column(Float, nullable=True)
    iron_mg = Column(Float, nullable=True)
    calcium_mg = Column(Float, nullable=True)
    vitamin_d_iu = Column(Float, nullable=True)
    
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    baby = relationship("Baby", back_populates="nutrition_requirements")


class Recipe(Base):
    """食谱表"""
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    baby_id = Column(Integer, ForeignKey("babies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    week_start_date = Column(DateTime(timezone=True), nullable=False)  # 周开始日期
    status = Column(String(20), default="generating")  # generating / completed

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    baby = relationship("Baby", back_populates="recipes")
    user = relationship("User", back_populates="recipes")
    details = relationship("RecipeDetail", back_populates="recipe", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="recipe")


class RecipeDetail(Base):
    """食谱详情表（每日每餐）"""
    __tablename__ = "recipe_details"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    
    day_of_week = Column(Integer, nullable=False)  # 1-7 (周一-周日)
    meal_type = Column(String, nullable=False)  # breakfast/lunch/dinner/snack
    
    dish_name = Column(String, nullable=False)  # 菜品名称
    ingredients = Column(JSON, nullable=False)  # 食材列表 [{"name": "胡萝卜", "amount": "50g"}]
    cooking_steps = Column(JSON, nullable=False)  # 烹饪步骤 [{"step": 1, "description": "..."}]
    nutrition_info = Column(JSON, nullable=True)  # 营养信息 {"calories": 100, "protein": 5}
    image_url = Column(String, nullable=True)  # 配图URL
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    recipe = relationship("Recipe", back_populates="details")


class Conversation(Base):
    """对话历史表"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    message_type = Column(String, nullable=False)  # user/assistant
    content = Column(Text, nullable=False)
    extra_data = Column(JSON, default=dict)  # 额外信息（如调整类型、替换的食材等）
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    recipe = relationship("Recipe", back_populates="conversations")
