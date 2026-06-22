"""行业板块 RS（相对强度）接口。

RS = 板块过去 20 日累积涨幅 / |全市场过去 20 日累积涨幅|（价格动量 RS）

前端数据已按最后一天 RS 从大到小排列。
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Query

from app.core.config import settings
from app.core.database import DuckDBPool

router = APIRouter()
_db = DuckDBPool(settings.DB_PATH)


@router.get("/rs")
def get_sector_rs(
    days: int = Query(252, ge=1, le=500, description="回溯天数"),
):
    """返回各行业板块的 RS 时序数据（价格动量），用于前端热力图。"""
    _db.ensure_tables_exist()

    today = datetime.today()
    from_date = today - timedelta(days=int(days * 1.4))
    trade_date_from = int(from_date.strftime("%Y%m%d"))
    trade_date_to = int(today.strftime("%Y%m%d"))

    # 从缓存表读取
    rows = _db.query_list(
        """SELECT trade_date, industry, rs
           FROM sector_rs_cache
           WHERE trade_date >= ? AND trade_date <= ?
           ORDER BY trade_date, industry""",
        [trade_date_from, trade_date_to],
    )

    if not rows:
        return {"dates": [], "industries": [], "data": []}

    # 整理日期和行业
    date_set = {}
    ind_set = {}
    for r in rows:
        date_set[r[0]] = True
        ind_set[r[1]] = True

    dates = sorted(date_set.keys())
    all_industries = list(ind_set.keys())

    # 按最后一天的 RS 降序排列行业
    last_date = dates[-1]
    last_day_rs = {}
    for r in rows:
        if r[0] == last_date:
            last_day_rs[r[1]] = r[2]  # rs

    sorted_industries = sorted(all_industries, key=lambda ind: -last_day_rs.get(ind, 0))

    date_index = {d: i for i, d in enumerate(dates)}
    ind_index = {ind: i for i, ind in enumerate(sorted_industries)}

    # 构建热力图数据
    heatmap = []
    for r in rows:
        d, ind, rs = r
        if ind not in ind_index:
            continue
        heatmap.append({
            "di": date_index[d],
            "ii": ind_index[ind],
            "rs": round(float(rs), 2),
        })

    return {
        "dates": [str(d) for d in dates],
        "industries": sorted_industries,
        "data": heatmap,
    }
