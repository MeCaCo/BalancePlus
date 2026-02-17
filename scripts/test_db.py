from app.core.database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Подключение к PostgreSQL успешно!")
except Exception as e:
    print(f"❌ Ошибка подключения: {e}")