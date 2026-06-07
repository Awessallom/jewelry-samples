# Jewelry Samples API

REST API сервис для системы учета проб драгоценных металлов.

## Технологии

- Python 3.10+
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- Pytest

## Установка и запуск

### 1. Клонирование репозитория

bash
git clone <your-repo-url>
cd jewelry_samples

### 2. Создание виртуального окружения

bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

### 3. Установка зависимостей

bash
pip install -r requirements.txt

### 4. Запуск сервера

bash
uvicorn app.main:app --reload

Сервер будет доступен по адресу: http://localhost:8000

Документация API: http://localhost:8000/docs

## Эндпоинты API

| Метод	| URL	| Описание |
|--|--|--|
| POST	| /samples	| Создание новой пробы |
| GET	| /samples	| Получение списка проб  |
| GET	| /samples/{id}	| Получение информации о пробе |
| PATCH	| /samples/{id}/status	| Изменение статуса пробы |
| GET	| /reports/summary	| Сводный отчет |

## Примеры запросов

### 1. Создание пробы

bash
curl -X POST http://localhost:8000/samples \
  -H "Content-Type: application/json" \
  -d '{"sample_code":"AU-001","weight":12.5,"operator":"John Doe"}'

### 2. Получение списка проб

bash
curl "http://localhost:8000/samples?skip=0&limit=10"

### 3. Изменение статуса

bash
curl -X PATCH http://localhost:8000/samples/1/status \
  -H "Content-Type: application/json" \
  -d '{"status":"approved"}'

### 4. Получение отчета

bash
curl http://localhost:8000/reports/summary

### 5. Запуск эмулятора оборудования

В отдельном терминале:

bash
python device_simulator.py

Эмулятор создаст 20+ проб с интервалом 2 секунды.

### 6. Запуск тестов

bash
pytest tests/test_api.py -v

## Структура проекта

jewelry_samples/

├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI приложение
│   ├── models.py        # SQLAlchemy модели
│   ├── schemas.py       # Pydantic схемы
│   └── database.py      # Подключение к БД
├── tests/
│   ├── __init__.py
│   └── test_api.py      # Тесты pytest
├── device_simulator.py  # Эмулятор оборудования
├── requirements.txt     # Зависимости
├── README.md           # Документация
└── .gitignore          # Игнорируемые файлы

### Допустимые статусы

created - создана (по умолчанию)
measured - измерена
approved - одобрена
rejected - отклонена

### Валидация данных

Код пробы не может быть пустым
Оператор не может быть пустым
Вес должен быть больше нуля
Статус только из списка допустимых