from orders.router import order_router
from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db, engine


app = FastAPI()
app.include_router(order_router)

@app.get("/health/db")
async def database_health(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(text("SELECT 1"))
    return {
        "status": "healthy",
        "database": "postgresql",
        "result": result.scalar(),
    }

@app.on_event("shutdown")
async def shutdown():
    await engine.dispose()