from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.models.transaction import Transaction
from app.models.category import Category
from app.schemas.transaction import TransactionCreate, TransactionUpdate, Transaction as TransactionSchema
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=TransactionSchema)
def create_transaction(
        transaction_data: TransactionCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """Создать новую транзакцию"""
    # Проверяем, что категория принадлежит пользователю
    category = db.query(Category).filter(
        Category.id == transaction_data.category_id
    ).first()

    if not category or (category.user_id != current_user.id and not category.is_default):
        raise HTTPException(status_code=404, detail="Category not found")

    # Создаём транзакцию
    transaction = Transaction(
        **transaction_data.dict(),
        user_id=current_user.id
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.get("/", response_model=List[TransactionSchema])
def get_transactions(
        skip: int = 0,
        limit: int = 100,
        category_id: int = None,
        start_date: datetime = None,
        end_date: datetime = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """Получить список транзакций с фильтрацией"""
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)

    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)

    transactions = query.order_by(Transaction.date.desc()).offset(skip).limit(limit).all()
    return transactions


@router.get("/{transaction_id}", response_model=TransactionSchema)
def get_transaction(
        transaction_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return transaction


@router.put("/{transaction_id}", response_model=TransactionSchema)
def update_transaction(
        transaction_id: int,
        transaction_data: TransactionUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Если меняется категория — проверяем её доступность
    if transaction_data.category_id:
        category = db.query(Category).filter(Category.id == transaction_data.category_id).first()
        if not category or (category.user_id != current_user.id and not category.is_default):
            raise HTTPException(status_code=404, detail="Category not found")

    for key, value in transaction_data.dict(exclude_unset=True).items():
        setattr(transaction, key, value)

    db.commit()
    db.refresh(transaction)
    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
        transaction_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(transaction)
    db.commit()
    return None