"""Generate random seed data for the e-commerce database using Faker."""

import os
import random
import psycopg2
from faker import Faker
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_ADMIN_USER"),
    "password": os.getenv("DB_ADMIN_PASSWORD"),
}

# Multi-locale faker for diverse names/addresses
fake = Faker(["en_US", "en_GB", "de_DE", "fr_FR", "ja_JP", "ko_KR", "hi_IN", "es_ES", "pt_BR", "ar_AE"])

PRODUCT_TEMPLATES = {
    1: [  # Electronics
        "Wireless Earbuds {}", "Smart Watch {}", "Bluetooth Speaker {}",
        "Tablet {} inch", "Mechanical Keyboard {}", "USB-C Hub {}",
        "Portable Charger {}mAh", "Monitor {} inch", "Webcam {}",
        "Gaming Mouse {}", "Noise Cancelling Headphones {}",
    ],
    2: [  # Clothing
        "Hoodie {}", "Sneakers {}", "Polo Shirt {}", "Chino Pants {}",
        "Winter Jacket {}", "Wool Scarf {}", "Canvas Belt {}",
        "Denim Shorts {}", "Linen Shirt {}", "Running Tights {}",
    ],
    3: [  # Home & Kitchen
        "Air Fryer {}", "Coffee Maker {}", "Knife Set {}", "Blender {}",
        "Toaster Oven {}", "Cutting Board {}", "Water Bottle {}",
        "Dutch Oven {}", "Espresso Machine {}", "Rice Cooker {}",
    ],
    4: [  # Books
        "Learn {} in 30 Days", "The Art of {}", "Mastering {}",
        "Introduction to {}", "{} Cookbook", "Deep Dive into {}",
    ],
}

PRICE_RANGES = {1: (19.99, 999.99), 2: (9.99, 249.99), 3: (9.99, 299.99), 4: (9.99, 59.99)}

PRODUCT_VARIANTS = [
    "Pro", "Max", "Ultra", "Lite", "SE", "Plus", "Air", "Mini",
    "V2", "V3", "Elite", "Classic", "Sport", "Studio", "X", "S",
]

BOOK_TOPICS = [
    "Python", "Rust", "Go", "Kubernetes", "Machine Learning",
    "System Design", "Data Engineering", "Algorithms", "TypeScript",
    "Docker", "GraphQL", "Microservices", "DevOps", "Security",
]

STATUSES = ["pending", "shipped", "delivered", "cancelled"]
STATUS_WEIGHTS = [0.15, 0.2, 0.55, 0.1]


def seed(n_customers=50, n_products=40, n_orders=200, n_reviews=100):
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            # --- Customers ---
            emails_used = set()
            # Fetch existing emails to avoid conflicts
            cur.execute("SELECT email FROM customers")
            emails_used.update(row[0] for row in cur.fetchall())

            customer_ids = []
            for _ in range(n_customers):
                name = fake.name()
                email = fake.unique.email()
                while email in emails_used:
                    email = fake.unique.email()
                emails_used.add(email)
                city = fake.city()
                country = fake.country_code()
                days_ago = random.randint(1, 365)
                cur.execute(
                    """INSERT INTO customers (name, email, city, country, created_at)
                       VALUES (%s, %s, %s, %s, NOW() - INTERVAL '%s days')
                       RETURNING id""",
                    (name, email, city, country, days_ago),
                )
                customer_ids.append(cur.fetchone()[0])

            print(f"Inserted {len(customer_ids)} customers")

            # --- Products ---
            cur.execute("SELECT id FROM categories")
            category_ids = [row[0] for row in cur.fetchall()]

            product_ids = []
            for _ in range(n_products):
                cat_id = random.choice(category_ids)
                templates = PRODUCT_TEMPLATES.get(cat_id, PRODUCT_TEMPLATES[1])
                template = random.choice(templates)
                variant = random.choice(BOOK_TOPICS if cat_id == 4 else PRODUCT_VARIANTS)
                name = template.format(variant)
                min_p, max_p = PRICE_RANGES[cat_id]
                price = round(random.uniform(min_p, max_p), 2)
                stock = random.randint(0, 300)
                days_ago = random.randint(1, 180)
                cur.execute(
                    """INSERT INTO products (name, category_id, price, stock, created_at)
                       VALUES (%s, %s, %s, %s, NOW() - INTERVAL '%s days')
                       RETURNING id""",
                    (name, cat_id, price, stock, days_ago),
                )
                product_ids.append(cur.fetchone()[0])

            print(f"Inserted {len(product_ids)} products")

            # --- Orders + Order Items ---
            order_count = 0
            item_count = 0
            for _ in range(n_orders):
                customer_id = random.choice(customer_ids)
                status = random.choices(STATUSES, STATUS_WEIGHTS)[0]
                days_ago = random.randint(1, 180)
                num_items = random.randint(1, 5)
                items = []
                for _ in range(num_items):
                    product_id = random.choice(product_ids)
                    quantity = random.randint(1, 3)
                    cur.execute(
                        "SELECT price FROM products WHERE id = %s", (product_id,)
                    )
                    unit_price = cur.fetchone()[0]
                    items.append((product_id, quantity, float(unit_price)))

                total = round(sum(q * p for _, q, p in items), 2)
                cur.execute(
                    """INSERT INTO orders (customer_id, status, total, created_at)
                       VALUES (%s, %s, %s, NOW() - INTERVAL '%s days')
                       RETURNING id""",
                    (customer_id, status, total, days_ago),
                )
                order_id = cur.fetchone()[0]
                order_count += 1

                for product_id, quantity, unit_price in items:
                    cur.execute(
                        """INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                           VALUES (%s, %s, %s, %s)""",
                        (order_id, product_id, quantity, unit_price),
                    )
                    item_count += 1

            print(f"Inserted {order_count} orders with {item_count} items")

            # --- Reviews ---
            review_count = 0
            reviewed = set()
            for _ in range(n_reviews):
                product_id = random.choice(product_ids)
                customer_id = random.choice(customer_ids)
                if (product_id, customer_id) in reviewed:
                    continue
                reviewed.add((product_id, customer_id))
                rating = random.choices([1, 2, 3, 4, 5], [0.05, 0.1, 0.2, 0.35, 0.3])[0]
                comment = fake.sentence(nb_words=random.randint(6, 20))
                days_ago = random.randint(1, 120)
                cur.execute(
                    """INSERT INTO reviews (product_id, customer_id, rating, comment, created_at)
                       VALUES (%s, %s, %s, %s, NOW() - INTERVAL '%s days')""",
                    (product_id, customer_id, rating, comment, days_ago),
                )
                review_count += 1

            print(f"Inserted {review_count} reviews")

        conn.commit()
        print("\nSeeding complete!")

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed the e-commerce database")
    parser.add_argument("--customers", type=int, default=50)
    parser.add_argument("--products", type=int, default=40)
    parser.add_argument("--orders", type=int, default=200)
    parser.add_argument("--reviews", type=int, default=100)
    args = parser.parse_args()
    seed(args.customers, args.products, args.orders, args.reviews)
