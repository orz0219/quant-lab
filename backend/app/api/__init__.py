from fastapi import APIRouter

from app.api.v1 import stocks, backtest, strategy, user_strategies, settings, sectors, roadmap

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
api_router.include_router(backtest.router, prefix="/backtest", tags=["backtest"])
api_router.include_router(strategy.router, prefix="/strategy", tags=["strategy"])
api_router.include_router(user_strategies.router, prefix="/strategies", tags=["user_strategies"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(sectors.router, prefix="/sectors", tags=["sectors"])
api_router.include_router(roadmap.router, prefix="/roadmap", tags=["roadmap"])
