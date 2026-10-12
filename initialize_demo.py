"""Create the schema and a small demo dataset in an empty database."""
from pathlib import Path
import hashlib
import psycopg2
from settings import DB_CONFIG

ROOT = Path(__file__).resolve().parent

def main():
    with psycopg2.connect(**DB_CONFIG) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")
            if cursor.fetchone()[0]:
                raise SystemExit('Database already has tables; initialization stopped without changing them.')
            cursor.execute((ROOT/'bd/tables.sql').read_text(encoding='utf-8-sig'))
            cursor.execute((ROOT/'bd/functions.sql').read_text(encoding='utf-8-sig'))
            cursor.execute("INSERT INTO roles(id,name) VALUES(1,'владелец'),(2,'выгульщик'),(3,'администратор')")
            cursor.execute("INSERT INTO order_statuses(id,name) VALUES(1,'создан'),(2,'принят'),(3,'завершен'),(4,'отменен')")
            cursor.execute("INSERT INTO dog_breeds(id,name) VALUES(1,'Лабрадор'),(2,'Овчарка'),(3,'Метис')")
            for first, email, role in [('Демо владелец','owner@example.test',1),('Демо выгульщик','walker@example.test',2)]:
                cursor.execute('INSERT INTO users(first_name,last_name,email,phone,password_hash) VALUES(%s,%s,%s,%s,%s) RETURNING id',
                    (first,'',email,'+70000000000',hashlib.sha256(b'dog_demo').hexdigest()))
                user_id=cursor.fetchone()[0]
                cursor.execute('INSERT INTO user_roles(user_id,role_id) VALUES(%s,%s)',(user_id,role))
                if role == 1:
                    cursor.execute("INSERT INTO dogs(owner_id,breed_id,name,sex,birth_date) VALUES(%s,1,'Шарик','М','2020-01-01')",(user_id,))
            for table in ['roles','order_statuses','dog_breeds']:
                cursor.execute(f"SELECT setval(pg_get_serial_sequence('{table}','id'),(SELECT max(id) FROM {table}))")
    print('Demo initialized. Accounts: owner@example.test and walker@example.test; password: dog_demo')

if __name__ == '__main__':
    main()
