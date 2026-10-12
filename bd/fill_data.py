from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from settings import DB_CONFIG
import psycopg2
from psycopg2.extras import execute_values
from faker import Faker
import random
from datetime import timedelta, datetime
import hashlib

# --- НАСТРОЙКИ БАЗЫ ДАННЫХ ---
DB_NAME = "dog_walking_bd"
DB_USER = "postgres"
DB_PASSWORD = "1" 
DB_HOST = "localhost"
DB_PORT = "5432"

NUM_USERS = 1000
NUM_ORDERS = 10000
NUM_DOGS = int(NUM_USERS * 1.5)
OPEN_ORDERS_RATIO = 0.2

REAL_BREEDS = [
    "Австралийская короткохвостая пастушья собака", "Австралийская овчарка (аусси)",
    "Австралийская пастушья собака", "Австралийский келпи", "Австралийский терьер",
    "Австралийский шелковистый терьер", "Австрийская гончая", "Австрийский брудастый бракк",
    "Австрийский пинчер", "Азавак", "Азорская пастушья собака", "Аиди",
    "Акита-ину", "Алабай (среднеазиатская овчарка)", "Алан", "Алано",
    "Алапахский бульдог", "Алопекис", "Альпийская таксообразная гончая", "Аляскинский кли-кай",
    "Аляскинский маламут", "Американская акита", "Американская эскимосская собака", "Американский бандог",
    "Американский булли", "Американский бульдог", "Американский водяной спаниель", "Американский голый терьер",
    "Американский кокер-спаниель", "Американский мастиф", "Американский питбультерьер", "Американский стаффордширский терьер",
    "Американский фоксхаунд", "Анатолийская овчарка", "Английская енотовая гончая", "Английская овчарка",
    "Английский бульдог", "Английский водяной спаниель", "Английский кокер-спаниель", "Английский мастиф",
    "Английский пойнтер", "Английский сеттер", "Английский той-терьер", "Аппенцеллер зенненхунд",
    "Аргентинский дог", "Афганская борзая", "Аффенпинчер", "Басенджи",
    "Бассет-хаунд", "Бедлингтон-терьер", "Белая швейцарская овчарка", "Бельгийская овчарка",
    "Бернский зенненхунд", "Бигль", "Бишон фризе", "Бладхаунд",
    "Бобтейл (староанглийская овчарка)", "Боксер (немецкий)", "Болоньез", "Бордер-колли",
    "Бордер-терьер", "Бородатая колли", "Борзая (русская псовая)", "Бордоский дог",
    "Босерон", "Бостон-терьер", "Бразильский терьер", "Бразильский фила",
    "Бретонский эпаньоль", "Бриар", "Бульмастиф", "Бультерьер",
    "Бурбуль", "Бурят-монгольская собака", "Брюссельский гриффон", "Вельш-корги кардиган",
    "Вельш-корги пемброк", "Вельштерьер", "Вест-хайленд-уайт-терьер", "Венгерская выжла",
    "Восточно-европейская овчарка", "Гаванский бишон (хаванез)", "Гладкошерстный ретривер", "Золотистый ретривер",
    "Гордон (сеттер)", "Грейхаунд", "Далматин", "Данди-динмонт-терьер",
    "Датский брохольмер", "Джек-рассел-терьер", "Доберман", "Дратхаар",
    "Евразиер", "Ирландский волкодав", "Ирландский сеттер", "Ирландский терьер",
    "Испанский мастиф", "Итальянский кане-корсо", "Йоркширский терьер", "Ка-де-бо",
    "Кавалер-кинг-чарльз-спаниель", "Кавказская овчарка", "Канарский дог", "Карликовый пинчер (цвергпинчер)",
    "Керри-блю-терьер", "Кинг-чарльз-спаниель", "Китайская хохлатая собака", "Кламбер-спаниель",
    "Колли длинношерстный", "Колли короткошерстный", "Комондор", "Папильон",
    "Курцхаар", "Кувас", "Лабрадор-ретривер", "Ландзир",
    "Левретка", "Леонбергер", "Лхаса апсо", "Мальтийская болонка (мальтезе)",
    "Мальтипу", "Мареммо-абруцкая овчарка", "Миттельшнауцер", "Мопс",
    "Московская сторожевая", "Муди", "Неаполитанский мастиф", "Немецкий дог",
    "Немецкий охотничий терьер (ягдтерьер)", "Немецкая овчарка", "Ньюфаундленд", "Норвич-терьер",
    "Норфолк-терьер", "Парсон-рассел-терьер", "Пекинес", "Пиренейская горная собака",
    "Пиренейский мастиф", "Питбуль", "Померанский шпиц", "Помски",
    "Польская низинная овчарка", "Пудель", "Пули", "Пуми",
    "Пти-брабансон", "Ризеншнауцер", "Родезийский риджбек", "Ротвейлер",
    "Русская гончая", "Русская псовая борзая", "Русский охотничий спаниель", "Русский той",
    "Русский черный терьер", "Салюки", "Самоедская собака (самоед)", "Сенбернар",
    "Сиба-ину", "Сибирский хаски", "Силихем-терьер", "Скайтерьер",
    "Словацкий чувач", "Слюги", "Стаффордширский бультерьер", "Тайский риджбек",
    "Такса", "Тибетский мастиф", "Тибетский спаниель", "Тибетский терьер",
    "Тоса-ину", "Той-фокстерьер", "Фален", "Фландрский бувье",
    "Фокстерьер", "Французский бульдог", "Ховаварт", "Хортая борзая",
    "Цвергшнауцер", "Чау-чау", "Чехословацкая волчья собака", "Чихуахуа",
    "Шарпей", "Шелти", "Ши-тцу", "Шипперке (схипперке)",
    "Шотландский терьер (скотч-терьер)", "Эрдельтерьер", "Эскимосская лайка", "Южноафриканский бурбуль",
    "Южнорусская овчарка", "Японский хин", "Японский шпиц", "Бельгийский гриффон"
]

fake = Faker('ru_RU')

def generate_data():
    conn = psycopg2.connect(**DB_CONFIG, options='-c client_encoding=UTF8')
    cur = conn.cursor()
    
    print("Очистка старых данных...")
    cur.execute("TRUNCATE TABLE roles, users, order_statuses, dog_breeds, user_roles, dogs, orders, order_dogs, walks, reports, payments, reviews RESTART IDENTITY CASCADE;")
    
    print("Временное отключение триггера trg_generate_report...")
    cur.execute("ALTER TABLE walks DISABLE TRIGGER trg_generate_report;")
    
    print("1. Генерация справочников (Роли, Статусы, Породы)...")
    roles = [(1, 'владелец', 'Владелец собаки'), (2, 'выгульщик', 'Исполнитель'), (3, 'администратор', 'Админ системы')]
    execute_values(cur, "INSERT INTO roles (id, name, description) VALUES %s", roles)
    
    statuses = [(1, 'создан', ''), (2, 'принят', ''), (3, 'завершен', ''), (4, 'отменен', '')]
    execute_values(cur, "INSERT INTO order_statuses (id, name, description) VALUES %s", statuses)
    
    breeds = [(i+1, breed) for i, breed in enumerate(REAL_BREEDS)]
    execute_values(cur, "INSERT INTO dog_breeds (id, name) VALUES %s", breeds)
    
    print(f"2. Генерация {NUM_USERS} Пользователей...")
    users_data = []
    for i in range(NUM_USERS):
        email = f"user_{i}_{fake.email()}"
        password_hash = hashlib.sha256(email.encode('utf-8')).hexdigest()
        users_data.append((
            fake.first_name(), fake.last_name(), email, 
            fake.numerify('+7(###)###-##-##'), password_hash, fake.date_time_this_year(), True
        ))
    execute_values(cur, "INSERT INTO users (first_name, last_name, email, phone, password_hash, registered_at, is_active) VALUES %s RETURNING id", users_data, page_size=10000)
    user_ids = [row[0] for row in cur.fetchall()]
    
    num_owners = max(1, int(NUM_USERS * 0.75))
    num_admins = 1
    num_walkers = max(1, NUM_USERS - num_owners - num_admins)
    
    owner_ids = user_ids[0:num_owners]
    walker_ids = user_ids[num_owners:num_owners + num_walkers]
    admin_ids = user_ids[num_owners + num_walkers:]
    
    user_roles_data = []
    for uid in owner_ids:
        user_roles_data.append((1, uid))
    for uid in walker_ids:
        user_roles_data.append((2, uid))
    for uid in admin_ids:
        user_roles_data.append((3, uid))
        
    execute_values(cur, "INSERT INTO user_roles (role_id, user_id) VALUES %s", user_roles_data, page_size=10000)
    
    print(f"3. Генерация {NUM_DOGS} Собак...")
    dogs_data = []
    for owner in owner_ids:
        breed = random.randint(1, len(REAL_BREEDS))
        sex = random.choice(['М', 'Ж'])
        dogs_data.append((owner, breed, fake.first_name(), sex, fake.date_of_birth(minimum_age=1, maximum_age=15), fake.sentence(), fake.sentence()))
        
    remaining_dogs = NUM_DOGS - len(owner_ids)
    for _ in range(remaining_dogs):
        owner = random.choice(owner_ids)
        breed = random.randint(1, len(REAL_BREEDS))
        sex = random.choice(['М', 'Ж'])
        dogs_data.append((owner, breed, fake.first_name(), sex, fake.date_of_birth(minimum_age=1, maximum_age=15), fake.sentence(), fake.sentence()))
            
    execute_values(cur, "INSERT INTO dogs (owner_id, breed_id, name, sex, birth_date, behavior_notes, health_notes) VALUES %s RETURNING id, owner_id", dogs_data, page_size=10000)
    dogs_with_owners = cur.fetchall() 
    
    num_open = int(NUM_ORDERS * OPEN_ORDERS_RATIO)
    num_completed = NUM_ORDERS - num_open
    
    print(f"4. Генерация {NUM_ORDERS} заказов ({num_open} открытых, {num_completed} завершенных)...")
    orders_data = []
    
    # Сначала completed
    for i in range(num_completed):
        owner = random.choice(owner_ids)
        walker = random.choice(walker_ids)
        start_time = fake.date_time_this_month()
        end_time = start_time + timedelta(minutes=random.choice([30, 45, 60, 90]))
        orders_data.append((owner, walker, 3, start_time - timedelta(days=1), start_time, end_time, fake.address(), random.randint(500, 3000), fake.sentence()))
        
    # Затем open
    for i in range(num_open):
        owner = random.choice(owner_ids)
        start_time = datetime.now() + timedelta(days=random.randint(1, 15))
        end_time = start_time + timedelta(minutes=random.choice([30, 45, 60, 90]))
        orders_data.append((owner, None, 1, datetime.now() - timedelta(hours=random.randint(1, 24)), start_time, end_time, fake.address(), random.randint(500, 3000), fake.sentence()))
        
    execute_values(cur, "INSERT INTO orders (owner_id, walker_id, status_id, created_at, planned_start_at, planned_end_at, walk_address, total_cost, comment) VALUES %s RETURNING id, owner_id, status_id, planned_start_at, planned_end_at, total_cost", orders_data, page_size=10000)
    all_orders = cur.fetchall()
    
    completed_orders = all_orders[:num_completed]
    
    owner_dogs_map = {}
    for d_id, o_id in dogs_with_owners:
        if o_id not in owner_dogs_map:
            owner_dogs_map[o_id] = []
        owner_dogs_map[o_id].append(d_id)
        
    order_dogs_data = []
    completed_walks_data = []
    payments_data = []
    
    for order in all_orders:
        o_id, o_owner_id, o_status, o_start, o_end, o_cost = order
        owners_dogs = owner_dogs_map.get(o_owner_id, [])
        if owners_dogs:
            d_id = random.choice(owners_dogs)
        else:
            d_id = random.choice(dogs_with_owners)[0]
        order_dogs_data.append((o_id, d_id))
        
    for order in all_orders:
        o_id, o_owner_id, o_status, o_start, o_end, o_cost = order
        pay_method = random.choice(['Карта', 'СБП'])
        if o_status == 3:
            payments_data.append((o_id, o_cost, pay_method, 'оплачен', o_start - timedelta(minutes=15)))
        else:
            pay_status = 'оплачен' if random.random() < 0.8 else 'pending'
            paid_at = o_start - timedelta(hours=random.randint(1, 12)) if pay_status == 'оплачен' else None
            payments_data.append((o_id, o_cost, pay_method, pay_status, paid_at))
            
    for order in completed_orders:
        o_id, o_owner_id, o_status, o_start, o_end, o_cost = order
        completed_walks_data.append((o_id, o_start, o_end, 'завершена'))
        
    execute_values(cur, "INSERT INTO order_dogs (order_id, dog_id) VALUES %s", order_dogs_data, page_size=10000)
    execute_values(cur, "INSERT INTO payments (order_id, amount, payment_method, payment_status, paid_at) VALUES %s", payments_data, page_size=10000)
    execute_values(cur, "INSERT INTO walks (order_id, actual_start_at, actual_end_at, status) VALUES %s RETURNING id", completed_walks_data, page_size=10000)
    walk_ids = [row[0] for row in cur.fetchall()]
    
    print(f"5. Генерация {len(walk_ids)} отчетов о прогулках...")
    reports_data = []
    for w_id in walk_ids:
        reports_data.append((w_id, fake.date_time_this_month(), fake.paragraph()))
    execute_values(cur, "INSERT INTO reports (walk_id, created_at, summary) VALUES %s", reports_data, page_size=10000)
    
    print(f"6. Генерация {len(completed_orders)} отзывов...")
    reviews_data = []
    for order in completed_orders:
        o_id, o_owner_id, o_status, o_start, o_end, o_cost = order
        reviews_data.append((o_owner_id, o_id, random.randint(1, 5), fake.text(), o_end + timedelta(hours=1)))
    execute_values(cur, "INSERT INTO reviews (user_id, order_id, rating, comment, created_at) VALUES %s", reviews_data, page_size=10000)
    
    print("Включение триггера trg_generate_report...")
    cur.execute("ALTER TABLE walks ENABLE TRIGGER trg_generate_report;")
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"\nГенерация успешно завершена! В каждой mutable таблице сгенерировано ровно по {NUM_ORDERS} (или {NUM_USERS}/{NUM_DOGS}) записей истории.")

if __name__ == '__main__':
    generate_data()