from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.transaction import Transaction
from app.models.category import Category
from app.utils.csv_handler import export_transactions_to_csv, parse_csv_to_transactions

router = APIRouter()


@router.get("/export/csv")
def export_csv(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """Экспорт всех транзакций пользователя в CSV"""
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.date.desc()).all()

    csv_data = export_transactions_to_csv(transactions)

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=transactions_{current_user.id}.csv"
        }
    )


@router.post("/import/csv")
def import_csv(
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """Импорт транзакций из CSV файла"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(400, "Only CSV files are allowed")

    # Читаем файл
    contents = file.file.read().decode('utf-8')
    transactions_data = parse_csv_to_transactions(contents, current_user.id)

    if not transactions_data:
        raise HTTPException(400, "No valid transactions found in file")

    # Создаём транзакции
    created = []
    for data in transactions_data:
        # Проверяем категорию
        category = db.query(Category).filter(
            Category.id == data['category_id']
        ).first()

        if not category or (category.user_id != current_user.id and not category.is_default):
            data['category_id'] = 1  # ставим категорию по умолчанию

        transaction = Transaction(**data)
        db.add(transaction)
        created.append(data)

    db.commit()

    return {
        "message": f"Successfully imported {len(created)} transactions",
        "count": len(created)
    }