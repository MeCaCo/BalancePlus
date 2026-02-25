from app.repositories.category_repository import CategoryRepository
from app.services.base import BaseService
from app.models.category import Category
from fastapi import HTTPException, status
from typing import List


class CategoryService(BaseService[Category]):
    def __init__(self, repository: CategoryRepository):
        super().__init__(repository)
        self.repository = repository

    def get_user_categories(self, user_id: int) -> List[Category]:
        return self.repository.get_by_user(user_id)

    def create_category(self, user_id: int, name: str, type: str) -> Category:
        # Проверяем, есть ли уже такая категория у пользователя
        existing = self.repository.get_by_name_and_user(name, user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category with this name already exists"
            )

        return self.create(
            name=name,
            type=type,
            user_id=user_id
        )