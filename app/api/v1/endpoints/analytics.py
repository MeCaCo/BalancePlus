from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, timezone

from app.core.database import get_db
from app.models.transaction import Transaction
from app.models.category import Category
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/balance")
def get_balance(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить текущий баланс (доходы - расходы) — считает в БД"""
    # Доходы
    income = db.query(func.coalesce(func.sum(Transaction.amount), 0)) \
        .join(Category, Transaction.category_id == Category.id) \
        .filter(
        Transaction.user_id == current_user.id,
        Category.type == 'income'
    ).scalar()

    # Расходы
    expense = db.query(func.coalesce(func.sum(Transaction.amount), 0)) \
        .join(Category, Transaction.category_id == Category.id) \
        .filter(
        Transaction.user_id == current_user.id,
        Category.type == 'expense'
    ).scalar()

    return {
        "total_income": float(income),
        "total_expense": float(expense),
        "balance": float(income - expense)
    }


@router.get("/by-category")
def get_expenses_by_category(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        start_date: Optional[datetime] = Query(None),
        end_date: Optional[datetime] = Query(None)
):
    """Получить расходы по категориям за период — GROUP BY в БД"""
    query = db.query(
        Category.name,
        func.coalesce(func.sum(Transaction.amount), 0).label('total')
    ).join(
        Transaction, Transaction.category_id == Category.id
    ).filter(
        Transaction.user_id == current_user.id,
        Category.type == "expense"
    )

    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)

    results = query.group_by(Category.name).all()

    return [{"category": r[0], "total": float(r[1])} for r in results]


@router.get("/monthly/{year}/{month}")
def get_monthly_stats(
        year: int,
        month: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить статистику за конкретный месяц — агрегация в БД"""
    # Формируем границы месяца
    start_date = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end_date = datetime(year, month + 1, 1, tzinfo=timezone.utc)

    # Доходы за месяц
    income = db.query(func.coalesce(func.sum(Transaction.amount), 0)) \
        .join(Category, Transaction.category_id == Category.id) \
        .filter(
        Transaction.user_id == current_user.id,
        Category.type == 'income',
        Transaction.date >= start_date,
        Transaction.date < end_date
    ).scalar()

    # Расходы за месяц
    expense = db.query(func.coalesce(func.sum(Transaction.amount), 0)) \
        .join(Category, Transaction.category_id == Category.id) \
        .filter(
        Transaction.user_id == current_user.id,
        Category.type == 'expense',
        Transaction.date >= start_date,
        Transaction.date < end_date
    ).scalar()

    # Расходы по категориям (группировка в БД)
    by_category_raw = db.query(
        Category.name,
        func.coalesce(func.sum(Transaction.amount), 0).label('total')
    ).join(
        Transaction, Transaction.category_id == Category.id
    ).filter(
        Transaction.user_id == current_user.id,
        Category.type == 'expense',
        Transaction.date >= start_date,
        Transaction.date < end_date
    ).group_by(Category.name).all()

    by_category = {r[0]: float(r[1]) for r in by_category_raw}

    return {
        "month": f"{year}-{month:02d}",
        "income": float(income),
        "expense": float(expense),
        "balance": float(income - expense),
        "by_category": by_category
    }