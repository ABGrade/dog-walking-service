from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from settings import DB_CONFIG
import psycopg2
from psycopg2.extras import RealDictCursor

# --- НАСТРОЙКИ БАЗЫ ДАННЫХ ---
DB_NAME = "dog_walking_bd"
DB_USER = "postgres"
DB_PASSWORD = "1" 
DB_HOST = "localhost"
DB_PORT = "5432"

def print_user(user):
    print(f"ID: {user['id']} | Роль: {user['role_name'].upper()}")
    print(f"Имя: {user['first_name']} {user['last_name']}")
    print(f"Телефон: {user['phone']}")
    print(f"Email (ЛОГИН): {user['email']}")
    print(f"ПАРОЛЬ (открытый вид): {user['email']}  <-- Использовать для входа")
    print("-" * 50)

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=RealDictCursor)
    except Exception as e:
        print(f"Ошибка подключения к БД: {e}")
        return

    query_random = """
        SELECT u.*, r.name as role_name
        FROM users u
        JOIN user_roles ur ON u.id = ur.user_id
        JOIN roles r ON ur.role_id = r.id
        WHERE r.id = %s
        ORDER BY RANDOM()
        LIMIT %s
    """

    print("\n" + "="*50)
    print("СЛУЧАЙНЫЕ ПОЛЬЗОВАТЕЛИ ДЛЯ ТЕСТИРОВАНИЯ:")
    print("="*50)
    
    print("\n--- ВЛАДЕЛЬЦЫ (КЛИЕНТЫ) ---")
    cur.execute(query_random, (1, 2))
    for u in cur.fetchall(): print_user(u)

    print("\n--- ВЫГУЛЬЩИКИ ---")
    cur.execute(query_random, (2, 2))
    for u in cur.fetchall(): print_user(u)

    print("\n--- АДМИНИСТРАТОР ---")
    cur.execute(query_random, (3, 1))
    for u in cur.fetchall(): print_user(u)

    print("\n" + "="*50)
    print("РЕЖИМ ПОИСКА ПО ЛОГИНУ (EMAIL)")
    print("="*50)
    
    while True:
        email = input("\nВведите Email пользователя (или 'q' для выхода): ").strip()
        if email.lower() == 'q':
            break

        cur.execute("""
            SELECT u.*, r.name as role_name
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            WHERE u.email = %s
        """, (email,))
        user = cur.fetchone()

        if user:
            print("\n✅ НАЙДЕН ПОЛЬЗОВАТЕЛЬ:")
            print_user(user)
        else:
            print("\n❌ Пользователь с таким Email не найден в базе.")

    cur.close()
    conn.close()

if __name__ == '__main__':
    main()