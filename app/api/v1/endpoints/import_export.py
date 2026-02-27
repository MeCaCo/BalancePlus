from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import csv
import io

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.transaction import Transaction
from app.models.category import Category
from app.utils.csv_handler import export_transactions_to_csv

router = APIRouter()


@router.get("/export/csv")
def export_csv(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
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
        current_user: User = Depends(get_current_user)
):
    """Импорт транзакций из CSV файла"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(400, "Only CSV files are allowed")

    # Получаем дефолтную категорию пользователя
    default_category = db.query(Category).filter(
        Category.user_id == current_user.id,
        Category.is_default == True
    ).first()

    # Если нет дефолтной, берём любую первую
    if not default_category:
        default_category = db.query(Category).filter(
            Category.user_id == current_user.id
        ).first()

    # Если вообще нет категорий — создаём "Uncategorized"
    if not default_category:
        default_category = Category(
            name="Uncategorized",
            type="expense",
            user_id=current_user.id,
            is_default=True
        )
        db.add(default_category)
        db.commit()
        db.refresh(default_category)

    try:
        contents = file.file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(contents))

        # Проверка заголовков
        required_fields = ['amount', 'description', 'date']
        if not all(field in reader.fieldnames for field in required_fields):
            raise HTTPException(
                status_code=400,
                detail=f"CSV must contain columns: {required_fields}"
            )

        created = []
        errors = []

        for i, row in enumerate(reader, start=2):  # start=2 because row 1 is header
            try:
                # Парсим сумму
                amount = float(row.get('amount', 0))
                if amount <= 0:
                    errors.append(f"Row {i}: amount must be positive")
                    continue

                # Описание
                description = row.get('description', '').strip()
                if not description:
                    description = "Imported transaction"

                # Парсим дату
                date_str = row.get('date', '')
                try:
                    if date_str:
                        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    else:
                        date = datetime.now(timezone.utc)
                except ValueError:
                    errors.append(f"Row {i}: invalid date format, using current date")
                    date = datetime.now(timezone.utc)

                # Определяем категорию
                category_id = None
                if 'category_id' in row and row['category_id']:
                    try:
                        cat_id = int(row['category_id'])
                        category = db.query(Category).filter(
                            Category.id == cat_id,
                            Category.user_id == current_user.id
                        ).first()
                        if category:
                            category_id = cat_id
                    except ValueError:
                        pass

                # Если категория не найдена, используем дефолтную
                if not category_id:
                    category_id = default_category.id

                transaction = Transaction(
                    amount=amount,
                    description=description,
                    date=date,
                    user_id=current_user.id,
                    category_id=category_id
                )
                db.add(transaction)
                created.append(transaction)

            except Exception as e:
                errors.append(f"Row {i}: {str(e)}")

        if created:
            db.commit()

        return {
            "message": f"Imported {len(created)} transactions, {len(errors)} errors",
            "imported": len(created),
            "errors": errors
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        file.file.close()