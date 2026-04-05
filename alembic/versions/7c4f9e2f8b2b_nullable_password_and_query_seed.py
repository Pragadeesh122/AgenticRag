"""Allow nullable OAuth passwords and seed query database tables

Revision ID: 7c4f9e2f8b2b
Revises: 1f33eaf80923
Create Date: 2026-04-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7c4f9e2f8b2b"
down_revision: Union[str, Sequence[str], None] = "1f33eaf80923"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("user", "hashed_password", existing_type=sa.String(length=1024), nullable=True)

    op.execute(
        sa.text(
            """
            UPDATE "user" u
            SET hashed_password = NULL
            WHERE EXISTS (
                SELECT 1
                FROM oauth_account oa
                WHERE oa.user_id = u.id
            )
            """
        )
    )

    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("country", sa.String(length=50), nullable=False, server_default="US"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id"), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("total", sa.Numeric(10, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("status IN ('pending', 'shipped', 'delivered', 'cancelled')"),
    )

    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
    )

    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("rating BETWEEN 1 AND 5"),
    )

    op.execute(
        """
        INSERT INTO categories (name, description) VALUES
            ('Electronics', 'Phones, laptops, gadgets'),
            ('Clothing', 'Apparel and accessories'),
            ('Home & Kitchen', 'Furniture, appliances, decor'),
            ('Books', 'Fiction, non-fiction, textbooks');
        """
    )

    op.execute(
        """
        INSERT INTO customers (name, email, city, country) VALUES
            ('Alice Chen', 'alice@example.com', 'Austin', 'US'),
            ('Bob Smith', 'bob@example.com', 'London', 'UK'),
            ('Carlos Ruiz', 'carlos@example.com', 'Madrid', 'ES'),
            ('Diana Kumar', 'diana@example.com', 'Bangalore', 'IN'),
            ('Eve Johnson', 'eve@example.com', 'Toronto', 'CA'),
            ('Frank Meyer', 'frank@example.com', 'Berlin', 'DE'),
            ('Grace Lee', 'grace@example.com', 'Seoul', 'KR'),
            ('Hassan Ali', 'hassan@example.com', 'Dubai', 'AE');
        """
    )

    op.execute(
        """
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
        """
    )

    op.execute(
        """
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
        """
    )

    op.execute(
        """
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
        """
    )

    op.execute(
        """
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
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'llm_reader') THEN
                GRANT USAGE ON SCHEMA public TO llm_reader;
                GRANT SELECT ON customers, categories, products, orders, order_items, reviews TO llm_reader;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.drop_table("reviews")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("products")
    op.drop_table("categories")
    op.drop_table("customers")

    op.execute(
        sa.text(
            """
            UPDATE "user"
            SET hashed_password = ''
            WHERE hashed_password IS NULL
            """
        )
    )
    op.alter_column("user", "hashed_password", existing_type=sa.String(length=1024), nullable=False)
