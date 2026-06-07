# Образ с Python 3.11
FROM python:3.11-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код в контейнер
COPY . .

# Открываем порт 8000
EXPOSE 8000

# Команда для запуска сервера
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]