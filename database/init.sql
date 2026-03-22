-- ============================================================
-- Schema: E-commerce store with customers, products, orders
-- ============================================================

-- Customers
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    city VARCHAR(100),
    country VARCHAR(50) DEFAULT 'US',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Product categories
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

-- Products
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    category_id INT REFERENCES categories(id),
    price NUMERIC(10, 2) NOT NULL,
    stock INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Orders
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(id),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'shipped', 'delivered', 'cancelled')),
    total NUMERIC(10, 2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Order items (many-to-many: orders <-> products)
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id) ON DELETE CASCADE,
    product_id INT REFERENCES products(id),
    quantity INT NOT NULL DEFAULT 1,
    unit_price NUMERIC(10, 2) NOT NULL
);

-- Product reviews
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(id),
    customer_id INT REFERENCES customers(id),
    rating INT CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- Seed data
-- ============================================================

INSERT INTO categories (name, description) VALUES
    ('Electronics', 'Phones, laptops, gadgets'),
    ('Clothing', 'Apparel and accessories'),
    ('Home & Kitchen', 'Furniture, appliances, decor'),
    ('Books', 'Fiction, non-fiction, textbooks');

INSERT INTO customers (name, email, city, country) VALUES
    ('Alice Chen', 'alice@example.com', 'Austin', 'US'),
    ('Bob Smith', 'bob@example.com', 'London', 'UK'),
    ('Carlos Ruiz', 'carlos@example.com', 'Madrid', 'ES'),
    ('Diana Kumar', 'diana@example.com', 'Bangalore', 'IN'),
    ('Eve Johnson', 'eve@example.com', 'Toronto', 'CA'),
    ('Frank Meyer', 'frank@example.com', 'Berlin', 'DE'),
    ('Grace Lee', 'grace@example.com', 'Seoul', 'KR'),
    ('Hassan Ali', 'hassan@example.com', 'Dubai', 'AE');

INSERT INTO products (name, category_id, price, stock) VALUES
    ('iPhone 16 Pro', 1, 999.99, 50),
    ('MacBook Air M4', 1, 1299.00, 30),
    ('Sony WH-1000XM6', 1, 349.99, 100),
    ('Cotton T-Shirt', 2, 24.99, 200),
    ('Denim Jacket', 2, 89.99, 75),
    ('Running Shoes', 2, 129.99, 120),
    ('Instant Pot Pro', 3, 119.99, 60),
    ('Cast Iron Skillet', 3, 44.99, 80),
    ('Desk Lamp LED', 3, 39.99, 150),
    ('The Pragmatic Programmer', 4, 49.99, 40),
    ('Designing Data-Intensive Apps', 4, 44.99, 35),
    ('Clean Code', 4, 39.99, 55);

-- Orders with varied statuses and dates
INSERT INTO orders (customer_id, status, total, created_at) VALUES
    (1, 'delivered', 1049.98, NOW() - INTERVAL '45 days'),
    (1, 'shipped', 24.99, NOW() - INTERVAL '5 days'),
    (2, 'delivered', 1299.00, NOW() - INTERVAL '30 days'),
    (2, 'cancelled', 349.99, NOW() - INTERVAL '20 days'),
    (3, 'delivered', 164.98, NOW() - INTERVAL '60 days'),
    (3, 'pending', 89.99, NOW() - INTERVAL '1 day'),
    (4, 'shipped', 209.98, NOW() - INTERVAL '3 days'),
    (4, 'delivered', 44.99, NOW() - INTERVAL '90 days'),
    (5, 'delivered', 1349.98, NOW() - INTERVAL '15 days'),
    (5, 'pending', 39.99, NOW() - INTERVAL '2 days'),
    (6, 'delivered', 119.99, NOW() - INTERVAL '25 days'),
    (7, 'shipped', 94.98, NOW() - INTERVAL '4 days'),
    (7, 'delivered', 259.98, NOW() - INTERVAL '35 days'),
    (8, 'delivered', 89.98, NOW() - INTERVAL '50 days');

-- Order items matching order totals
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
    (1, 1, 1, 999.99), (1, 4, 2, 24.99),
    (2, 4, 1, 24.99),
    (3, 2, 1, 1299.00),
    (4, 3, 1, 349.99),
    (5, 5, 1, 89.99), (5, 4, 3, 24.99),
    (6, 5, 1, 89.99),
    (7, 6, 1, 129.99), (7, 8, 1, 44.99), (7, 4, 1, 24.99),
    (8, 8, 1, 44.99),
    (9, 2, 1, 1299.00), (9, 4, 2, 24.99),
    (10, 9, 1, 39.99),
    (11, 7, 1, 119.99),
    (12, 10, 1, 49.99), (12, 11, 1, 44.99),
    (13, 3, 1, 349.99), (13, 6, 1, 129.99),
    (14, 10, 1, 49.99), (14, 9, 1, 39.99);

-- Reviews
INSERT INTO reviews (product_id, customer_id, rating, comment, created_at) VALUES
    (1, 1, 5, 'Best phone I have ever used. Camera is incredible.', NOW() - INTERVAL '40 days'),
    (2, 3, 4, 'Great laptop, wish it had more ports though.', NOW() - INTERVAL '55 days'),
    (3, 2, 3, 'Good noise cancellation but uncomfortable after 2 hours.', NOW() - INTERVAL '18 days'),
    (1, 5, 4, 'Solid upgrade from the 15 Pro.', NOW() - INTERVAL '10 days'),
    (7, 6, 5, 'Makes cooking so much easier. Use it daily.', NOW() - INTERVAL '20 days'),
    (10, 7, 5, 'Every developer should read this book.', NOW() - INTERVAL '30 days'),
    (11, 7, 4, 'Dense but incredibly valuable for system design.', NOW() - INTERVAL '28 days'),
    (4, 4, 3, 'Decent quality for the price. Runs a bit small.', NOW() - INTERVAL '85 days'),
    (5, 1, 4, 'Great jacket, looks even better in person.', NOW() - INTERVAL '35 days'),
    (6, 4, 5, 'Super comfortable for long runs.', NOW() - INTERVAL '2 days'),
    (8, 8, 4, 'Heavy and solid. Seasoning was easy.', NOW() - INTERVAL '45 days'),
    (12, 3, 5, 'A must read. Changed how I write code.', NOW() - INTERVAL '50 days');

-- Read-only user is created by setup-reader.sh (password from env)
