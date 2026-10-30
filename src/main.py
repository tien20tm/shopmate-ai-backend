from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import get_db, engine
from src.orders.router import order_router

from src.orders.router import order_router
from src.products.router import router as products_router
from src.chat.router import router as chat_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title="ShopMate AI Backend",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(chat_router)

app.include_router(order_router)
app.include_router(order_router)
app.include_router(products_router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
