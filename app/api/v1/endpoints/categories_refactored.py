from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.category import CategoryCreate, Category as CategoryOut
from app.repositories.category_repository import CategoryRepository
from app.services.category_service import CategoryService

router = APIRouter()

def get_category_service(db: Session = Depends(get_db)) -> CategoryService:
    repository = CategoryRepository(db)
    return CategoryService(repository)

@router.post("/", response_model=CategoryOut)
def create_category(
    category_data: CategoryCreate,
    service: CategoryService = Depends(get_category_service),
    current_user: User = Depends(get_current_user)
):
    return service.create_category(
        user_id=current_user.id,
        name=category_data.name,
        type=category_data.type
    )

@router.get("/", response_model=List[CategoryOut])
def get_categories(
    service: CategoryService = Depends(get_category_service),
    current_user: User = Depends(get_current_user)
):
    return service.get_user_categories(current_user.id)

@router.get("/{category_id}", response_model=CategoryOut)
def get_category(
    category_id: int,
    service: CategoryService = Depends(get_category_service),
    current_user: User = Depends(get_current_user)
):
    category = service.get_by_id(category_id)
    if not category or category.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Category not found")
    return category