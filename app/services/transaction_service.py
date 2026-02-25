from app.repositories.transaction_repository import TransactionRepository
from app.services.base import BaseService
from app.models.transaction import Transaction
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import date


class TransactionService(BaseService[Transaction]):
    def __init__(self, repository: TransactionRepository):
        super().__init__(repository)
        self.repository = repository

    def get_user_transactions(self, user_id: int) -> List[Transaction]:
        return self.repository.get_by_user(user_id)

    def get_transactions_by_category(self, user_id: int, category_id: int) -> List[Transaction]:
        # Проверим, что категория принадлежит пользователю (опционально)
        return self.repository.get_by_user_and_category(user_id, category_id)

    def get_transactions_by_date_range(self, user_id: int, start_date: date, end_date: date) -> List[Transaction]:
        return self.repository.get_by_date_range(user_id, start_date, end_date)

    def create_transaction(self, user_id: int, amount: float, description: str,
                           category_id: int, transaction_date: date) -> Transaction:
        # Валидация суммы
        if amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amount must be positive"
            )

        # Здесь можно добавить проверку существования категории
        # и её принадлежности пользователю

        return self.create(
            user_id=user_id,
            amount=amount,
            description=description,
            category_id=category_id,
            date=transaction_date
        )

    def update_transaction(self, transaction_id: int, user_id: int, **kwargs) -> Optional[Transaction]:
        transaction = self.get_by_id(transaction_id)

        # Проверяем, что транзакция существует и принадлежит пользователю
        if not transaction or transaction.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )

        # Обновляем поля
        for key, value in kwargs.items():
            if hasattr(transaction, key) and value is not None:
                setattr(transaction, key, value)

        self.repository.db.commit()
        self.repository.db.refresh(transaction)
        return transaction

    def delete_transaction(self, transaction_id: int, user_id: int) -> None:
        transaction = self.get_by_id(transaction_id)

        if not transaction or transaction.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )

        self.delete(transaction)