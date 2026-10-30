
# scripts/seed_demo.py
import asyncio
import random

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import select

from src.database import async_session_maker
from src.customers.models import Customer
from src.products.models import Product
from src.orders.models import Order, OrderItem

rng = random.Random(42)

CATEGORIES = [
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

# Các đơn hàng cố định cho Agent evaluation
FIXED_ORDERS = {
    1: (1, "pending"),
    2: (1, "shipped"),
    3: (1, "delivered"),
    4: (1, "delivered"),
    5: (1, "cancelled"),
    6: (2, "processing"),
}


async def seed():
    now = datetime.now(timezone.utc)

    async with async_session_maker() as db:
        existing = await db.scalar(
            select(Order.id).limit(1)
        )
        if existing:
            print("Orders already seeded. Skipping.")
            return

        customers = [
            Customer(
                id=i,
                full_name=f"Khách hàng {i:02d}",
                email=f"customer{i}@example.com",
            )
            for i in range(1, 21)
        ]

        products = [
            Product(
                id=i,
                sku=f"SKU-{i:03d}",
                name=f"{CATEGORIES[(i-1) % 6]} ShopMate {i:02d}",
                price=Decimal(250000 + i * 20000),
            )
            for i in range(1, 31)
        ]

        db.add_all(customers + products)
        await db.flush()

        for i in range(1, 101):
            customer_id, status = FIXED_ORDERS.get(
                i,
                (
                    rng.randint(1, 20),
                    rng.choice(STATUSES),
                ),
            )

            days_old = {
                "pending": 1,
                "processing": 2,
                "shipped": 4,
                "delivered": 21,
                "cancelled": 7,
            }[status]

            if i == 3:
                days_old = 5
            elif i == 4:
                days_old = 20

            created_at = now - timedelta(days=days_old)

            delivered_at = (
                created_at + timedelta(days=2)
                if status == "delivered"
                else None
            )

            order_id = f"ORD-{i:04d}"

            db.add(Order(
                id=order_id,
                customer_id=customer_id,
                status=status,
                created_at=created_at,
                delivered_at=delivered_at,
            ))

            for product_id in rng.sample(
                range(1, 31),
                k=rng.randint(1, 3),
            ):
                quantity = rng.randint(1, 2)
                price = Decimal(
                    250000 + product_id * 20000
                )

                db.add(OrderItem(
                    order_id=order_id,
                    product_id=product_id,
                    quantity=quantity,
                    unit_price=price,
                ))

        await db.commit()
        print("Demo data seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
