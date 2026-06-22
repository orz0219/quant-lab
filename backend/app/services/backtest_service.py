"""简易回测引擎：内置 MA 金叉/死叉策略。

注意：这里实现的是"不依赖 backtrader"的纯 Python 回测，
便于在线 Demo 直接跑。若项目已安装 backtrader，可在
engine.py 中替换为更完整的实现。
"""
from typing import List, Optional, Dict, Any
from datetime import date as _date

from app.core.database import DuckDBPool
from app.schemas.backtest import BacktestRequest, BacktestResult, Metric, Trade
from app.services.stock_service import StockService


class BacktestService:
    def __init__(self, db: DuckDBPool):
        self.db = db
        self.stock = StockService(db)

    def run(self, request: BacktestRequest) -> BacktestResult:
        klines = self.stock.get_klines(
            request.ts_code,
            int(request.start_date.strftime("%Y%m%d")),
            int(request.end_date.strftime("%Y%m%d")),
        )
        if len(klines) < 5:
            return BacktestResult(
                ts_code=request.ts_code,
                start_date=request.start_date,
                end_date=request.end_date,
                metric=Metric(),
                equity_curve=[],
                trades=[],
            )

        closes = [k.close for k in klines]
        dates = [k.trade_date for k in klines]

        params = request.params or {}
        short = int(params.get("short", 5))
        long_ = int(params.get("long", 20))

        # 计算 MA
        def ma(window: int) -> List[float]:
            out: List[float] = []
            for i in range(len(closes)):
                if i + 1 < window:
                    out.append(0.0)
                else:
                    out.append(sum(closes[i - window + 1 : i + 1]) / window)
            return out

        ma_short = ma(short)
        ma_long = ma(long_)

        cash = request.initial_cash
        position = 0.0
        trades: List[Trade] = []
        equity_curve: List[Dict[str, Any]] = []
        open_trade: Optional[Dict[str, Any]] = None

        for i in range(len(closes)):
            if i >= 1 and ma_long[i] > 0 and ma_long[i - 1] > 0:
                if ma_short[i - 1] <= ma_long[i - 1] and ma_short[i] > ma_long[i]:
                    # 金叉买入
                    if position == 0 and cash > 0:
                        shares = int(cash / closes[i] / 100) * 100
                        if shares > 0:
                            cost = shares * closes[i]
                            cash -= cost
                            position = shares
                            open_trade = {
                                "open_date": dates[i],
                                "open_price": closes[i],
                                "shares": shares,
                            }
                elif ma_short[i - 1] >= ma_long[i - 1] and ma_short[i] < ma_long[i]:
                    # 死叉卖出
                    if position > 0 and open_trade is not None:
                        proceeds = position * closes[i]
                        pnl = proceeds - open_trade["shares"] * open_trade["open_price"]
                        pnl_pct = pnl / (open_trade["shares"] * open_trade["open_price"])
                        trades.append(Trade(
                            open_date=open_trade["open_date"],
                            close_date=dates[i],
                            side="long",
                            open_price=open_trade["open_price"],
                            close_price=closes[i],
                            pnl=pnl,
                            pnl_pct=pnl_pct,
                        ))
                        cash += proceeds
                        position = 0
                        open_trade = None

            equity = cash + position * closes[i]
            equity_curve.append({"date": dates[i].isoformat(), "equity": equity})

        # 计算指标
        final_equity = equity_curve[-1]["equity"] if equity_curve else request.initial_cash
        total_return = (final_equity - request.initial_cash) / request.initial_cash

        peak = request.initial_cash
        max_drawdown = 0.0
        for point in equity_curve:
            peak = max(peak, point["equity"])
            dd = (peak - point["equity"]) / peak if peak > 0 else 0.0
            max_drawdown = max(max_drawdown, dd)

        wins = sum(1 for t in trades if (t.pnl or 0) > 0)
        win_rate = wins / len(trades) if trades else 0.0

        days = max(1, (dates[-1] - dates[0]).days)
        annual = (1 + total_return) ** (365 / days) - 1

        metric = Metric(
            total_return=total_return,
            annual_return=annual,
            max_drawdown=max_drawdown,
            sharpe=0.0,
            win_rate=win_rate,
            trades=len(trades),
        )
        return BacktestResult(
            ts_code=request.ts_code,
            start_date=request.start_date,
            end_date=request.end_date,
            metric=metric,
            equity_curve=equity_curve,
            trades=trades,
        )
