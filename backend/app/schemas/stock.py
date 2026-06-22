"""Pydantic 模型：股票基础信息 / K 线 / 列表响应。"""
from datetime import date
from typing import Optional, List
from pydantic import BaseModel


class StockInfo(BaseModel):
    ts_code: str
    symbol: Optional[str] = None
    name: Optional[str] = None
    area: Optional[str] = None
    industry: Optional[str] = None
    market: Optional[str] = None


class KlineData(BaseModel):
    trade_date: date
    open: float
    high: float
    low: float
    close: float
    vol: Optional[float] = None
    amount: Optional[float] = None
    pct_chg: Optional[float] = None


class StockListResponse(BaseModel):
    total: int
    items: List[StockInfo]
    has_name: Optional[bool] = True
