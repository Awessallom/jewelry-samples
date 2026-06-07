"""
Автоматические тесты для REST API проб драгоценных металлов
Запуск: pytest tests/test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app import models

# ============================================
# НАСТРОЙКА ТЕСТОВОЙ БАЗЫ ДАННЫХ
# ============================================

# Создаём тестовую БД в памяти (не сохраняется на диск)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # Для SQLite в памяти
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создаём таблицы в тестовой БД
Base.metadata.create_all(bind=engine)

# Переопределяем зависимость get_db для тестов
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Подменяем реальную зависимость на тестовую
app.dependency_overrides[get_db] = override_get_db

# Создаём тестовый клиент FastAPI
client = TestClient(app)


# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

def create_test_sample(sample_code="TEST-001", weight=10.5, operator="Test Operator"):
    """Создаёт тестовую пробу и возвращает её ID"""
    response = client.post(
        "/samples",
        json={
            "sample_code": sample_code,
            "weight": weight,
            "operator": operator
        }
    )
    assert response.status_code == 201
    return response.json()["id"]


def clear_database():
    """Очищает таблицу samples (для изоляции тестов)"""
    db = TestingSessionLocal()
    try:
        db.query(models.Sample).delete()
        db.commit()
    finally:
        db.close()


# ============================================
# ТЕСТ 1: Создание новой пробы (позитивный сценарий)
# ============================================

def test_create_sample_success():
    """Проверяет успешное создание пробы с валидными данными"""
    clear_database()  # Начинаем с чистой БД
    
    response = client.post(
        "/samples",
        json={
            "sample_code": "AU-001",
            "weight": 12.5,
            "operator": "John Doe"
        }
    )
    
    # Проверяем статус ответа
    assert response.status_code == 201
    
    # Проверяем структуру ответа
    data = response.json()
    assert "id" in data
    assert data["sample_code"] == "AU-001"
    assert data["weight"] == 12.5
    assert data["operator"] == "John Doe"
    assert data["status"] == "created"  # Автоматически установлен
    assert "created_at" in data
    
    # Проверяем, что данные реально сохранились в БД
    db = TestingSessionLocal()
    sample = db.query(models.Sample).filter(models.Sample.id == data["id"]).first()
    assert sample is not None
    assert sample.sample_code == "AU-001"
    db.close()


# ============================================
# ТЕСТ 2: Ошибка при отрицательном весе
# ============================================

def test_create_sample_negative_weight():
    """Проверяет, что API возвращает ошибку при отрицательном весе"""
    clear_database()
    
    response = client.post(
        "/samples",
        json={
            "sample_code": "AU-002",
            "weight": -10.5,  # Отрицательный вес
            "operator": "John Doe"
        }
    )
    
    # Должна быть ошибка валидации
    assert response.status_code == 422
    
    # Проверяем сообщение об ошибке
    error_data = response.json()
    assert "detail" in error_data
    # Ищем ошибку, связанную с weight
    weight_errors = [e for e in error_data["detail"] if e["loc"] == ["body", "weight"]]
    assert len(weight_errors) > 0
    assert "greater than 0" in weight_errors[0]["msg"] or "больше нуля" in weight_errors[0]["msg"]


# ============================================
# ТЕСТ 3: Ошибка при пустом коде пробы
# ============================================

def test_create_sample_empty_code():
    """Проверяет, что API не принимает пустой код пробы"""
    clear_database()
    
    response = client.post(
        "/samples",
        json={
            "sample_code": "",  # Пустая строка
            "weight": 10.5,
            "operator": "John Doe"
        }
    )
    
    assert response.status_code == 422
    
    # Проверяем, что ошибка связана с sample_code
    error_data = response.json()
    code_errors = [e for e in error_data["detail"] if "sample_code" in str(e["loc"])]
    assert len(code_errors) > 0


# ============================================
# ТЕСТ 4: Получение списка проб
# ============================================

def test_get_samples_list():
    """Проверяет получение списка всех проб"""
    clear_database()
    
    # Создаём несколько проб
    create_test_sample("LIST-001", 10.0, "Operator1")
    create_test_sample("LIST-002", 20.0, "Operator2")
    create_test_sample("LIST-003", 30.0, "Operator3")
    
    # Получаем список
    response = client.get("/samples")
    
    assert response.status_code == 200
    data = response.json()
    
    # Должно быть 3 пробы
    assert len(data) == 3
    
    # Проверяем, что все поля присутствуют
    for sample in data:
        assert "id" in sample
        assert "sample_code" in sample
        assert "weight" in sample
        assert "operator" in sample
        assert "status" in sample
        assert "created_at" in sample


# ============================================
# ТЕСТ 5: Получение конкретной пробы по ID
# ============================================

def test_get_sample_by_id():
    """Проверяет получение конкретной пробы по её ID"""
    clear_database()
    
    # Создаём пробу
    sample_id = create_test_sample("GETBYID-001", 15.5, "FindMe")
    
    # Получаем её по ID
    response = client.get(f"/samples/{sample_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == sample_id
    assert data["sample_code"] == "GETBYID-001"
    assert data["weight"] == 15.5
    assert data["operator"] == "FindMe"


def test_get_nonexistent_sample():
    """Проверяет, что API возвращает 404 при запросе несуществующей пробы"""
    clear_database()
    
    response = client.get("/samples/99999")
    
    assert response.status_code == 404
    assert "не найдена" in response.json()["detail"].lower() or "not found" in response.json()["detail"].lower()


# ============================================
# ТЕСТ 6: Изменение статуса пробы
# ============================================

def test_update_sample_status():
    """Проверяет успешное изменение статуса пробы"""
    clear_database()
    
    # Создаём пробу со статусом "created"
    sample_id = create_test_sample("STATUS-001", 10.0, "StatusTester")
    
    # Меняем статус на "measured"
    response = client.patch(
        f"/samples/{sample_id}/status",
        json={"status": "measured"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "measured"
    
    # Проверяем, что статус реально изменился в БД
    db = TestingSessionLocal()
    sample = db.query(models.Sample).filter(models.Sample.id == sample_id).first()
    assert sample.status == "measured"
    db.close()


def test_update_status_invalid_value():
    """Проверяет, что API не принимает недопустимый статус"""
    clear_database()
    
    sample_id = create_test_sample("STATUS-002", 20.0, "InvalidTester")
    
    response = client.patch(
        f"/samples/{sample_id}/status",
        json={"status": "invalid_status_123"}  # Недопустимый статус
    )
    
    assert response.status_code == 422
    error_data = response.json()
    
    # Проверяем, что ошибка связана со статусом
    status_errors = [e for e in error_data["detail"] if "status" in str(e["loc"])]
    assert len(status_errors) > 0


def test_update_status_nonexistent_sample():
    """Проверяет, что при обновлении статуса несуществующей пробы возвращается 404"""
    clear_database()
    
    response = client.patch(
        "/samples/99999/status",
        json={"status": "approved"}
    )
    
    assert response.status_code == 404


# ============================================
# ТЕСТ 7: Получение сводного отчёта
# ============================================

def test_get_summary_report():
    """Проверяет корректность сводного отчёта"""
    clear_database()
    
    # Создаём пробы с разными весами и статусами
    create_test_sample("REP-01", 10.0, "Op1")  # status=created
    create_test_sample("REP-02", 20.0, "Op2")  # status=created
    create_test_sample("REP-03", 30.0, "Op3")  # status=created
    
    # Меняем статусы
    ids = [1, 2, 3]
    client.patch(f"/samples/{ids[0]}/status", json={"status": "measured"})
    client.patch(f"/samples/{ids[1]}/status", json={"status": "approved"})
    client.patch(f"/samples/{ids[2]}/status", json={"status": "rejected"})
    
    # Получаем отчёт
    response = client.get("/reports/summary")
    
    assert response.status_code == 200
    report = response.json()
    
    # Проверяем общую статистику
    assert report["total_samples"] == 3
    assert report["min_weight"] == 10.0
    assert report["max_weight"] == 30.0
    assert report["average_weight"] == 20.0  # (10+20+30)/3 = 20
    
    # Проверяем распределение по статусам
    assert "status_breakdown" in report
    breakdown = report["status_breakdown"]
    assert breakdown.get("measured") == 1
    assert breakdown.get("approved") == 1
    assert breakdown.get("rejected") == 1
    assert breakdown.get("created") is None or breakdown.get("created") == 0


def test_empty_report():
    """Проверяет отчёт при пустой базе данных"""
    clear_database()
    
    response = client.get("/reports/summary")
    
    assert response.status_code == 200
    report = response.json()
    
    assert report["total_samples"] == 0
    assert report["average_weight"] == 0
    assert report["min_weight"] == 0
    assert report["max_weight"] == 0
    assert report["status_breakdown"] == {}


# ============================================
# ТЕСТ 8: Пагинация (skip/limit)
# ============================================

def test_pagination():
    """Проверяет работу параметров пагинации skip и limit"""
    clear_database()
    
    # Создаём 10 проб
    for i in range(10):
        create_test_sample(f"PAGE-{i:03d}", float(i + 1), f"Op{i}")
    
    # Проверяем limit
    response = client.get("/samples?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    
    # Проверяем skip
    response = client.get("/samples?skip=5&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    
    # Проверяем, что ID разные (пропустили первые 5)
    ids = [item["id"] for item in data]
    assert min(ids) > 5  # Должны быть ID от 6 до 10


# ============================================
# ЗАПУСК ТЕСТОВ
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])