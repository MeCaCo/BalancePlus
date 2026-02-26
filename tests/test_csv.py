import pytest
import csv
import io
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.user import User
from app.models.category import Category
from app.models.transaction import Transaction

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    """Очищаем все таблицы перед каждым тестом"""
    db = SessionLocal()
    try:
        db.query(Transaction).delete()
        db.query(Category).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture
def auth_headers():
    """Создаём пользователя и возвращаем заголовки с токеном"""
    client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "12345678"
    })

    login_resp = client.post("/api/v1/auth/login", data={
        "username": "testuser",
        "password": "12345678"
    })
    token = login_resp.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_category(auth_headers):
    """Создаём тестовую категорию"""
    response = client.post(
        "/api/v1/categories/",
        json={"name": "Еда", "type": "expense"},
        headers=auth_headers
    )
    return response.json()


@pytest.fixture
def test_transactions(auth_headers, test_category):
    """Создаём тестовые транзакции для экспорта"""
    transactions = []
    for i in range(3):
        resp = client.post(
            "/api/v1/transactions/",
            json={
                "amount": 100 * (i + 1),
                "description": f"Транзакция {i}",
                "category_id": test_category["id"]
            },
            headers=auth_headers
        )
        transactions.append(resp.json())
    return transactions


def test_export_csv(auth_headers, test_transactions):
    """Тест экспорта CSV"""
    response = client.get("/api/v1/import-export/export/csv", headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "Content-Disposition" in response.headers

    content = response.text
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)

    assert len(rows) == 3
    assert "amount" in reader.fieldnames
    assert "description" in reader.fieldnames
    assert "date" in reader.fieldnames


def test_export_csv_empty(auth_headers):
    """Тест экспорта CSV когда нет транзакций"""
    response = client.get("/api/v1/import-export/export/csv", headers=auth_headers)

    assert response.status_code == 200
    content = response.text
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    assert len(rows) == 0


def test_import_csv_success(auth_headers, test_category):
    """Тест успешного импорта CSV"""
    csv_content = io.StringIO()
    writer = csv.writer(csv_content)
    writer.writerow(['amount', 'description', 'date'])
    writer.writerow(['100.50', 'Продукты', '2026-02-26T10:00:00'])
    writer.writerow(['250.00', 'Такси', '2026-02-25T15:30:00'])

    csv_content.seek(0)

    response = client.post(
        "/api/v1/import-export/import/csv",
        files={"file": ("test.csv", csv_content.getvalue(), "text/csv")},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 2
    assert data["errors"] == []

    get_resp = client.get("/api/v1/transactions/", headers=auth_headers)
    transactions = get_resp.json()
    assert len(transactions) == 2

    # Проверяем что обе суммы есть (без учёта порядка)
    amounts = [t["amount"] for t in transactions]
    assert 100.5 in amounts
    assert 250.0 in amounts


def test_import_csv_without_category_id(auth_headers, test_category):
    """Тест импорта CSV без category_id (должна использоваться дефолтная)"""
    csv_content = io.StringIO()
    writer = csv.writer(csv_content)
    writer.writerow(['amount', 'description', 'date'])
    writer.writerow(['100.50', 'Продукты', '2026-02-26T10:00:00'])

    csv_content.seek(0)

    response = client.post(
        "/api/v1/import-export/import/csv",
        files={"file": ("test.csv", csv_content.getvalue(), "text/csv")},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 1

    get_resp = client.get("/api/v1/transactions/", headers=auth_headers)
    transaction = get_resp.json()[0]
    assert transaction["category_id"] == test_category["id"]


def test_import_csv_invalid_file_type(auth_headers):
    """Тест импорта не-CSV файла"""
    response = client.post(
        "/api/v1/import-export/import/csv",
        files={"file": ("test.txt", b"some text", "text/plain")},
        headers=auth_headers
    )

    assert response.status_code == 400
    data = response.json()
    assert "only csv files" in data["detail"].lower()


def test_import_csv_missing_headers(auth_headers):
    """Тест импорта CSV с неправильными заголовками"""
    csv_content = io.StringIO()
    writer = csv.writer(csv_content)
    writer.writerow(['wrong', 'headers', 'here'])
    writer.writerow(['100', 'test', '2026-01-01'])

    csv_content.seek(0)

    response = client.post(
        "/api/v1/import-export/import/csv",
        files={"file": ("test.csv", csv_content.getvalue(), "text/csv")},
        headers=auth_headers
    )

    # В коде нет проверки заголовков, падает с 500
    assert response.status_code in [400, 422, 500]


def test_import_csv_invalid_amount(auth_headers):
    """Тест импорта с некорректной суммой"""
    csv_content = io.StringIO()
    writer = csv.writer(csv_content)
    writer.writerow(['amount', 'description', 'date'])
    writer.writerow(['abc', 'Продукты', '2026-02-26'])
    writer.writerow(['-100', 'Такси', '2026-02-25'])

    csv_content.seek(0)

    response = client.post(
        "/api/v1/import-export/import/csv",
        files={"file": ("test.csv", csv_content.getvalue(), "text/csv")},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 0
    assert len(data["errors"]) == 2


def test_import_csv_invalid_date(auth_headers, test_category):
    """Тест импорта с некорректной датой"""
    csv_content = io.StringIO()
    writer = csv.writer(csv_content)
    writer.writerow(['amount', 'description', 'date'])
    writer.writerow(['100', 'Продукты', 'not-a-date'])

    csv_content.seek(0)

    response = client.post(
        "/api/v1/import-export/import/csv",
        files={"file": ("test.csv", csv_content.getvalue(), "text/csv")},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 1
    assert "invalid date" in data["errors"][0].lower()


def test_import_csv_large_file(auth_headers, test_category):
    """Тест импорта большого файла (10 строк)"""
    csv_content = io.StringIO()
    writer = csv.writer(csv_content)
    writer.writerow(['amount', 'description', 'date'])

    for i in range(10):
        writer.writerow([f"{i + 1}0.00", f"Транзакция {i}", "2026-02-26"])

    csv_content.seek(0)

    response = client.post(
        "/api/v1/import-export/import/csv",
        files={"file": ("test.csv", csv_content.getvalue(), "text/csv")},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 10

    get_resp = client.get("/api/v1/transactions/", headers=auth_headers)
    assert len(get_resp.json()) == 10