"""将内置均线策略写入 user_strategies 表。"""
import sys
import uuid
import hashlib
import json
from datetime import datetime
from pathlib import Path


def _find_backend_root(start: Path) -> Path:
    cursor = start.resolve()
    for _ in range(8):
        if (cursor / "app" / "main.py").is_file():
            return cursor
        if cursor.parent == cursor:
            break
        cursor = cursor.parent
    return start.resolve().parent.parent


PROJECT_ROOT = _find_backend_root(Path(__file__))
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.core.database import DuckDBPool


MA_CROSS_CODE = r'''/**
 * 均线金叉/死叉策略 (MA Cross)
 * 生命周期: init → onTick (每根 K 线) → onDestroy
 */
function init(context) {
  context.MA_S = context.params.MA_S || 5;
  context.MA_L = context.params.MA_L || 20;
  context.prevS = null;
  context.prevL = null;
  context.log('MA Cross 初始化: 短均线=' + context.MA_S + ', 长均线=' + context.MA_L);
}

function onTick(context, bar) {
  if (!bar) return;
  if (!context.prices) context.prices = [];
  context.prices.push(bar.close);
  if (context.prices.length > context.MA_L) context.prices.shift();
  if (context.prices.length < context.MA_L) return;
  var shortArr = context.prices.slice(-context.MA_S);
  var longArr = context.prices.slice(-context.MA_L);
  var curS = shortArr.reduce(function(a,b){return a+b;}) / shortArr.length;
  var curL = longArr.reduce(function(a,b){return a+b;}) / longArr.length;
  if (context.prevS !== null && context.prevL !== null) {
    if (context.prevS <= context.prevL && curS > curL) context.buy({price:bar.close, reason:'金叉买入'});
    else if (context.prevS >= context.prevL && curS < curL) context.sell({price:bar.close, reason:'死叉卖出'});
  }
  context.prevS = curS;
  context.prevL = curL;
}

function onDestroy(context) {
  context.log('MA Cross 策略已停止');
}'''

PARAMS_SCHEMA = {
    "type": "object",
    "properties": {
        "MA_S": {"type": "number", "default": 5, "label": "短均线"},
        "MA_L": {"type": "number", "default": 20, "label": "长均线"},
    },
    "required": [],
}


def main():
    db = DuckDBPool(settings.DB_PATH)
    db.ensure_tables_exist()

    sid = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    csum = hashlib.sha256(MA_CROSS_CODE.encode()).hexdigest()[:16]

    # 检测是否已有同名内置策略
    existing = db.query_list(
        "SELECT id FROM user_strategies WHERE is_builtin = TRUE LIMIT 1",
    )
    if existing:
        print(f"内置策略已存在 (id={existing[0][0][:12]}...)，跳过写入。")
        return

    db.execute(
        """INSERT INTO user_strategies
           (id, name, description, tags, code, params_schema, dependencies, version, checksum, is_builtin, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, TRUE, ?, ?)""",
        [
            sid,
            "MA Cross 均线策略",
            "经典的双均线金叉/死叉策略。当短均线上穿长均线时买入，下穿时卖出。",
            "均线,趋势,经典",
            MA_CROSS_CODE,
            json.dumps(PARAMS_SCHEMA),
            "[]",  # dependencies
            csum,
            now,
            now,
        ],
    )
    print(f"MA Cross 均线策略已写入，id={sid}")


if __name__ == "__main__":
    main()
