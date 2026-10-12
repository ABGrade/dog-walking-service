CREATE ROLE db_owner_role NOLOGIN;
CREATE ROLE db_walker_role NOLOGIN;
CREATE ROLE db_admin_role NOLOGIN;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO db_admin_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO db_admin_role;

GRANT SELECT ON dog_breeds, order_statuses TO db_owner_role;

GRANT SELECT, INSERT, UPDATE, DELETE ON dogs TO db_owner_role;

GRANT SELECT, INSERT, UPDATE ON orders, order_dogs, payments, reviews TO db_owner_role;
GRANT SELECT ON walks, reports TO db_owner_role;

GRANT USAGE, SELECT ON SEQUENCE dogs_id_seq, orders_id_seq, payments_id_seq, reviews_id_seq TO db_owner_role;

GRANT SELECT ON dog_breeds, order_statuses, dogs, orders, order_dogs TO db_walker_role;

GRANT UPDATE (status_id, walker_id) ON orders TO db_walker_role;

GRANT SELECT, INSERT, UPDATE ON walks, reports TO db_walker_role;

GRANT USAGE, SELECT ON SEQUENCE walks_id_seq, reports_id_seq TO db_walker_role;