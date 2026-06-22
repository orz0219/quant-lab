"""AI 辅助策略生成服务（QuantLab 亮点功能）。

- 在没有 LLM API 时，使用内置的"描述->代码"规则引擎，
  识别常见策略关键词并输出可执行的 Python 模板代码。
- 当配置了 LLM provider 时，可替换为真正的大模型调用。
"""
import re
from typing import Tuple, Optional

from app.core.config import settings
from app.schemas.backtest import (
    StrategyGenerateRequest, StrategyGenerateResponse,
)


_MA_CROSS_TEMPLATE = '''"""策略: {description}
由 QuantLab AI 自动生成。
可直接粘贴到 app/services/backtest_service.py 中替换 _simple_ma_backtest 逻辑。
"""
from typing import List, Dict, Any


class Strategy:
    """{description}"""

    def __init__(self, short_window: int = {short}, long_window: int = {long},
                 initial_cash: float = 100000.0):
        self.short_window = short_window
        self.long_window = long_window
        self.initial_cash = initial_cash

    @staticmethod
    def _ma(values: List[float], window: int) -> List[float]:
        out: List[float] = []
        for i in range(len(values)):
            if i + 1 < window:
                out.append(0.0)
            else:
                out.append(sum(values[i - window + 1:i + 1]) / window)
        return out

    def run(self, dates: List[Any], closes: List[float]) -> Dict[str, Any]:
        ma_s = self._ma(closes, self.short_window)
        ma_l = self._ma(closes, self.long_window)

        cash = self.initial_cash
        position = 0.0
        trades: List[Dict[str, Any]] = []
        equity: List[Dict[str, Any]] = []
        open_trade: Optional[Dict[str, Any]] = None

        for i in range(len(closes)):
            if i >= 1 and ma_l[i] > 0 and ma_l[i - 1] > 0:
                # 金叉买入
                if ma_s[i - 1] <= ma_l[i - 1] and ma_s[i] > ma_l[i] and position == 0:
                    shares = int(cash / closes[i] / 100) * 100
                    if shares > 0:
                        cost = shares * closes[i]
                        cash -= cost
                        position = shares
                        open_trade = {{"open_date": dates[i], "open_price": closes[i], "shares": shares}}
                # 死叉卖出
                elif ma_s[i - 1] >= ma_l[i - 1] and ma_s[i] < ma_l[i] and position > 0 and open_trade:
                    proceeds = position * closes[i]
                    trades.append({{
                        "open_date": open_trade["open_date"],
                        "close_date": dates[i],
                        "pnl": proceeds - open_trade["shares"] * open_trade["open_price"],
                    }})
                    cash += proceeds
                    position = 0
                    open_trade = None

            equity.append({{"date": str(dates[i]), "equity": cash + position * closes[i]}})

        return {{"trades": trades, "equity_curve": equity}}
'''


class StrategyService:
    def __init__(self):
        self.default_short = 5
        self.default_long = 20

    def _parse_windows(self, text: str) -> Tuple[int, int]:
        # 识别 "MA5 上穿 MA20" 或 "短长周期 5/20" 这样的数字
        matches = re.findall(r"MA\s*(\d+)|(\d+)\s*日?", text, flags=re.IGNORECASE)
        flat = []
        for groups in matches:
            for token in groups:
                if token:
                    try:
                        flat.append(int(token))
                    except ValueError:
                        pass
        flat = [x for x in flat if x > 0]
        if len(flat) >= 2 and flat[0] < flat[1]:
            return flat[0], flat[1]
        return self.default_short, self.default_long

    def generate(self, request: StrategyGenerateRequest) -> StrategyGenerateResponse:
        text = request.description
        warning: Optional[str] = None

        # 识别常见策略关键词
        if re.search(r"MA|均线|金叉|死叉|moving.?average|cross", text, re.IGNORECASE):
            short, long_ = self._parse_windows(text)
            code = _MA_CROSS_TEMPLATE.format(
                description=text, short=short, long=long_,
            )
        else:
            code = (
                '"""策略: {}\n\n'
                "QuantLab 当前仅内置 ma_cross 模板。\n"
                "请在描述中明确包含 '均线/MA' 等关键词，\n"
                '或配置 LLM API 以支持自由描述。"""\n'
            ).format(text)
            warning = "未识别到策略关键词，已返回占位代码。可在描述中加入 '均线' 等关键词。"

        return StrategyGenerateResponse(
            description=text,
            generated_code=code,
            warning=warning,
        )
