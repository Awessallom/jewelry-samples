"""
Эмулятор оборудования для генерации проб драгоценных металлов.
Отправляет данные в REST API каждые 2 секунды.
"""

import requests
import random
import time
import os
from datetime import datetime

# Конфигурация — читаем переменную окружения, если она есть
API_URL = os.getenv("API_URL", "http://localhost:8000/samples")
OPERATORS = ["John First", "Michael Second", "Andrew Third", "Nick Fourth", "Carlos Fifth"]
SAMPLE_PREFIXES = ["AU", "AG", "PT", "PD", "RH"]  # Золото, Серебро, Платина, Палладий, Родий

def generate_sample_code():
    """Генерирует уникальный код пробы: AU-001, AG-042, PT-999"""
    prefix = random.choice(SAMPLE_PREFIXES)
    number = random.randint(1, 999)
    return f"{prefix}-{number:03d}"

def generate_weight():
    """Генерирует случайный вес от 0.1 до 50.0 грамм с 2 знаками"""
    return round(random.uniform(0.1, 50.0), 2)

def send_sample_to_api(sample_code, weight, operator):
    """Отправляет пробу в API и возвращает результат"""
    payload = {
        "sample_code": sample_code,
        "weight": weight,
        "operator": operator
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=5)
        
        if response.status_code == 201:
            print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] Создана проба: "
                  f"{sample_code} | Вес: {weight}г | Оператор: {operator}")
            print(f"   Ответ сервера: ID={response.json()['id']}, "
                  f"Статус={response.json()['status']}")
            return True
        else:
            print(f"❌ [{datetime.now().strftime('%H:%M:%S')}] Ошибка {response.status_code}: "
                  f"{response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ [{datetime.now().strftime('%H:%M:%S')}] Не удалось подключиться к API. "
              f"Убедитесь, что сервер запущен на {API_URL}")
        return False
    except Exception as e:
        print(f"❌ [{datetime.now().strftime('%H:%M:%S')}] Ошибка: {e}")
        return False

def main():
    """Основной цикл эмулятора"""
    print("=" * 60)
    print("ЭМУЛЯТОР ОБОРУДОВАНИЯ ДЛЯ ПРОБ ДРАГОЦЕННЫХ МЕТАЛЛОВ")
    print("=" * 60)
    print(f"API endpoint: {API_URL}")
    print("Генерация проб каждые 2 секунды...")
    print("Для остановки нажмите Ctrl+C")
    print("-" * 60)
    
    samples_created = 0
    samples_failed = 0
    
    try:
        while samples_created < 20:  # Создаём минимум 20 проб
            # Генерируем данные
            sample_code = generate_sample_code()
            weight = generate_weight()
            operator = random.choice(OPERATORS)
            
            # Отправляем в API
            if send_sample_to_api(sample_code, weight, operator):
                samples_created += 1
            else:
                samples_failed += 1
            
            # Ждём 2 секунды перед следующей пробой
            time.sleep(2)
            
            # Показываем прогресс каждые 5 проб
            if samples_created % 5 == 0 and samples_created > 0:
                print(f"📊 Прогресс: создано {samples_created} проб, "
                      f"ошибок: {samples_failed}")
                print("-" * 60)
                
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print(f"⚠️  Остановка пользователем")
    
    finally:
        print("=" * 60)
        print(f"📊 ИТОГОВАЯ СТАТИСТИКА:")
        print(f"   ✅ Успешно создано: {samples_created} проб")
        print(f"   ❌ Ошибок: {samples_failed}")
        print(f"   📦 Всего попыток: {samples_created + samples_failed}")
        print("=" * 60)

if __name__ == "__main__":
    main()