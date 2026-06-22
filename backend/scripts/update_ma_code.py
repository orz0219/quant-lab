"""更新 MA Cross 均线策略的代码，使其使用自定义参数 MA_S / MA_L。"""
import sys
from pathlib import Path

def _find_root(start):
    c = start.resolve()
    for _ in range(8):
        if (c / "app" / "main.py").is_file():
            return c
        if c.parent == c:
            break
        c = c.parent
    return start.parent.parent

ROOT = _find_root(Path(__file__))
sys.path.insert(0, str(ROOT))

from app.core.config import settings
from app.core.database import DuckDBPool

db = DuckDBPool(settings.DB_PATH)
db.ensure_tables_exist()

rows = db.query_list("SELECT id FROM user_strategies WHERE name = 'MA Cross 均线策略' LIMIT 1")
if not rows:
    print("未找到 MA Cross 策略")
    sys.exit(1)

sid = rows[0][0]

NEW_CODE = """/**
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
}"""

db.execute("UPDATE user_strategies SET code = ? WHERE id = ?", [NEW_CODE, sid])
print("MA Cross 策略代码已更新，ID:", sid[:12])

# 验证
row = db.query_list("SELECT code FROM user_strategies WHERE id = ?", [sid])
has_s = "context.MA_S" in row[0][0]
has_l = "context.MA_L" in row[0][0]
has_old = "context.short" in row[0][0]
print(f"  context.MA_S 引用: {'✅' if has_s else '❌'}")
print(f"  context.MA_L 引用: {'✅' if has_l else '❌'}")
print(f"  context.short 残留: {'⚠️' if has_old else '✅ 已清理'}")
