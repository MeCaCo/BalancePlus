# Balance+ API 📊

Умная система учёта и аналитики личных финансов

## 🚀 Технологии

- Python 3.13
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- JWT
- Pytest
- Docker

## 📁 Структура проекта
app/
├── api/ # Эндпоинты
├── core/ # Конфигурация, безопасность
├── models/ # SQLAlchemy модели
├── repositories/ # Слой доступа к данным
├── schemas/ # Pydantic схемы
├── services/ # Бизнес-логика
└── utils/ # Вспомогательные функции
tests/ # Тесты

text

## 📦 Установка и запуск

### Локально

1. Клонировать репозиторий:
```bash
git clone https://github.com/MeCaCo/BalancePlus.git
cd BalancePlus
Создать виртуальное окружение:

bash
python -m venv venv
venv\Scripts\activate  # Windows
Установить зависимости:

bash
pip install -r requirements.txt
Создать файл .env:

env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=balanceplus
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
SECRET_KEY=your-secret-key-here
Применить миграции:

bash
alembic upgrade head
Запустить сервер:

bash
uvicorn app.main:app --reload
Открыть Swagger: http://localhost:8000/docs

🐳 Запуск через Docker
Установи Docker Desktop

Запусти контейнеры:

bash
docker-compose up --build
API будет доступно: http://localhost:8000

Swagger: http://localhost:8000/docs

Остановить:

bash
docker-compose down
Полный сброс (удалить БД):

bash
docker-compose down -v
🧪 Тестирование
bash
pytest tests/ -v
✅ Статус проекта
✅ Аутентификация (JWT)

✅ CRUD категорий

✅ CRUD транзакций

✅ CRUD целей

✅ Аналитика (баланс, отчёты)

✅ Импорт/экспорт CSV

✅ Тесты (36/37 проходят)

✅ Docker