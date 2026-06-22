"""Pydantic 模型：回测请求、结果、策略生成请求/响应。"""
from datetime import date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Metric(BaseModel):
    total_return: float = 0.0
    annual_return: float = 0.0
    max_drawdown: float = 0.0
    sharpe: float = 0.0
    win_rate: float = 0.0
    trades: int = 0


class Trade(BaseModel):
    open_date: date
    close_date: Optional[date] = None
    side: str = "long"
    open_price: float
    close_price: Optional[float] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None


class BacktestRequest(BaseModel):
    ts_code: str
    start_date: date
    end_date: date
    strategy_type: str = Field(
        default="ma_cross",
        description="策略类型: ma_cross / custom",
    )
    initial_cash: float = 100000.0
    params: Optional[Dict[str, Any]] = None


class BacktestResult(BaseModel):
    ts_code: str
    start_date: date
    end_date: date
    metric: Metric
    equity_curve: List[Dict[str, Any]] = []
    trades: List[Trade] = []


class StrategyGenerateRequest(BaseModel):
    description: str = Field(
        ...,
        description="自然语言描述的交易策略，例如：'MA5 上穿 MA20 买入，下穿卖出'",
        min_length=5,
    )


class StrategyGenerateResponse(BaseModel):
    description: str
    generated_code: str
    warning: Optional[str] = None
