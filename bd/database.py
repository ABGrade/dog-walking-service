from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
import redis
import json
import threading

from settings import DB_CONFIG

from settings import REDIS_CONFIG
redis_client = redis.Redis(**REDIS_CONFIG)

def get_connection():
    """Создает и возвращает подключение к БД"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

def hash_password(password: str) -> str:
    """Хеширование пароля (SHA-256)"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def authenticate_user(email, password):
    """Проверяет логин/пароль и возвращает данные юзера и его роль"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        pwd_hash = hash_password(password)
        cur.execute("""
            SELECT u.id, u.first_name, u.last_name, u.email, r.id as role_id, r.name as role_name
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            WHERE u.email = %s AND u.password_hash = %s
        """, (email, pwd_hash))
        
        user = cur.fetchone()
        return user # Возвращает словарь с данными или None, если неверный пароль
        
    except Exception as e:
        print(f"Ошибка БД (auth): {e}")
        return None
    finally:
        cur.close()
        conn.close()

def register_user(name, phone, email, password, is_walker):
    """Создает нового пользователя и назначает ему роль"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        pwd_hash = hash_password(password)
        
        # Разделяем введенное имя на first_name и last_name
        name_parts = name.strip().split(maxsplit=1)
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        # 1. Вставляем пользователя
        cur.execute("""
            INSERT INTO users (first_name, last_name, email, phone, password_hash)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (first_name, last_name, email, phone, pwd_hash))
        user_id = cur.fetchone()['id']
        
        # 2. Назначаем роль: 2 - выгульщик, 1 - владелец
        role_id = 2 if is_walker else 1
        cur.execute("INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)", (user_id, role_id))
        
        conn.commit()
        
        # 3. Возвращаем профиль, чтобы сразу "залогинить" юзера в приложении
        return {
            "id": user_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "role_id": role_id,
            "role_name": "выгульщик" if is_walker else "владелец"
        }
    except psycopg2.errors.UniqueViolation:
        # Если Email уже есть в базе
        conn.rollback()
        return "EMAIL_EXISTS"
    except Exception as e:
        conn.rollback()
        print(f"Ошибка БД (register): {e}")
        return None
    finally:
        cur.close()
        conn.close()

def _save_breeds_to_redis(breeds):
    """Вспомогательная функция для асинхронного сохранения"""
    try:
        mapping = {b['id']: b['name'] for b in breeds}
        redis_client.hset("dog_breeds", mapping=mapping)
        redis_client.expire("dog_breeds", 3600)
        print("Породы успешно закэшированы в Redis (фоновый поток)")
    except Exception as e:
        print(f"Ошибка фонового сохранения в Redis: {e}")

def get_breeds():
    """Получает породы собак. Сначала ищет в Redis, затем в Postgres."""
    try:
        cached = redis_client.hgetall("dog_breeds")
        if cached:
            return [{"id": int(k), "name": v} for k, v in cached.items()]
    except redis.RedisError:
        pass

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, name FROM dog_breeds ORDER BY name")
        breeds = cur.fetchall()
        if breeds:
            # ЗАПУСК СОХРАНЕНИЯ В ОТДЕЛЬНОМ ПОТОКЕ
            thread = threading.Thread(target=_save_breeds_to_redis, args=(breeds,), daemon=True)
            thread.start()
        return breeds
    finally:
        cur.close()
        conn.close()

# ==========================================
# POSTGRES: РАБОТА С КЛИЕНТСКИМИ ДАННЫМИ
# ==========================================
def get_user_dogs(owner_id):
    """Получает всех собак конкретного владельца"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT d.id, d.name, b.name as breed_name
            FROM dogs d
            JOIN dog_breeds b ON d.breed_id = b.id
            WHERE d.owner_id = %s
        """, (owner_id,))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def add_dog(owner_id, name, breed_id, sex, birth_date, behavior, health):
    """Добавляет новую собаку в БД"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO dogs (owner_id, breed_id, name, sex, birth_date, behavior_notes, health_notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (owner_id, breed_id, name, sex, birth_date, behavior, health))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Ошибка БД (add_dog): {e}")
        return False
    finally:
        cur.close()
        conn.close()

def create_order(owner_id, dog_id, start_at, end_at, address, comment):
    """Создает заказ и привязывает к нему собаку"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        # 1. Создаем сам заказ (статус 1 - создан, выгульщика пока нет)
        # Сумму пока захардкодим для примера, в реале она считается от времени услуги
        total_cost = 1500 
        cur.execute("""
            INSERT INTO orders (owner_id, status_id, created_at, planned_start_at, planned_end_at, walk_address, total_cost, comment)
            VALUES (%s, 1, NOW(), %s, %s, %s, %s, %s)
            RETURNING id
        """, (owner_id, start_at, end_at, address, total_cost, comment))
        order_id = cur.fetchone()['id']
        
        # 2. Привязываем выбранную собаку к заказу
        cur.execute("INSERT INTO order_dogs (order_id, dog_id) VALUES (%s, %s)", (order_id, dog_id))
        
        # 3. Создаем запись о неоплаченном платеже
        cur.execute("""
            INSERT INTO payments (order_id, amount, payment_method, payment_status)
            VALUES (%s, %s, 'Карта', 'pending')
        """, (order_id, total_cost))
        
        conn.commit()
        return order_id
    except Exception as e:
        conn.rollback()
        print(f"Ошибка БД (create_order): {e}")
        return None
    finally:
        invalidate_orders_cache()
        cur.close()
        conn.close()

def get_available_orders(search_query="", payment_filter="Все"):
    """Получает список свободных заказов с учетом фильтров"""
    cache_key = "available_orders_all"
    if not search_query and payment_filter == "Все":
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                print("Лента заказов получена из Redis")
                return json.loads(cached_data)
        except redis.RedisError:
            pass
    
    conn = get_connection()
    cur = conn.cursor()
    try:
        query = """
            SELECT o.id, o.walk_address, o.total_cost, 
                   to_char(o.planned_start_at, 'DD.MM.YYYY, HH24:MI') as date_str,
                   d.name as dog_name, b.name as breed_name,
                   COALESCE(p.payment_status, 'неизвестно') as pay_status,
                   u.phone as owner_phone
            FROM orders o
            JOIN order_dogs od ON o.id = od.order_id
            JOIN dogs d ON od.dog_id = d.id
            JOIN dog_breeds b ON d.breed_id = b.id
            LEFT JOIN payments p ON o.id = p.order_id
            JOIN users u ON o.owner_id = u.id
            WHERE o.status_id = 1 AND o.walker_id IS NULL
        """
        params = []
        
        if search_query:
            query += " AND o.walk_address ILIKE %s"
            params.append(f"%{search_query}%")
            
        if payment_filter == "Оплачено":
            query += " AND p.payment_status = 'оплачен'"
        elif payment_filter == "Не оплачено":
            query += " AND (p.payment_status = 'pending' OR p.payment_status IS NULL)"
            
        query += " ORDER BY o.planned_start_at ASC"
        
        cur.execute(query, tuple(params))
        orders = cur.fetchall()
        if not search_query and payment_filter == "Все" and orders:
            try:
                redis_client.set(cache_key, json.dumps(orders, default=str), ex=300)
            except redis.RedisError:
                pass
        return orders
    
    finally:
        cur.close()
        conn.close()

def invalidate_orders_cache():
    """Удаляет закэшированный список заказов при создании нового или принятии заказа"""
    try:
        redis_client.delete("available_orders_all")
    except redis.RedisError:
        pass

def get_walkers():
    """Получает список всех выгульщиков с их средним рейтингом"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Считаем средний рейтинг из таблицы reviews
        cur.execute("""
            SELECT u.id, u.first_name, u.last_name,
                   COUNT(r.id) as reviews_count,
                   COALESCE(ROUND(AVG(r.rating), 1), 0) as avg_rating
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            LEFT JOIN orders o ON u.id = o.walker_id
            LEFT JOIN reviews r ON o.id = r.order_id
            WHERE ur.role_id = 2
            GROUP BY u.id
            ORDER BY avg_rating DESC, reviews_count DESC
        """)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def accept_order(order_id, walker_id):
    """Выгульщик берет заказ в работу (меняем статус на 2)"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE orders 
            SET walker_id = %s, status_id = 2 
            WHERE id = %s AND status_id = 1
            RETURNING id
        """, (walker_id, order_id))
        result = cur.fetchone()
        conn.commit()
        return bool(result)
    except Exception as e:
        conn.rollback()
        print(f"Ошибка БД (accept_order): {e}")
        return False
    finally:
        invalidate_orders_cache()
        cur.close()
        conn.close()

def start_walk(order_id):
    """Создает запись о начале прогулки в таблице walks"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO walks (order_id, actual_start_at, status)
            VALUES (%s, NOW(), 'in_progress')
            RETURNING id
        """, (order_id,))
        walk_id = cur.fetchone()['id']
        conn.commit()
        return walk_id
    except Exception as e:
        conn.rollback()
        print(f"Ошибка БД (start_walk): {e}")
        return None
    finally:
        cur.close()
        conn.close()

def complete_walk_and_report(order_id, walk_id, summary):
    """Завершает прогулку, меняет статус заказа и сохраняет отчет"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        # 1. Завершаем прогулку
        cur.execute("""
            UPDATE walks 
            SET actual_end_at = NOW(), status = 'completed'
            WHERE id = %s
        """, (walk_id,))
        
        # 2. Обновляем статус заказа на "завершен" (3)
        cur.execute("UPDATE orders SET status_id = 3 WHERE id = %s", (order_id,))
        
        # 3. Пишем текст отчета
        cur.execute("""
            INSERT INTO reports (walk_id, created_at, summary) 
            VALUES (%s, NOW(), %s)
        """, (walk_id, summary))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Ошибка БД (complete_walk_and_report): {e}")
        return False
    finally:
        cur.close()
        conn.close()

def get_order_details_for_client(order_id):
    """Возвращает всю информацию о заказе для экрана клиента"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT o.id, o.status_id, 
                   u.first_name as walker_name, u.last_name as walker_last,
                   p.payment_status, p.amount,
                   to_char(w.actual_start_at, 'HH24:MI') as start_time,
                   to_char(w.actual_end_at, 'HH24:MI') as end_time,
                   r.summary as report_summary,
                   rev.rating as review_rating,
                   rev.comment as review_comment
            FROM orders o
            LEFT JOIN users u ON o.walker_id = u.id
            LEFT JOIN payments p ON o.id = p.order_id
            LEFT JOIN walks w ON o.id = w.order_id
            LEFT JOIN reports r ON w.id = r.walk_id
            LEFT JOIN reviews rev ON o.id = rev.order_id
            WHERE o.id = %s
        """, (order_id,))
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()

def add_or_update_review(user_id, order_id, rating, comment):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM reviews WHERE order_id = %s", (order_id,))
        cur.execute("""
            INSERT INTO reviews (user_id, order_id, rating, comment)
            VALUES (%s, %s, %s, %s)
        """, (user_id, order_id, rating, comment))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Ошибка БД (add_or_update_review): {e}")
        return False
    finally:
        cur.close()
        conn.close()