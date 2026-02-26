import pytest
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
    # Регистрируем
    client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "12345678"
    })

    # Логинимся
    login_resp = client.post("/api/v1/auth/login", data={
        "username": "testuser",
        "password": "12345678"
    })
    token = login_resp.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def test_create_category(auth_headers):
    """Тест создания категории"""
    response = client.post(
        "/api/v1/categories/",
        json={
            "name": "Еда",
            "type": "expense"
        },
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Еда"
    assert data["type"] == "expense"
    assert "id" in data


def test_get_categories(auth_headers):
    """Тест получения списка категорий"""
    # Создаём категорию
    client.post(
        "/api/v1/categories/",
        json={"name": "Еда", "type": "expense"},
        headers=auth_headers
    )

    # Получаем список
    response = client.get("/api/v1/categories/", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["name"] == "Еда"


def test_get_category_by_id(auth_headers):
    """Тест получения категории по ID"""
    # Создаём
    create_resp = client.post(
        "/api/v1/categories/",
        json={"name": "Транспорт", "type": "expense"},
        headers=auth_headers
    )
    category_id = create_resp.json()["id"]

    # Получаем
    response = client.get(f"/api/v1/categories/{category_id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Транспорт"
    assert data["id"] == category_id


# ⚠️ Тесты на update и delete убраны, так как их нет в API

def test_categories_different_users(auth_headers):
    """Тест что пользователи не видят чужие категории"""
    # Создаём категорию первым пользователем
    client.post(
        "/api/v1/categories/",
        json={"name": "Моя категория", "type": "expense"},
        headers=auth_headers
    )

    # Регистрируем второго пользователя
    client.post("/api/v1/auth/register", json={
        "username": "user2",
        "email": "user2@example.com",
        "password": "12345678"
    })

    # Логинимся вторым
    login_resp2 = client.post("/api/v1/auth/login", data={
        "username": "user2",
        "password": "12345678"
    })
    headers2 = {"Authorization": f"Bearer {login_resp2.json()['access_token']}"}

    # Получаем категории второго
    response = client.get("/api/v1/categories/", headers=headers2)

    assert response.status_code == 200
    data = response.json()
    # Должен быть пустой список или только его категории
    assert len(data) == 0 or all(c["name"] != "Моя категория" for c in data)