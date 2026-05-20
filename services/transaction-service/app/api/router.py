from fastapi import APIRouter

from app.api.routes import (
    attachments,
    categories,
    health,
    hello,
    payment_methods,
    recurring_transactions,
    tags,
    transactions,
    wallets,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(hello.router)
api_router.include_router(wallets.router)
api_router.include_router(categories.router)
api_router.include_router(payment_methods.router)
api_router.include_router(transactions.router)
api_router.include_router(recurring_transactions.router)
api_router.include_router(attachments.router)
api_router.include_router(tags.router)
