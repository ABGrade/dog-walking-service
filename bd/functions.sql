CREATE OR REPLACE FUNCTION create_order(
    p_owner_id INTEGER,
    p_planned_start_at TIMESTAMP,
    p_planned_end_at TIMESTAMP,
    p_walk_address VARCHAR,
    p_total_cost DECIMAL,
    p_dog_ids INTEGER[]
) RETURNS INTEGER AS $$
DECLARE
    v_order_id INTEGER;
    v_status_id INTEGER;
    v_dog_count INTEGER;
    v_valid_dogs INTEGER;
BEGIN
    IF p_planned_start_at IS NULL OR p_planned_end_at IS NULL OR p_planned_end_at <= p_planned_start_at THEN
        RAISE EXCEPTION 'Ошибка: конец прогулки должен быть позже начала';
    END IF;
    IF p_total_cost IS NULL OR p_total_cost < 0 THEN
        RAISE EXCEPTION 'Ошибка: стоимость не может быть отрицательной';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM users WHERE id = p_owner_id) THEN
        RAISE EXCEPTION 'Ошибка: владелец не найден';
    END IF;
    v_dog_count := array_length(p_dog_ids, 1);
    IF v_dog_count IS NULL OR v_dog_count = 0 THEN
        RAISE EXCEPTION 'Ошибка: список собак пуст';
    END IF;
    SELECT count(*) INTO v_valid_dogs
    FROM dogs
    WHERE id = ANY(p_dog_ids) AND owner_id = p_owner_id;

    IF v_valid_dogs != v_dog_count THEN
        RAISE EXCEPTION 'Ошибка: данные о собаках некорректны (чужая собака или не существует)';
    END IF;
    SELECT id INTO v_status_id FROM order_statuses WHERE name = 'создан';
    INSERT INTO orders (owner_id, status_id, planned_start_at, planned_end_at, walk_address, total_cost)
    VALUES (p_owner_id, v_status_id, p_planned_start_at, p_planned_end_at, p_walk_address, p_total_cost)
    RETURNING id INTO v_order_id;
    INSERT INTO order_dogs (order_id, dog_id)
    SELECT v_order_id, unnest(p_dog_ids);
    RETURN v_order_id;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION accept_order(
    p_order_id INTEGER,
    p_walker_id INTEGER
) RETURNS BOOLEAN AS $$
DECLARE
    v_current_status_id INTEGER;
    v_walker_assigned INTEGER;
    v_created_status_id INTEGER;
    v_accepted_status_id INTEGER;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM users WHERE id = p_walker_id) THEN
        RAISE EXCEPTION 'Ошибка: выгульщик не найден';
    END IF;
    SELECT status_id, walker_id INTO v_current_status_id, v_walker_assigned
    FROM orders WHERE id = p_order_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Ошибка: заказ не найден';
    END IF;
    SELECT id INTO v_created_status_id FROM order_statuses WHERE name = 'создан';
    SELECT id INTO v_accepted_status_id FROM order_statuses WHERE name = 'принят';
    IF v_current_status_id != v_created_status_id THEN
        RAISE EXCEPTION 'Ошибка: заказ нельзя принять (неверный статус)';
    END IF;
    IF v_walker_assigned IS NOT NULL THEN
        RAISE EXCEPTION 'Ошибка: заказ уже принят другим выгульщиком';
    END IF;
    UPDATE orders
    SET walker_id = p_walker_id, status_id = v_accepted_status_id
    WHERE id = p_order_id;
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION complete_walk(
    p_order_id INTEGER,
    p_actual_start_at TIMESTAMP,
    p_actual_end_at TIMESTAMP
) RETURNS INTEGER AS $$
DECLARE
    v_current_status_id INTEGER;
    v_accepted_status_id INTEGER;
    v_completed_status_id INTEGER;
    v_walk_id INTEGER;
BEGIN
    SELECT id INTO v_accepted_status_id FROM order_statuses WHERE name = 'принят';
    SELECT id INTO v_completed_status_id FROM order_statuses WHERE name = 'завершен';
    SELECT status_id INTO v_current_status_id
    FROM orders WHERE id = p_order_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Ошибка: заказ не найден';
    END IF;
    IF v_current_status_id != v_accepted_status_id THEN
        RAISE EXCEPTION 'Ошибка: заказ нельзя завершить (он не был принят)';
    END IF;
    SELECT id INTO v_walk_id FROM walks WHERE order_id = p_order_id;
    IF FOUND THEN
        UPDATE walks
        SET actual_start_at = p_actual_start_at,
            actual_end_at = p_actual_end_at,
            status = 'завершена'
        WHERE id = v_walk_id;
    ELSE
        INSERT INTO walks (order_id, actual_start_at, actual_end_at, status)
        VALUES (p_order_id, p_actual_start_at, p_actual_end_at, 'завершена')
        RETURNING id INTO v_walk_id;
    END IF;
    UPDATE orders
    SET status_id = v_completed_status_id
    WHERE id = p_order_id;
    RETURN v_walk_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION trigger_generate_report()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'завершена' AND (TG_OP = 'INSERT' OR OLD.status IS DISTINCT FROM 'завершена') THEN
        IF NOT EXISTS (SELECT 1 FROM reports WHERE walk_id = NEW.id) THEN
            INSERT INTO reports (walk_id, summary)
            VALUES (NEW.id, 'Автоматический отчет: Прогулка завершена. Выгульщик скоро добавит комментарии.');
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_generate_report
AFTER INSERT OR UPDATE ON walks
FOR EACH ROW
EXECUTE FUNCTION trigger_generate_report();
