from pydantic import BaseModel, Field
from typing import Optional


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    type: str = Field(..., pattern="^(income|expense)$")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    type: Optional[str] = Field(None, pattern="^(income|expense)$")


class Category(CategoryBase):
    id: int
    user_id: Optional[int] = None
    is_default: bool

    model_config = {
        "from_attributes": True
    }