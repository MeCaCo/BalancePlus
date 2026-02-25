from sqlalchemy.orm import Session
from app.models.transaction import Transaction
from app.repositories.base import BaseRepository
from typing import List
from datetime import date

class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, db: Session):
        super().__init__(db, Transaction)

    def get_by_user(self, user_id: int) -> List[Transaction]:
        return self.db.query(Transaction).filter(Transaction.user_id == user_id).all()

    def get_by_user_and_category(self, user_id: int, category_id: int) -> List[Transaction]:
        return self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.category_id == category_id
        ).all()

    def get_by_date_range(self, user_id: int, start_date: date, end_date: date) -> List[Transaction]:
        return self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).all()

    def get_by_type(self, user_id: int, type: str) -> List[Transaction]:
        return self.db.query(Transaction).join(Transaction.category).filter(
            Transaction.user_id == user_id,
            Category.type == type  # type: ignore
        ).all()