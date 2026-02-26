import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.user import User
from app.models.category import Category
from app.models.transaction import Transaction
from datetime import datetime, timedelta

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
def test_categories(auth_headers):
    """Создаём тестовые категории"""
    categories = {}

    # Доход
    resp = client.post(
        "/api/v1/categories/",
        json={"name": "Зарплата", "type": "income"},
        headers=auth_headers
    )
    categories["income"] = resp.json()

    # Расходы
    for name in ["Еда", "Транспорт", "Развлечения"]:
        resp = client.post(
            "/api/v1/categories/",
            json={"name": name, "type": "expense"},
            headers=auth_headers
        )
        categories[name] = resp.json()

    return categories


@pytest.fixture
def test_transactions(auth_headers, test_categories):
    """Создаём тестовые транзакции"""
    transactions = []

    # Доходы (зарплата)
    transactions.append(client.post(
        "/api/v1/transactions/",
        json={
            "amount": 100000,
            "description": "Зарплата",
            "category_id": test_categories["income"]["id"]
        },
        headers=auth_headers
    ).json())

    # Расходы
    transactions.append(client.post(
        "/api/v1/transactions/",
        json={
            "amount": 5000,
            "description": "Продукты",
            "category_id": test_categories["Еда"]["id"]
        },
        headers=auth_headers
    ).json())

    transactions.append(client.post(
        "/api/v1/transactions/",
        json={
            "amount": 3000,
            "description": "Такси",
            "category_id": test_categories["Транспорт"]["id"]
        },
        headers=auth_headers
    ).json())

    transactions.append(client.post(
        "/api/v1/transactions/",
        json={
            "amount": 2000,
            "description": "Кино",
            "category_id": test_categories["Развлечения"]["id"]
        },
        headers=auth_headers
    ).json())

    return transactions


# ========== ТЕСТЫ ==========

def test_get_balance(auth_headers, test_transactions):
    """Тест получения баланса"""
    response = client.get("/api/v1/analytics/balance", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Проверяем структуру
    assert "total_income" in data
    assert "total_expense" in data
    assert "balance" in data

    # Проверяем суммы
    assert data["total_income"] == 100000
    assert data["total_expense"] == 5000 + 3000 + 2000  # 10000
    assert data["balance"] == 100000 - 10000  # 90000


def test_get_balance_no_transactions(auth_headers):
    """Тест баланса когда нет транзакций"""
    response = client.get("/api/v1/analytics/balance", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total_income"] == 0
    assert data["total_expense"] == 0
    assert data["balance"] == 0


def test_get_expenses_by_category(auth_headers, test_categories, test_transactions):
    """Тест получения расходов по категориям"""
    response = client.get("/api/v1/analytics/by-category", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Проверяем что это список
    assert isinstance(data, list)

    # Преобразуем в словарь для удобства
    by_category = {item["category"]: item["total"] for item in data}

    # Проверяем суммы
    assert by_category.get("Еда", 0) == 5000
    assert by_category.get("Транспорт", 0) == 3000
    assert by_category.get("Развлечения", 0) == 2000

    # Доходов не должно быть в этом отчёте
    assert "Зарплата" not in by_category


def test_get_expenses_by_category_with_dates(auth_headers, test_categories):
    """Тест фильтрации расходов по датам"""
    # Создаём транзакции с разными датами
    today = datetime.now()
    last_month = today - timedelta(days=35)

    # Сегодняшняя
    client.post(
        "/api/v1/transactions/",
        json={
            "amount": 1000,
            "description": "Сегодня",
            "category_id": test_categories["Еда"]["id"]
        },
        headers=auth_headers
    )

    # Месячной давности
    client.post(
        "/api/v1/transactions/",
        json={
            "amount": 2000,
            "description": "Давно",
            "category_id": test_categories["Еда"]["id"],
            "date": last_month.isoformat()
        },
        headers=auth_headers
    )

    # Фильтр по дате начала (только сегодняшние)
    response = client.get(
        "/api/v1/analytics/by-category",
        params={"start_date": today.isoformat()},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    by_category = {item["category"]: item["total"] for item in data}
    assert by_category.get("Еда", 0) == 1000


def test_get_monthly_stats(auth_headers, test_categories):
    """Тест месячной статистики"""
    # Создаём транзакции в феврале 2026
    feb_date = datetime(2026, 2, 15, tzinfo=None)  # Без timezone

    client.post(
        "/api/v1/transactions/",
        json={
            "amount": 100000,
            "description": "Зарплата",
            "category_id": test_categories["income"]["id"],
            "date": feb_date.isoformat()
        },
        headers=auth_headers
    )

    client.post(
        "/api/v1/transactions/",
        json={
            "amount": 5000,
            "description": "Еда",
            "category_id": test_categories["Еда"]["id"],
            "date": feb_date.isoformat()
        },
        headers=auth_headers
    )

    # Статистика за февраль 2026
    response = client.get("/api/v1/analytics/monthly/2026/2", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["month"] == "2026-02"
    assert data["income"] == 100000
    assert data["expense"] == 5000
    assert data["balance"] == 95000
    assert data["by_category"]["Еда"] == 5000


def test_get_monthly_stats_empty_month(auth_headers):
    """Тест месячной статистики за месяц без транзакций"""
    response = client.get("/api/v1/analytics/monthly/2025/1", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["income"] == 0
    assert data["expense"] == 0
    assert data["balance"] == 0
    assert data["by_category"] == {}


def test_analytics_different_users(auth_headers, test_categories):
    """Тест что пользователи видят только свои данные"""
    # Создаём транзакцию первого пользователя
    client.post(
        "/api/v1/transactions/",
        json={
            "amount": 1000,
            "description": "Пользователь 1",
            "category_id": test_categories["Еда"]["id"]
        },
        headers=auth_headers
    )

    # Регистрируем второго пользователя
    client.post("/api/v1/auth/register", json={
        "username": "user2",
        "email": "user2@example.com",
        "password": "12345678"
    })

    login_resp2 = client.post("/api/v1/auth/login", data={
        "username": "user2",
        "password": "12345678"
    })
    headers2 = {"Authorization": f"Bearer {login_resp2.json()['access_token']}"}

    # Создаём категории для второго
    cat2_resp = client.post(
        "/api/v1/categories/",
        json={"name": "Еда2", "type": "expense"},
        headers=headers2
    )
    cat2 = cat2_resp.json()

    # Транзакция второго
    client.post(
        "/api/v1/transactions/",
        json={
            "amount": 500,
            "description": "Пользователь 2",
            "category_id": cat2["id"]
        },
        headers=headers2
    )

    # Проверяем баланс второго
    response = client.get("/api/v1/analytics/balance", headers=headers2)

    assert response.status_code == 200
    data = response.json()
    assert data["total_expense"] == 500  # Видит только свою транзакцию