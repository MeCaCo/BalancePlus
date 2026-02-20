import csv
import io
from typing import List
from app.models.transaction import Transaction


def export_transactions_to_csv(transactions: List[Transaction]) -> str:
    """Создаёт CSV строку из списка транзакций"""
    output = io.StringIO()
    writer = csv.writer(output)

    # Заголовки
    writer.writerow(['id', 'amount', 'description', 'date', 'category_id', 'user_id'])

    # Данные
    for t in transactions:
        writer.writerow([
            t.id,
            t.amount,
            t.description or '',
            t.date.isoformat(),
            t.category_id,
            t.user_id
        ])

    return output.getvalue()


def parse_csv_to_transactions(csv_content: str, user_id: int) -> List[dict]:
    """Парсит CSV и возвращает список словарей для создания транзакций"""
    result = []
    reader = csv.DictReader(io.StringIO(csv_content))

    for row in reader:
        try:
            amount = float(row.get('amount', 0))
            if amount <= 0:
                continue

            transaction_data = {
                'amount': amount,
                'description': row.get('description', ''),
                'category_id': int(row.get('category_id', 1)),
                'user_id': user_id
            }
            result.append(transaction_data)
        except (ValueError, KeyError):
            continue

    return result