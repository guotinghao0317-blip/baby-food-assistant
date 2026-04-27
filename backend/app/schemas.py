"""
Pydantic 数据模型（API请求/响应）
"""
from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, Dict, Any
from datetime import datetime


# ========== 用户相关 ==========
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度至少6个字符')
        if len(v.encode('utf-8')) > 72:
            raise ValueError('密码长度不能超过72个字符')
        return v


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


# ========== 宝宝信息相关 ==========
class BabyCreate(BaseModel):
    name: Optional[str] = None
    age_months: int
    weight: Optional[float] = None
    height: Optional[float] = None
    feeding_stage: str  # 进食能力阶段
    teething_status: str  # 出牙情况
    months_since_weaning: Optional[int] = None
    allergies: List[str] = []
    dietary_needs: Optional[str] = None
    digestion_status: Optional[str] = None
    liked_ingredients: List[str] = []
    disliked_ingredients: List[str] = []
    family_diet_style: Optional[str] = None


class BabyResponse(BaseModel):
    id: int
    user_id: int
    name: Optional[str]
    age_months: int
    weight: Optional[float]
    height: Optional[float]
    feeding_stage: str
    teething_status: str
    allergies: List[str]
    liked_ingredients: List[str]
    disliked_ingredients: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


class NutritionRequirementResponse(BaseModel):
    calories_per_day: Optional[float]
    protein_g: Optional[float]
    fat_g: Optional[float]
    carbs_g: Optional[float]
    iron_mg: Optional[float]
    calcium_mg: Optional[float]
    vitamin_d_iu: Optional[float]

    class Config:
        from_attributes = True


# ========== 食谱相关 ==========
class Ingredient(BaseModel):
    name: str
    amount: str  # 如 "50g", "1个"


class CookingStep(BaseModel):
    step: int
    description: str


class NutritionInfo(BaseModel):
    calories: Optional[float] = None
    protein: Optional[float] = None
    fat: Optional[float] = None
    carbs: Optional[float] = None


class RecipeDetailCreate(BaseModel):
    day_of_week: int  # 1-7
    meal_type: str  # breakfast/lunch/dinner/snack
    dish_name: str
    ingredients: List[Ingredient]
    cooking_steps: List[CookingStep]
    nutrition_info: Optional[NutritionInfo] = None
    image_url: Optional[str] = None


class RecipeGenerateRequest(BaseModel):
    baby_id: int


class RecipeDetailResponse(BaseModel):
    id: int
    day_of_week: int
    meal_type: str
    dish_name: str
    ingredients: List[Dict[str, Any]]
    cooking_steps: List[Dict[str, Any]]
    nutrition_info: Optional[Dict[str, Any]] = None
    image_url: Optional[str] = None

    class Config:
        from_attributes = True


class RecipeResponse(BaseModel):
    id: int
    baby_id: int
    week_start_date: datetime
    status: str
    created_at: datetime
    details: List[RecipeDetailResponse]

    class Config:
        from_attributes = True


class RecipeAdjustRequest(BaseModel):
    recipe_id: int
    message: str  # 用户反馈消息


class ReplaceDishRequest(BaseModel):
    day_of_week: int  # 1-7
    meal_type: str  # breakfast/lunch/dinner/snack
    original_dish_id: int


# ========== 对话相关 ==========
class ConversationMessage(BaseModel):
    message_type: str  # user/assistant
    content: str
    metadata: Optional[Dict[str, Any]] = None


class ConversationResponse(BaseModel):
    id: int
    recipe_id: int
    message_type: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
