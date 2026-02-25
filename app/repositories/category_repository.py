from sqlalchemy.orm import Session
from app.models.category import Category
from app.repositories.base import BaseRepository
from typing import List, Optional

class CategoryRepository(BaseRepository[Category]):
    def __init__(self, db: Session):
        super().__init__(db, Category)

    def get_by_user(self, user_id: int) -> List[Category]:
        return self.db.query(Category).filter(Category.user_id == user_id).all()

    def get_by_name_and_user(self, name: str, user_id: int) -> Optional[Category]:
        return self.db.query(Category).filter(
            Category.name == name,
            Category.user_id == user_id
        ).first()