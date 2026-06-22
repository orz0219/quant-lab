"""领域数据模型。Kline / PinBarSignal。"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal, Optional


PinBarTag = Literal["P1", "P2", "P3", "N"]


@dataclass
class Kline:
    """单根 K 线（日/周通用）"""
    ts_code: str
    trade_date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    vol: Decimal
    amount: Optional[Decimal] = None
    pre_close: Optional[Decimal] = None
    pct_chg: Optional[Decimal] = None


@dataclass
class PinBarSignal:
    """pinBar 信号记录（对应 week_check 表的一行）"""
    ts_code: str
    trade_date: date
    price_open: Decimal
    price_high: Decimal
    price_low: Decimal
    price_close: Decimal
    pin_bar_tag: PinBarTag
    radio: Decimal
    win_p: Decimal
    lose_p: Decimal
    near_high: Decimal

    def to_row(self) -> tuple:
        return (
            self.ts_code,
            int(self.trade_date.strftime("%Y%m%d")),
            float(self.price_open),
            float(self.price_high),
            float(self.price_low),
            float(self.price_close),
            self.pin_bar_tag,
            float(self.radio),
            float(self.win_p),
            float(self.lose_p),
            float(self.near_high),
        )
