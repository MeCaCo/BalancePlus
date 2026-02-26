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
    """Очищаем все таблицы перед каждым тестом в правильном порядке"""
    db = SessionLocal()
    try:
        # Сначала удаляем транзакции (они ссылаются на категории)
        db.query(Transaction).delete()
        # Потом удаляем категории (они ссылаются на пользователей)
        db.query(Category).delete()
        # Потом удаляем пользователей
        db.query(User).delete()
        db.commit()
    finally:
        db.close()
    yield


def test_register():
    """Тест регистрации нового пользователя"""
    response = client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "12345678"
    })

    assert response.status_code == 200, f"Ошибка: {response.text}"
    data = response.json()
    assert "id" in data
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"


def test_register_duplicate_username():
    """Тест на попытку регистрации с существующим username"""
    # Сначала регистрируем
    client.post("/api/v1/auth/register", json={
        "username": "duplicate",
        "email": "first@example.com",
        "password": "12345678"
    })

    # Пытаемся зарегистрировать того же пользователя
    response = client.post("/api/v1/auth/register", json={
        "username": "duplicate",
        "email": "second@example.com",
        "password": "12345678"
    })

    assert response.status_code == 400  # Должна быть ошибка


def test_login():
    """Тест логина"""
    # Сначала регистрируем
    client.post("/api/v1/auth/register", json={
        "username": "loginuser",
        "email": "login@example.com",
        "password": "12345678"
    })

    # Пытаемся залогиниться (form-data!)
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "loginuser",
            "password": "12345678"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password():
    """Тест логина с неверным паролем"""
    # Регистрируем
    client.post("/api/v1/auth/register", json={
        "username": "wrongpass",
        "email": "wrong@example.com",
        "password": "12345678"
    })

    # Пытаемся с неверным паролем (form-data!)
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "wrongpass",
            "password": "wrong123"
        }
    )

    assert response.status_code == 401  # Неавторизован