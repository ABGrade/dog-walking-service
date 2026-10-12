from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Настройки подключения
from settings import DB_CONFIG

def run_test_case(name, func, cur, is_error_path=False):
    print(f"\n--- Тест-кейс: {name} ---")
    cur.execute("SAVEPOINT tc_savepoint;")
    try:
        func()
        if is_error_path:
            cur.execute("ROLLBACK TO SAVEPOINT tc_savepoint;")
            print("Результат: [ПРОВАЛ] - Исключение не было выброшено!")
            return False
        else:
            cur.execute("RELEASE SAVEPOINT tc_savepoint;")
            print("Результат: [УСПЕШНО]")
            return True
    except Exception as e:
        cur.execute("ROLLBACK TO SAVEPOINT tc_savepoint;")
        if is_error_path:
            print(f"Результат: [УСПЕШНО] (Ожидаемое исключение перехвачено: {e})")
            return True
        else:
            print(f"Результат: [ПРОВАЛ] - Неожиданное исключение: {e}")
            return False

def verify():
    print("======================================================================")
    print("ЗАПУСК КОМПЛЕКСНОЙ ВЕРИФИКАЦИИ ХРАНИМЫХ ФУНКЦИЙ И ТРИГГЕРОВ В БД")
    print("======================================================================")
    
    conn = psycopg2.connect(**DB_CONFIG)
    # Отключаем автокоммит, чтобы управлять транзакциями вручную
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    passed = 0
    failed = 0
    
    try:
        # Находим тестовые ID
        cur.execute("""
            SELECT u.id as owner_id, d.id as dog_id 
            FROM users u 
            JOIN dogs d ON u.id = d.owner_id 
            LIMIT 1;
        """)
        sample = cur.fetchone()
        if not sample:
            print("Ошибка: Нет пользователей или собак в базе. Сначала запустите fill_data.py!")
            return
            
        owner_id = sample['owner_id']
        dog_id = sample['dog_id']
        
        cur.execute("""
            SELECT u.id 
            FROM users u 
            JOIN user_roles ur ON u.id = ur.user_id 
            WHERE ur.role_id = 2 
            LIMIT 1;
        """)
        walker_res = cur.fetchone()
        if not walker_res:
            print("Ошибка: Нет выгульщиков в базе!")
            return
        walker_id = walker_res['id']
        
        test_order_id = None
        test_walk_id = None

        # ----------------------------------------------------
        # 1. Функция create_order() - Успешное создание заказа
        # ----------------------------------------------------
        def tc_create_order_success():
            nonlocal test_order_id
            cur.execute("""
                SELECT create_order(
                    %s::INTEGER, 
                    NOW()::TIMESTAMP, 
                    (NOW() + interval '1 hour')::TIMESTAMP, 
                    'Тестовый адрес'::VARCHAR, 
                    1500::DECIMAL, 
                    ARRAY[%s]::INTEGER[]
                ) as order_id;
            """, (owner_id, dog_id))
            test_order_id = cur.fetchone()['order_id']
            print(f"Создан тестовый заказ ID: {test_order_id}")
            assert test_order_id is not None
            
        if run_test_case("create_order() - Создание заказа (Happy Path)", tc_create_order_success, cur):
            passed += 1
        else:
            failed += 1

        # ----------------------------------------------------
        # 2. Функция create_order() - Ошибка при неверной собаке
        # ----------------------------------------------------
        def tc_create_order_invalid_dog():
            cur.execute("""
                SELECT create_order(
                    %s::INTEGER, 
                    NOW()::TIMESTAMP, 
                    (NOW() + interval '1 hour')::TIMESTAMP, 
                    'Тестовый адрес'::VARCHAR, 
                    1500::DECIMAL, 
                    ARRAY[-999]::INTEGER[]
                ) as order_id;
            """, (owner_id,))
            cur.fetchone()

        if run_test_case("create_order() - Проверка валидации собак (Error Path)", tc_create_order_invalid_dog, cur, is_error_path=True):
            passed += 1
        else:
            failed += 1

        # ----------------------------------------------------
        # 3. Функция accept_order() - Успешное принятие заказа
        # ----------------------------------------------------
        def tc_accept_order_success():
            cur.execute("SELECT accept_order(%s::INTEGER, %s::INTEGER) as success;", (test_order_id, walker_id))
            success = cur.fetchone()['success']
            assert success is True

        if test_order_id and run_test_case("accept_order() - Успешное принятие (Happy Path)", tc_accept_order_success, cur):
            passed += 1
        else:
            failed += 1

        # ----------------------------------------------------
        # 4. Функция accept_order() - Повторный прием заказа (ошибка)
        # ----------------------------------------------------
        def tc_accept_order_already_accepted():
            cur.execute("SELECT accept_order(%s::INTEGER, %s::INTEGER) as success;", (test_order_id, walker_id))
            cur.fetchone()

        if test_order_id and run_test_case("accept_order() - Повторный прием (Error Path)", tc_accept_order_already_accepted, cur, is_error_path=True):
            passed += 1
        else:
            failed += 1

        # ----------------------------------------------------
        # 5. Функция complete_walk() - Успешное завершение прогулки
        # ----------------------------------------------------
        def tc_complete_walk_success():
            nonlocal test_walk_id
            cur.execute("SELECT complete_walk(%s::INTEGER, NOW()::TIMESTAMP, (NOW() + interval '30 minutes')::TIMESTAMP) as walk_id;", (test_order_id,))
            test_walk_id = cur.fetchone()['walk_id']
            assert test_walk_id is not None
            print(f"ID Прогулки: {test_walk_id}")

        if test_order_id and run_test_case("complete_walk() - Завершение прогулки (Happy Path)", tc_complete_walk_success, cur):
            passed += 1
        else:
            failed += 1

        # ----------------------------------------------------
        # 6. Триггер trg_generate_report() - Проверка автоотчета
        # ----------------------------------------------------
        def tc_trigger_report_generated():
            cur.execute("SELECT * FROM reports WHERE walk_id = %s;", (test_walk_id,))
            report = cur.fetchone()
            assert report is not None
            print(f"Автоматический отчет найден: '{report['summary']}'")
            assert "Автоматический отчет" in report['summary']

        if test_walk_id and run_test_case("Триггер trg_generate_report - Генерация отчета", tc_trigger_report_generated, cur):
            passed += 1
        else:
            failed += 1

        # ----------------------------------------------------
        # ИТОГИ ВЕРИФИКАЦИИ
        # ----------------------------------------------------
        print("\n=======================================================")
        print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        print(f"Всего тестов пройдено: {passed}")
        print(f"Тестов провалено: {failed}")
        print("=======================================================")
        
    except Exception as e:
        print(f"Произошла фатальная ошибка верификации: {e}")
    finally:
        # Откатываем основную транзакцию
        conn.rollback()
        cur.close()
        conn.close()
        print("\nТранзакция отменена (ROLLBACK). Изменения в БД отсутствуют.")

if __name__ == "__main__":
    verify()
