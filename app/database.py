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
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def authenticate_user(email, password):
    conn = get_connection()
    cur = conn.cursor()
    try:
        pwd_hash = hash_password(password)
        cur.execute('\n            SELECT u.id, u.first_name, u.last_name, u.email, r.id as role_id, r.name as role_name\n            FROM users u\n            JOIN user_roles ur ON u.id = ur.user_id\n            JOIN roles r ON ur.role_id = r.id\n            WHERE u.email = %s AND u.password_hash = %s\n        ', (email, pwd_hash))
        user = cur.fetchone()
        return user
    except Exception as e:
        print(f'Ошибка БД (auth): {e}')
        return None
    finally:
        cur.close()
        conn.close()

def register_user(name, phone, email, password, is_walker):
    conn = get_connection()
    cur = conn.cursor()
    try:
        pwd_hash = hash_password(password)
        name_parts = name.strip().split(maxsplit=1)
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        cur.execute('\n            INSERT INTO users (first_name, last_name, email, phone, password_hash)\n            VALUES (%s, %s, %s, %s, %s)\n            RETURNING id\n        ', (first_name, last_name, email, phone, pwd_hash))
        user_id = cur.fetchone()['id']
        role_id = 2 if is_walker else 1
        cur.execute('INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)', (user_id, role_id))
        conn.commit()
        return {'id': user_id, 'first_name': first_name, 'last_name': last_name, 'email': email, 'role_id': role_id, 'role_name': 'выгульщик' if is_walker else 'владелец'}
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return 'EMAIL_EXISTS'
    except Exception as e:
        conn.rollback()
        print(f'Ошибка БД (register): {e}')
        return None
    finally:
        cur.close()
        conn.close()

def _save_breeds_to_redis(breeds):
    try:
        mapping = {b['id']: b['name'] for b in breeds}
        redis_client.hset('dog_breeds', mapping=mapping)
        redis_client.expire('dog_breeds', 3600)
        print('Породы успешно закэшированы в Redis (фоновый поток)')
    except Exception as e:
        print(f'Ошибка фонового сохранения в Redis: {e}')

def get_breeds():
    try:
        cached = redis_client.hgetall('dog_breeds')
        if cached:
            return [{'id': int(k), 'name': v} for k, v in cached.items()]
    except redis.RedisError:
        pass
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT id, name FROM dog_breeds ORDER BY name')
        breeds = cur.fetchall()
        if breeds:
            thread = threading.Thread(target=_save_breeds_to_redis, args=(breeds,), daemon=True)
            thread.start()
        return breeds
    finally:
        cur.close()
        conn.close()

def get_user_dogs(owner_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('\n            SELECT d.id, d.name, b.name as breed_name\n            FROM dogs d\n            JOIN dog_breeds b ON d.breed_id = b.id\n            WHERE d.owner_id = %s\n        ', (owner_id,))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def add_dog(owner_id, name, breed_id, sex, birth_date, behavior, health):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('\n            INSERT INTO dogs (owner_id, breed_id, name, sex, birth_date, behavior_notes, health_notes)\n            VALUES (%s, %s, %s, %s, %s, %s, %s)\n        ', (owner_id, breed_id, name, sex, birth_date, behavior, health))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f'Ошибка БД (add_dog): {e}')
        return False
    finally:
        cur.close()
        conn.close()

def create_order(owner_id, dog_id, start_at, end_at, address, comment):
    conn = get_connection()
    cur = conn.cursor()
    try:
        total_cost = 1500
        cur.execute('\n            SELECT create_order(\n                %s::INTEGER, \n                %s::TIMESTAMP, \n                %s::TIMESTAMP, \n                %s::VARCHAR, \n                %s::DECIMAL, \n                ARRAY[%s]::INTEGER[]\n            ) as id\n        ', (owner_id, start_at, end_at, address, total_cost, dog_id))
        order_id = cur.fetchone()['id']
        if comment:
            cur.execute('UPDATE orders SET comment = %s WHERE id = %s', (comment, order_id))
        cur.execute("\n            INSERT INTO payments (order_id, amount, payment_method, payment_status)\n            VALUES (%s, %s, 'Карта', 'pending')\n            ON CONFLICT (order_id) DO NOTHING\n        ", (order_id, total_cost))
        conn.commit()
        return order_id
    except Exception as e:
        conn.rollback()
        print(f'Ошибка БД (create_order): {e}')
        return None
    finally:
        invalidate_orders_cache()
        cur.close()
        conn.close()

def get_available_orders(search_query='', payment_filter='Все'):
    cache_key = 'available_orders_all'
    if not search_query and payment_filter == 'Все':
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                print('Лента заказов получена из Redis')
                return json.loads(cached_data)
        except redis.RedisError:
            pass
    conn = get_connection()
    cur = conn.cursor()
    try:
        query = "\n            SELECT o.id, o.walk_address, o.total_cost, \n                   to_char(o.planned_start_at, 'DD.MM.YYYY, HH24:MI') as date_str,\n                   d.name as dog_name, b.name as breed_name,\n                   COALESCE(p.payment_status, 'неизвестно') as pay_status,\n                   u.phone as owner_phone\n            FROM orders o\n            JOIN order_dogs od ON o.id = od.order_id\n            JOIN dogs d ON od.dog_id = d.id\n            JOIN dog_breeds b ON d.breed_id = b.id\n            LEFT JOIN payments p ON o.id = p.order_id\n            JOIN users u ON o.owner_id = u.id\n            WHERE o.status_id = 1 AND o.walker_id IS NULL\n        "
        params = []
        if search_query:
            digits_only = ''.join([c for c in search_query if c.isdigit()])
            if digits_only:
                query += "\n                    AND (\n                        CAST(o.id AS TEXT) ILIKE %s\n                        OR regexp_replace(u.phone, '\\D', '', 'g') ILIKE %s\n                    )\n                "
                params.extend([f'%{search_query}%', f'%{digits_only}%'])
            else:
                query += '\n                    AND CAST(o.id AS TEXT) ILIKE %s\n                '
                params.append(f'%{search_query}%')
        if payment_filter == 'Оплачено':
            query += " AND p.payment_status = 'оплачен'"
        elif payment_filter == 'Не оплачено':
            query += " AND (p.payment_status = 'pending' OR p.payment_status IS NULL)"
        query += ' ORDER BY o.planned_start_at ASC'
        cur.execute(query, tuple(params))
        orders = cur.fetchall()
        if not search_query and payment_filter == 'Все' and orders:
            try:
                redis_client.set(cache_key, json.dumps(orders, default=str), ex=300)
            except redis.RedisError:
                pass
        return orders
    finally:
        cur.close()
        conn.close()

def invalidate_orders_cache():
    try:
        redis_client.delete('available_orders_all')
    except redis.RedisError:
        pass

def get_walkers():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('\n            SELECT u.id, u.first_name, u.last_name,\n                   COUNT(r.id) as reviews_count,\n                   COALESCE(ROUND(AVG(r.rating), 1), 0) as avg_rating\n            FROM users u\n            JOIN user_roles ur ON u.id = ur.user_id\n            LEFT JOIN orders o ON u.id = o.walker_id\n            LEFT JOIN reviews r ON o.id = r.order_id\n            WHERE ur.role_id = 2\n            GROUP BY u.id\n            ORDER BY avg_rating DESC, reviews_count DESC\n        ')
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def accept_order(order_id, walker_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT accept_order(%s, %s) as success', (order_id, walker_id))
        result = cur.fetchone()['success']
        conn.commit()
        return bool(result)
    except Exception as e:
        conn.rollback()
        print(f'Ошибка БД (accept_order): {e}')
        return False
    finally:
        invalidate_orders_cache()
        cur.close()
        conn.close()

def start_walk(order_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("\n            INSERT INTO walks (order_id, actual_start_at, status)\n            VALUES (%s, NOW(), 'in_progress')\n            RETURNING id\n        ", (order_id,))
        walk_id = cur.fetchone()['id']
        conn.commit()
        return walk_id
    except Exception as e:
        conn.rollback()
        print(f'Ошибка БД (start_walk): {e}')
        return None
    finally:
        cur.close()
        conn.close()

def complete_walk_and_report(order_id, walk_id, summary):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("\n            UPDATE walks \n            SET actual_end_at = NOW(), status = 'completed'\n            WHERE id = %s\n        ", (walk_id,))
        cur.execute('UPDATE orders SET status_id = 3 WHERE id = %s', (order_id,))
        cur.execute('\n            INSERT INTO reports (walk_id, created_at, summary) \n            VALUES (%s, NOW(), %s)\n        ', (walk_id, summary))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f'Ошибка БД (complete_walk_and_report): {e}')
        return False
    finally:
        cur.close()
        conn.close()

def get_order_details_for_client(order_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("\n            SELECT o.id, o.status_id, \n                   u.first_name as walker_name, u.last_name as walker_last,\n                   p.payment_status, p.amount,\n                   to_char(w.actual_start_at, 'HH24:MI') as start_time,\n                   to_char(w.actual_end_at, 'HH24:MI') as end_time,\n                   r.summary as report_summary,\n                   rev.rating as review_rating,\n                   rev.comment as review_comment\n            FROM orders o\n            LEFT JOIN users u ON o.walker_id = u.id\n            LEFT JOIN payments p ON o.id = p.order_id\n            LEFT JOIN walks w ON o.id = w.order_id\n            LEFT JOIN reports r ON w.id = r.walk_id\n            LEFT JOIN reviews rev ON o.id = rev.order_id\n            WHERE o.id = %s\n        ", (order_id,))
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()

def finish_walk(order_id, walk_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        from datetime import datetime
        cur.execute('SELECT actual_start_at FROM walks WHERE id = %s', (walk_id,))
        start_res = cur.fetchone()
        start_at = start_res['actual_start_at'] if start_res else datetime.now()
        cur.execute('SELECT complete_walk(%s::INTEGER, %s::TIMESTAMP, NOW()::TIMESTAMP) as id', (order_id, start_at))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f'Ошибка БД (finish_walk): {e}')
        return False
    finally:
        cur.close()
        conn.close()

def update_report(walk_id, summary):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('\n            UPDATE reports\n            SET summary = %s\n            WHERE walk_id = %s\n        ', (summary, walk_id))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f'Ошибка БД (update_report): {e}')
        return False
    finally:
        cur.close()
        conn.close()

def get_order_payment_status(order_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT payment_status FROM payments WHERE order_id = %s', (order_id,))
        res = cur.fetchone()
        return res['payment_status'] if res else None
    except Exception as e:
        print(f'Ошибка БД (get_order_payment_status): {e}')
        return None
    finally:
        cur.close()
        conn.close()

def get_order_walk_status(order_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('\n            SELECT id, actual_start_at, actual_end_at, status \n            FROM walks \n            WHERE order_id = %s\n            ORDER BY id DESC LIMIT 1\n        ', (order_id,))
        res = cur.fetchone()
        if not res:
            return (None, None)
        walk_id = res['id']
        if res['actual_end_at'] is None:
            return ('in_progress', walk_id)
        else:
            return ('completed', walk_id)
    except Exception as e:
        print(f'Ошибка БД (get_order_walk_status): {e}')
        return (None, None)
    finally:
        cur.close()
        conn.close()

def get_client_orders(client_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("\n            SELECT o.id, o.walk_address, o.total_cost, o.status_id,\n                   to_char(o.planned_start_at, 'DD.MM.YYYY, HH24:MI') as date_str,\n                   d.name as dog_name, b.name as breed_name,\n                   COALESCE(p.payment_status, 'неизвестно') as pay_status,\n                   u.first_name as walker_name, u.last_name as walker_last, u.phone as walker_phone\n            FROM orders o\n            JOIN order_dogs od ON o.id = od.order_id\n            JOIN dogs d ON od.dog_id = d.id\n            JOIN dog_breeds b ON d.breed_id = b.id\n            LEFT JOIN payments p ON o.id = p.order_id\n            LEFT JOIN users u ON o.walker_id = u.id\n            WHERE o.owner_id = %s\n            ORDER BY o.id DESC\n        ", (client_id,))
        return cur.fetchall()
    except Exception as e:
        print(f'Ошибка БД (get_client_orders): {e}')
        return []
    finally:
        cur.close()
        conn.close()

def get_walker_orders(walker_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("\n            SELECT o.id, o.walk_address, o.total_cost, o.status_id,\n                   to_char(o.planned_start_at, 'DD.MM.YYYY, HH24:MI') as date_str,\n                   d.name as dog_name, b.name as breed_name,\n                   COALESCE(p.payment_status, 'неизвестно') as pay_status,\n                   u.first_name as owner_name, u.last_name as owner_last, u.phone as owner_phone\n            FROM orders o\n            JOIN order_dogs od ON o.id = od.order_id\n            JOIN dogs d ON od.dog_id = d.id\n            JOIN dog_breeds b ON d.breed_id = b.id\n            LEFT JOIN payments p ON o.id = p.order_id\n            JOIN users u ON o.owner_id = u.id\n            WHERE o.walker_id = %s\n            ORDER BY o.id DESC\n        ", (walker_id,))
        return cur.fetchall()
    except Exception as e:
        print(f'Ошибка БД (get_walker_orders): {e}')
        return []
    finally:
        cur.close()
        conn.close()

def add_or_update_review(user_id, order_id, rating, comment):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM reviews WHERE order_id = %s", (order_id,))
        cur.execute("\n            INSERT INTO reviews (user_id, order_id, rating, comment)\n            VALUES (%s, %s, %s, %s)\n        ", (user_id, order_id, rating, comment))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Ошибка БД (add_or_update_review): {e}")
        return False
    finally:
        cur.close()
        conn.close()