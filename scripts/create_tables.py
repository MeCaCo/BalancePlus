from app.core.database import engine
from app.models import user  # импортируем модели, чтобы они зарегистрировались в Base
from app.core.database import Base

print("Создаём таблицы в базе данных...")
Base.metadata.create_all(bind=engine)
print("✅ Таблицы созданы!")