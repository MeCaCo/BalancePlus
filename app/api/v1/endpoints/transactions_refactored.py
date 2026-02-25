from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.transaction import TransactionCreate, TransactionUpdate, Transaction as TransactionOut
from app.repositories.transaction_repository import TransactionRepository
from app.services.transaction_service import TransactionService

router = APIRouter()

def get_transaction_service(db: Session = Depends(get_db)) -> TransactionService:
    repository = TransactionRepository(db)
    return TransactionService(repository)

@router.post("/", response_model=TransactionOut)
def create_transaction(
    transaction_data: TransactionCreate,
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user)
):
    data = transaction_data.model_dump(exclude_unset=True)
    return service.create_transaction(
        user_id=current_user.id,
        amount=data.get("amount"),
        description=data.get("description"),
        category_id=data.get("category_id"),
        transaction_date=data.get("date")
    )

@router.get("/", response_model=List[TransactionOut])
def get_transactions(
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    category_id: Optional[int] = Query(None)
):
    if start_date and end_date:
        return service.get_transactions_by_date_range(
            current_user.id, start_date, end_date
        )
    elif category_id:
        return service.get_transactions_by_category(
            current_user.id, category_id
        )
    else:
        return service.get_user_transactions(current_user.id)

@router.get("/{transaction_id}", response_model=TransactionOut)
def get_transaction(
    transaction_id: int,
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user)
):
    transaction = service.get_by_id(transaction_id)
    if not transaction or transaction.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@router.put("/{transaction_id}", response_model=TransactionOut)
def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user)
):
    return service.update_transaction(
        transaction_id,
        current_user.id,
        **transaction_data.model_dump(exclude_unset=True)
    )

@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user)
):
    service.delete_transaction(transaction_id, current_user.id)
    return {"message": "Transaction deleted successfully"}