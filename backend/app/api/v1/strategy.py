"""AI 辅助策略生成接口。"""
from fastapi import APIRouter, HTTPException

from app.services.strategy_service import StrategyService
from app.schemas.backtest import StrategyGenerateRequest, StrategyGenerateResponse

router = APIRouter()
_service = StrategyService()


@router.post("/generate", response_model=StrategyGenerateResponse)
def generate_strategy(request: StrategyGenerateRequest):
    if not request.description or len(request.description) < 5:
        raise HTTPException(status_code=400, detail="请提供更详细的策略描述")
    return _service.generate(request)
