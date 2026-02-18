from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List, Dict
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.transaction import Transaction
from app.models.category import Category
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter()


@router.get("/balance")
def get_balance(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """Получить текущий баланс (доходы - расходы)"""
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).all()

    total_income = sum(t.amount for t in transactions if t.category.type == "income")
    total_expense = sum(t.amount for t in transactions if t.category.type == "expense")

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": total_income - total_expense
    }


@router.get("/by-category")
def get_expenses_by_category(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
        start_date: datetime = None,
        end_date: datetime = None
):
    """Получить расходы по категориям за период"""
    query = db.query(
        Category.name,
        func.sum(Transaction.amount).label('total')
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
        current_user: User = Depends(get_current_active_user)
):
    """Получить статистику за конкретный месяц"""
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.date >= start_date,
        Transaction.date < end_date
    ).all()

    income = sum(t.amount for t in transactions if t.category.type == "income")
    expense = sum(t.amount for t in transactions if t.category.type == "expense")

    # Расходы по категориям
    by_category = {}
    for t in transactions:
        if t.category.type == "expense":
            by_category[t.category.name] = by_category.get(t.category.name, 0) + t.amount

    return {
        "month": f"{year}-{month:02d}",
        "income": income,
        "expense": expense,
        "balance": income - expense,
        "by_category": by_category
    }