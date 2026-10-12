CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description VARCHAR(255)
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    registered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE order_statuses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description VARCHAR(255)
);

CREATE TABLE dog_breeds (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- Таблицы с зависимостями (Связи)
CREATE TABLE user_roles (
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, user_id)
);

CREATE TABLE dogs (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    breed_id INTEGER NOT NULL REFERENCES dog_breeds(id),
    name VARCHAR(100) NOT NULL,
    sex VARCHAR(20) NOT NULL,
    birth_date DATE,
    behavior_notes TEXT,
    health_notes TEXT
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL REFERENCES users(id),
    walker_id INTEGER REFERENCES users(id),
    status_id INTEGER NOT NULL REFERENCES order_statuses(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    planned_start_at TIMESTAMP NOT NULL,
    planned_end_at TIMESTAMP NOT NULL,
    walk_address VARCHAR(255) NOT NULL,
    total_cost DECIMAL(10,2) NOT NULL,
    comment TEXT
);

CREATE TABLE order_dogs (
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    dog_id INTEGER NOT NULL REFERENCES dogs(id) ON DELETE CASCADE,
    PRIMARY KEY (order_id, dog_id)
);

CREATE TABLE walks (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL UNIQUE REFERENCES orders(id) ON DELETE CASCADE,
    actual_start_at TIMESTAMP NOT NULL,
    actual_end_at TIMESTAMP,
    status VARCHAR(50) NOT NULL
);

CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    walk_id INTEGER NOT NULL UNIQUE REFERENCES walks(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    summary TEXT NOT NULL
);

CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL UNIQUE REFERENCES orders(id) ON DELETE CASCADE,
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    payment_status VARCHAR(50) NOT NULL,
    paid_at TIMESTAMP
);

CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL,
    comment TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);