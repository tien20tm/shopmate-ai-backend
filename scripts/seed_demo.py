
import asyncio
import random

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select, func

from src.database import AsyncSessionLocal
from src.customers.models import Customer
from src.products.models import Product
from src.orders.models import Order, OrderItem


PRODUCT_TYPES = [
    "Bàn phím cơ",
    "Chuột không dây",
    "Tai nghe Bluetooth",
    "Webcam",
    "USB-C Hub",
    "Màn hình",
]

STATUSES = [
    "pending",
    "processing",
    "shipped",
    "delivered",
    "cancelled",
]

# customer index (0-based), status
FIXED_ORDERS = {
    1: (0, "pending"),
    2: (0, "shipped"),
    3: (0, "delivered"),
    4: (0, "delivered"),
    5: (0, "cancelled"),
    6: (1, "processing"),
}


async def seed():
    rng = random.Random(42)
    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as db:
        # Only seed an empty demo database.
        for model in (Customer, Product, Order):
            count = await db.scalar(
                select(func.count()).select_from(model)
            )
            if count:
                print("Database is not empty. Skip seeding.")
                return

        customers = [
            Customer(
                full_name=f"Khách hàng {i:02d}",
                email=f"customer{i}@example.com",
            )
            for i in range(1, 21)
        ]

        products = [
            Product(
                sku=f"SKU-{i:03d}",
                name=f"{PRODUCT_TYPES[(i - 1) % 6]} {i:02d}",
                price=Decimal(300000 + i * 15000),
            )
            for i in range(1, 31)
        ]

        db.add_all(customers + products)
        await db.flush()

        orders = []

        for i in range(1, 101):
            customer_index, status = FIXED_ORDERS.get(
                i,
                (
                    rng.randrange(len(customers)),
                    rng.choice(STATUSES),
                ),
            )

            days_old = 5 if i == 3 else 20 if i == 4 else 7

            delivered_at = None
            if status == "delivered":
                delivered_at = now - timedelta(
                    days=3 if i == 3 else 15 if i == 4 else 1
                )

            order = Order(
                id=f"ORD-{i:04d}",
                customer_id=customers[customer_index].id,
                status=status,
                created_at=now - timedelta(days=days_old),
                delivered_at=delivered_at,
            )

            selected_products = rng.sample(
                products,
                k=rng.randint(1, 3),
            )

            for product in selected_products:
                order.items.append(
                    OrderItem(
                        product_id=product.id,
                        quantity=rng.randint(1, 2),
                        unit_price=product.price,
                    )
                )

            orders.append(order)

        db.add_all(orders)
        await db.commit()

        print("Created 20 customers")
        print("Created 30 products")
        print("Created 100 orders")


if __name__ == "__main__":
    asyncio.run(seed())
