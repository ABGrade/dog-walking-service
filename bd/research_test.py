import os
import time
import csv
import matplotlib
matplotlib.use('Agg') # Для сохранения картинок без UI
import matplotlib.pyplot as plt

# Импортируем ваши модули
import database
import fill_data

# --- НАСТРОЙКИ ДЛЯ ТЕСТИРОВАНИЯ ---
# Симметричные шаги: по 7 точек
SIZES_SMALL = [100, 500, 1000, 2500, 5000, 7500, 10000]
ITERATIONS_SMALL = 75 

SIZES_BIG = [10000, 50000, 100000, 250000, 500000, 750000, 1000000]
ITERATIONS_BIG = 15 

def execute_sql(query):
    """Выполняет DDL SQL-запросы"""
    conn = database.get_connection()
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(query)
    cur.close()
    conn.close()

def drop_all_indexes():
    execute_sql("DROP INDEX IF EXISTS idx_orders_status_walker_btree;")
    execute_sql("DROP INDEX IF EXISTS idx_dogs_owner_btree;")
    execute_sql("DROP INDEX IF EXISTS idx_orders_walker_btree;")
    execute_sql("DROP INDEX IF EXISTS idx_orders_status_hash;")
    execute_sql("DROP INDEX IF EXISTS idx_dogs_owner_hash;")
    execute_sql("DROP INDEX IF EXISTS idx_orders_walker_hash;")

def create_btree_indexes():
    execute_sql("CREATE INDEX idx_orders_status_walker_btree ON orders USING btree(status_id, walker_id);")
    execute_sql("CREATE INDEX idx_dogs_owner_btree ON dogs USING btree(owner_id);")
    execute_sql("CREATE INDEX idx_orders_walker_btree ON orders USING btree(walker_id);")

def create_hash_indexes():
    execute_sql("CREATE INDEX idx_orders_status_hash ON orders USING hash(status_id);")
    execute_sql("CREATE INDEX idx_dogs_owner_hash ON dogs USING hash(owner_id);")
    execute_sql("CREATE INDEX idx_orders_walker_hash ON orders USING hash(walker_id);")

def measure_time(func, *args, iterations=10, **kwargs):
    """Выполняет функцию N раз и возвращает среднее время в мс. Поддерживает kwargs!"""
    start_time = time.perf_counter()
    for _ in range(iterations):
        func(*args, **kwargs)
    end_time = time.perf_counter()
    return ((end_time - start_time) / iterations) * 1000

def get_random_owner_with_dogs():
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT owner_id FROM dogs LIMIT 1;")
    res = cur.fetchone()
    cur.close()
    conn.close()
    return res['owner_id'] if res else 1

def init_csv(filename, headers):
    """Создает файл и записывает заголовки"""
    with open(filename, mode='w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['Количество записей (шт.)'] + headers)

def append_to_csv(filename, row_data):
    """Дописывает одну строку с результатами в конец файла"""
    with open(filename, mode='a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=';')
        # Округляем числа с плавающей точкой до 3 знаков
        formatted_row = [round(x, 3) if isinstance(x, float) else x for x in row_data]
        writer.writerow(formatted_row)

def plot_and_save(sizes, times_no_idx, times_btree, times_hash, title, filename):
    plt.figure(figsize=(10, 6))
    plt.plot(sizes, times_no_idx, marker='o', linestyle='-', color='#D32F2F', linewidth=2, label='Без индексов (Seq Scan)')
    plt.plot(sizes, times_btree, marker='s', linestyle='--', color='#1976D2', linewidth=2, label='B-Tree индексы')
    plt.plot(sizes, times_hash, marker='^', linestyle='-.', color='#388E3C', linewidth=2, label='Hash индексы')
    plt.title(title, fontsize=13, pad=15, fontweight='bold')
    plt.xlabel('Количество записей в таблице', fontsize=11)
    plt.ylabel('Среднее время выполнения, мс', fontsize=11)
    plt.ticklabel_format(style='plain', axis='x')
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.close()
    print(f"[PLOT] График обновлен: {filename}")

def run_test_suite(sizes, iterations, prefix):
    # Имена файлов
    f_orders = f'results/{prefix}_query1_orders.csv'
    f_dogs = f'results/{prefix}_query2_dogs.csv'
    f_walkers = f'results/{prefix}_query3_walkers.csv'

    # Инициализируем CSV файлы
    headers = ['Без индексов (мс)', 'B-Tree (мс)', 'Hash (мс)']
    init_csv(f_orders, headers)
    init_csv(f_dogs, headers)
    init_csv(f_walkers, headers)

    # Словари для накопления данных ради графиков
    res_no = {1: [], 2: [], 3: []}
    res_bt = {1: [], 2: [], 3: []}
    res_hash = {1: [], 2: [], 3: []}
    
    # Чтобы график не падал, если скрипт прервется, собираем пройденные sizes
    completed_sizes = []

    for size in sizes:
        print(f"\n--- [ {prefix.upper()} ] Тестирование индексов: {size} записей ---")
        fill_data.NUM_ORDERS = size
        fill_data.NUM_USERS = max(10, size // 5) 
        
        print("[WAIT] Заполнение базы данных...")
        fill_data.generate_data()
        owner_id = get_random_owner_with_dogs()
        
        database.invalidate_orders_cache()
        
        # --- ТЕСТ 1: БЕЗ ИНДЕКСОВ ---
        print("[TIME] Замер: БЕЗ ИНДЕКСОВ...")
        drop_all_indexes()
        t1_no = measure_time(database.get_available_orders, search_query="NO_CACHE", iterations=iterations)
        t2_no = measure_time(database.get_user_dogs, owner_id, iterations=iterations)
        t3_no = measure_time(database.get_walkers, iterations=iterations)
        
        res_no[1].append(t1_no); res_no[2].append(t2_no); res_no[3].append(t3_no)
        
        # --- ТЕСТ 2: B-TREE ---
        print("[TIME] Замер: B-TREE...")
        create_btree_indexes()
        t1_bt = measure_time(database.get_available_orders, search_query="NO_CACHE", iterations=iterations)
        t2_bt = measure_time(database.get_user_dogs, owner_id, iterations=iterations)
        t3_bt = measure_time(database.get_walkers, iterations=iterations)
        
        res_bt[1].append(t1_bt); res_bt[2].append(t2_bt); res_bt[3].append(t3_bt)
        
        # --- ТЕСТ 3: HASH ---
        print("[TIME] Замер: HASH...")
        drop_all_indexes() 
        create_hash_indexes()
        t1_hash = measure_time(database.get_available_orders, search_query="NO_CACHE", iterations=iterations)
        t2_hash = measure_time(database.get_user_dogs, owner_id, iterations=iterations)
        t3_hash = measure_time(database.get_walkers, iterations=iterations)
        
        res_hash[1].append(t1_hash); res_hash[2].append(t2_hash); res_hash[3].append(t3_hash)

        # ДОЗАПИСЬ В ФАЙЛЫ В РЕАЛЬНОМ ВРЕМЕНИ
        append_to_csv(f_orders, [size, t1_no, t1_bt, t1_hash])
        append_to_csv(f_dogs, [size, t2_no, t2_bt, t2_hash])
        append_to_csv(f_walkers, [size, t3_no, t3_bt, t3_hash])
        print("[SAVE] Данные сохранены в CSV.")

        completed_sizes.append(size)

        # Перестраиваем графики на каждом шаге (если упадет - график до текущей точки останется)
        plot_and_save(completed_sizes, res_no[1], res_bt[1], res_hash[1],
                      f'Запрос 1: Получение доступных заказов (Биржа)', 
                      f'results/{prefix}_query1_orders.png')
        plot_and_save(completed_sizes, res_no[2], res_bt[2], res_hash[2],
                      f'Запрос 2: Список собак владельца', 
                      f'results/{prefix}_query2_dogs.png')
        plot_and_save(completed_sizes, res_no[3], res_bt[3], res_hash[3],
                      f'Запрос 3: Рейтинг выгульщиков (Агрегация)', 
                      f'results/{prefix}_query3_walkers.png')

def run_redis_test_suite(sizes, iterations, prefix):
    print(f"\n[START] [ {prefix.upper()} ] Запуск тестирования кэширования (Redis vs PostgreSQL)...")
    
    f_redis = f'results/{prefix}_redis_vs_pg.csv'
    init_csv(f_redis, ['PostgreSQL (мс)', 'PostgreSQL + Redis (мс)', 'Потребление ОЗУ Redis (МБ)'])

    results_pg = []
    results_redis = []
    completed_sizes = []

    for size in sizes:
        print(f"\n--- Тестирование кэша: {size} записей ---")
        fill_data.NUM_ORDERS = size
        fill_data.NUM_USERS = max(10, size // 5) 
        fill_data.generate_data()

        drop_all_indexes()
        
        # 1. Замер чистого Postgres
        print("[TIME] Замер времени PostgreSQL (Без кэша)...")
        def fetch_pg():
            database.invalidate_orders_cache()
            database.get_available_orders()
            
        t_pg = measure_time(fetch_pg, iterations=iterations)
        results_pg.append(t_pg)
    
        # 2. Замер Redis
        print("[TIME] Замер времени PostgreSQL + Redis...")
        database.invalidate_orders_cache()
        
        try:
            mem_before = database.redis_client.info('memory')['used_memory']
        except:
            mem_before = 0
            
        database.get_available_orders() # Прогрев
        
        try:
            mem_after = database.redis_client.info('memory')['used_memory']
            mem_diff = max(0, (mem_after - mem_before) / (1024 * 1024))
        except:
            mem_diff = 0

        def fetch_redis():
            database.get_available_orders()
            
        t_redis = measure_time(fetch_redis, iterations=iterations)
        results_redis.append(t_redis)
        
        print(f"Результат: Postgres = {t_pg:.2f} мс | Redis = {t_redis:.2f} мс | Память = {mem_diff:.3f} МБ")

        # ДОЗАПИСЬ
        append_to_csv(f_redis, [size, t_pg, t_redis, mem_diff])
        completed_sizes.append(size)

        # Отрисовка графика
        plt.figure(figsize=(10, 6))
        plt.plot(completed_sizes, results_pg, marker='o', linestyle='-', color='#D32F2F', linewidth=2, label='PostgreSQL (Без кэша)')
        plt.plot(completed_sizes, results_redis, marker='s', linestyle='-', color='#1976D2', linewidth=2, label='Redis (Из кэша)')
        plt.title('Эффективность кэширования: Redis vs PostgreSQL', fontsize=13, pad=15, fontweight='bold')
        plt.xlabel('Количество записей в таблице', fontsize=11)
        plt.ylabel('Среднее время выполнения, мс', fontsize=11)
        plt.ticklabel_format(style='plain', axis='x')
        plt.grid(True, linestyle=':', alpha=0.7)
        plt.legend(fontsize=11)
        plt.tight_layout()
        plt.savefig(f'results/{prefix}_redis_vs_pg.png', dpi=300)
        plt.close()
        print(f"[PLOT] График обновлен: results/{prefix}_redis_vs_pg.png")

def main():
    print("[START] Старт полного исследовательского тестирования БД...")
    os.makedirs('results', exist_ok=True)
    
    run_test_suite(SIZES_SMALL, ITERATIONS_SMALL, "small")
    run_test_suite(SIZES_BIG, ITERATIONS_BIG, "big")
    run_redis_test_suite(SIZES_BIG, ITERATIONS_BIG, "cache_test")
    
    print("\n[SUCCESS] Исследование полностью завершено!")

if __name__ == "__main__":
    main()