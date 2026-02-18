from fastapi import APIRouter
from app.api.v1.endpoints import auth, categories, transactions, analytics

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(categories.router, prefix="/categories", tags=["Categories"])
router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])