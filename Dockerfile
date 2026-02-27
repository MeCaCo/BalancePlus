FROM python:3.13-slim

WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Команда для запуска
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]