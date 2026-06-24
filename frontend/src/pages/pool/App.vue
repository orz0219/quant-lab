<template>
  <div>
    <div class="bg-aurora"></div>
    <div class="bg-grid"></div>
    <Nav active="pool" />
    <main class="workspace-single">
      <div class="headline center">
        <div class="pill"><span class="pill-dot"></span> 自选板块热度分析</div>
        <h2 class="head-title"><span class="grad-text">股票池</span> · <span class="grad-text-2">强中选强</span></h2>
        <p class="head-sub">基于你在选股页面加入自选的股票，按行业板块归类，判断哪些板块当前最受关注，寻找主线。</p>
      </div>
      <section class="glass card">
        <div class="card-head"><div class="card-title"><span class="title-dot cyan"></span> 我的股票池</div><span class="muted small">{{ watchlist.length }} 只股票</span><button class="small-btn btn-primary" style="padding:5px 12px;font-size:12px;white-space:nowrap;margin-left:8px;" @click="clearWatchlist">一键清除自选</button></div>
        <div class="pool-stock-list">
          <EmptyState v-if="!watchlist.length" icon="📂" title="自选池为空" desc='请先到<a href="/pages/screener/" style="color:var(--cyan);text-decoration:underline;">选股页面</a>扫描股票并点击「加入自选」。' />
          <template v-else>
            <div class="table-wrap">
              <table class="trades-table pool-table">
                <thead><tr><th style="width:40px;">#</th><th>代码</th><th>名称</th><th>行业</th><th style="width:180px;">操作</th></tr></thead>
                <tbody>
                  <tr v-for="(s, idx) in pageItems" :key="s.ts_code">
                    <td style="color:var(--muted);font-size:12px;">{{ (currentPage - 1) * pageSize + idx + 1 }}</td>
                    <td class="pool-stock-code clickable" @click="openDetail(s)">{{ s.ts_code }}</td>
                    <td style="font-weight:600;">{{ s.name || '—' }}</td>
                    <td><span class="screener-item-industry">{{ s.industry || '—' }}</span></td>
                    <td>
                      <button class="small-btn" style="padding:5px 10px;border-radius:6px;font-size:12px;background:var(--panel);border:1px solid var(--border);cursor:pointer;color:var(--text);" @click="removeWatch(s.ts_code)">✕ 移除</button>
                      <button class="btn-ghost small-btn" style="margin-left:4px;" @click="goBacktest(s)">回测</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <Pagination :current="currentPage" :total="watchlist.length" :page-size="pageSize" @change="currentPage = $event" />
          </template>
        </div>
      </section>
      <section v-if="sectors.length" class="glass card">
        <div class="card-head"><div class="card-title"><span class="title-dot pink"></span> 板块热度分析</div><span class="muted small">按行业归类，判断热门板块</span></div>
        <div class="pool-sectors">
          <div v-for="(sec, idx) in sectors" :key="sec.industry" :class="['sector-card', { 'sector-hot': idx < 3 }]">
            <div class="sector-head">
              <div class="sector-rank">#{{ idx + 1 }}</div>
              <div class="sector-name">{{ sec.industry }}</div>
              <span v-if="idx < 3" class="sector-hot-badge">🔥 热门</span>
              <div class="sector-count">{{ sec.count }} 只 <span class="muted">({{ (sec.count / watchlist.length * 100).toFixed(1) }}%)</span></div>
            </div>
            <div class="sector-bar-bg"><div class="sector-bar-fill" :style="{ width: (sec.count / sectors[0].count * 100).toFixed(0) + '%' }"></div></div>
            <div class="sector-stocks">
              <span v-for="stk in sec.stocks" :key="stk.ts_code" class="sector-stock-tag" :title="stk.ts_code" @click="openDetail(stk)">{{ stk.name || stk.ts_code }}</span>
            </div>
          </div>
        </div>
      </section>

      <section class="glass card">
        <div class="card-head"><div class="card-title"><span class="title-dot purple"></span> 板块 RS 热力图</div><span class="muted small">板块相对强度：红强绿弱，寻找主线</span></div>
        <div class="heat-date-range" v-if="dateRange">{{ dateRange }}</div>
        <div class="sector-chart-wrap" @mousedown="onHeatDragStart" @mousemove="onHeatMouseMove" @mouseleave="onHeatMouseLeave">
          <div v-if="chartLoading" class="chart-loading">计算板块 RS 强度中...</div>
          <div ref="heatmapLabelsRef" class="heatmap-labels" @click="onLabelClick"></div>
          <div ref="sectorChartRef" class="sector-chart" :style="{ opacity: chartLoading ? 0.3 : 1 }"></div>
        </div>
      </section>
      <Teleport to="body">
        <div v-if="tt.visible" class="heatmap-tooltip-fixed" :style="tt.style">
          <div class="tt-date">{{ tt.date }}</div>
          <div class="tt-industry">{{ tt.industry }}</div>
          <div class="tt-value">RS(20日动量) <b>{{ tt.val }}</b> ({{ tt.label }})</div>
        </div>
      </Teleport>

      <!-- 行业板块股票弹窗 -->
      <Teleport to="body">
        <div v-if="industryModalVisible" class="industry-modal-overlay" @click.self="industryModalVisible = false">
          <div class="industry-modal-box">
            <div class="industry-modal-head">
              <div class="industry-modal-title">{{ industryModalTitle }}</div>
              <button class="industry-modal-close" @click="industryModalVisible = false">✕</button>
            </div>
            <div class="industry-modal-body">
              <div v-if="industryModalLoading" class="industry-modal-loading">加载中...</div>
              <DataTable v-else :columns="indColumns" :rows="industryStocks" :page-size="9999" empty-text="该板块无数据">
                <template #cell-ts_code="{ row }">
                  <span class="ind-code-link" @click="openDetail(row)">{{ row.ts_code }}</span>
                </template>
                <template #cell-action="{ row }">
                  <span v-if="wlHas(row.ts_code)" class="ind-action-tag added">已加入</span>
                  <button v-else class="ind-action-btn" @click="addToWatchlist(row)">+ 自选</button>
                  <button class="ind-action-btn ind-btn-bt" @click="goBacktest(row)">回测</button>
                </template>
              </DataTable>
            </div>
          </div>
        </div>
      </Teleport>

      <StockDetailModal
        :visible="detailVisible"
        :stock="detailStock"
        @close="closeDetail"
      />

      <!-- 清空确认弹窗 -->
      <Teleport to="body">
        <div v-if="confirmVisible" class="confirm-overlay" @click.self="confirmVisible = false">
          <div class="confirm-box">
            <div class="confirm-title">确认清空</div>
            <div class="confirm-body">确定清空所有自选股？此操作不可撤销。</div>
            <div class="confirm-footer">
              <button class="btn-ghost" style="padding:9px 20px;" @click="confirmVisible = false">取消</button>
              <button class="btn-ghost" style="padding:9px 20px;" @click="doClear">确定清空</button>
            </div>
          </div>
        </div>
      </Teleport>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import Nav from '@/components/Nav.vue'
import EmptyState from '@/components/EmptyState.vue'
import Pagination from '@/components/Pagination.vue'
import DataTable from '@/components/DataTable.vue'
import StockDetailModal from '@/components/StockDetailModal.vue'
import { getAll, remove, clearAll, add as wlAdd, has as wlHas } from '@/utils/watchlist.js'
import { fetchSectorRS } from '@/utils/request.js'

const watchlist = ref([])
const currentPage = ref(1)
const pageSize = 10
const pageItems = computed(() => { const s = (currentPage.value - 1) * pageSize; return watchlist.value.slice(s, s + pageSize) })
const sectors = computed(() => {
  const items = watchlist.value; if (!items.length) return []
  const map = {}
  items.forEach(s => { const ind = s.industry || '其他'; if (!map[ind]) map[ind] = []; map[ind].push(s) })
  return Object.entries(map).map(([industry, stocks]) => ({ industry, stocks, count: stocks.length })).sort((a, b) => b.count - a.count)
})

const detailVisible = ref(false)
const detailStock = ref(null)
const confirmVisible = ref(false)

// 板块热力图
const sectorChartRef = ref(null)
const heatmapLabelsRef = ref(null)
const chartLoading = ref(false)

// Tooltip 状态
const tt = ref({ visible: false, style: {}, date: '', industry: '', val: '', label: '' })
// 日期范围显示
const dateRange = ref('')

// 行业板块股票弹窗
const industryModalVisible = ref(false)
const industryModalTitle = ref('')
const industryStocks = ref([])
const industryModalLoading = ref(false)

function addToWatchlist(stock) {
  if (wlAdd(stock)) loadWatchlist()
}

const indColumns = [
  { key: 'ts_code', label: '代码', width: '100px', class: 'ind-col-code' },
  { key: 'name', label: '名称' },
  { key: 'close', label: '价格', width: '80px' },
  { key: 'pct_chg', label: '涨幅', width: '80px', class: 'ind-col-pct' },
  { key: 'action', label: '操作', width: '150px' },
]

async function loadIndustryStocks(industry) {
  industryModalTitle.value = industry
  industryModalVisible.value = true
  industryModalLoading.value = true
  industryStocks.value = []
  try {
    const r = await fetch(`/api/v1/stocks/by_industry?industry=${encodeURIComponent(industry)}&limit=500`)
    if (r.ok) {
      industryStocks.value = await r.json()
    }
  } catch { /* 静默 */ }
  industryModalLoading.value = false
}

// 颜色阶梯
const RS_COLORS = ['#0a2a1a','#1a4a2a','#5a8a5a','#c0c0c0','#ffa070','#ff5030','#cc0000']

function lerpColor(a, b, t) {
  const ah = parseInt(a.slice(1), 16), bh = parseInt(b.slice(1), 16)
  const ar = (ah>>16)&255, ag = (ah>>8)&255, ab = ah&255
  const br = (bh>>16)&255, bg = (bh>>8)&255, bb = bh&255
  return `rgb(${Math.round(ar+(br-ar)*t)},${Math.round(ag+(bg-ag)*t)},${Math.round(ab+(bb-ab)*t)})`
}

function rsToColor(rs) {
  if (rs == null || isNaN(rs)) return 'transparent'
  const t = Math.max(-3, Math.min(3, rs))
  const idx = (t + 3) / 6 * 6  // 0 ~ 6
  const i0 = Math.floor(idx)
  const i1 = Math.min(i0 + 1, 6)
  return lerpColor(RS_COLORS[i0], RS_COLORS[i1], idx - i0)
}

// 板块名称点击处理
function onLabelClick(e) {
  const label = e.target.closest('.h-label')
  if (!label) return
  if (dragState && dragState.moved) return  // 拖拽中不触发
  loadIndustryStocks(label.getAttribute('title') || label.textContent.trim())
}

// 拖拽滚动状态
let dragState = null

function onHeatDragStart(e) {
  if (e.button !== 0) return
  const wrap = e.currentTarget
  dragState = {
    startX: e.clientX, startY: e.clientY,
    scrollLeft: wrap.scrollLeft, scrollTop: wrap.scrollTop,
    moved: false,
  }
  const onMove = (ev) => {
    if (!dragState) return
    const dx = ev.clientX - dragState.startX
    const dy = ev.clientY - dragState.startY
    if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
      dragState.moved = true
    }
    wrap.scrollLeft = dragState.scrollLeft - dx
    wrap.scrollTop = dragState.scrollTop - dy
  }
  const onUp = () => {
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
    setTimeout(() => { if (dragState) dragState.moved = false; dragState = null }, 20)
  }
  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}

// 热力悬浮
function onHeatMouseMove(e) {
  if (dragState && dragState.moved) { tt.value.visible = false; return }
  const cell = e.target.closest('.h-cell')
  if (!cell) { tt.value.visible = false; return }
  const rect = cell.getBoundingClientRect()
  const v = parseFloat(cell.dataset.rs)
  const label = v >= 1.2 ? '🔥 强势' : v >= 0.8 ? '偏强' : v >= -0.8 ? '中性' : v >= -1.2 ? '偏弱' : '❄️ 弱势'
  tt.value = {
    visible: true,
    style: { left: (rect.left + rect.width / 2) + 'px', top: (rect.top - 10) + 'px', transform: 'translateX(-50%)' },
    date: cell.dataset.date,
    industry: cell.dataset.industry,
    val: v.toFixed(2),
    label,
  }
}
function onHeatMouseLeave() { tt.value.visible = false }

function openDetail(stock) { detailStock.value = stock; detailVisible.value = true }
function closeDetail() { detailVisible.value = false; detailStock.value = null }

function goBacktest(stock) {
  localStorage.setItem('ql_pending_backtest', JSON.stringify({ ts_code: stock.ts_code, name: stock.name, industry: stock.industry }))
  location.href = '/pages/backtest/'
}

function clearWatchlist() { confirmVisible.value = true }
function doClear() { confirmVisible.value = false; clearAll(); loadWatchlist() }
function loadWatchlist() { watchlist.value = getAll() }

function removeWatch(tsCode) { remove(tsCode); loadWatchlist() }

// 从后端 RS API 加载板块热力图数据（全市场 1 年）
async function loadSectorHistory() {
  chartLoading.value = true
  try {
    const res = await fetchSectorRS(252)
    if (!res || !res.data || !res.dates.length) {
      chartLoading.value = false; return
    }
    await nextTick()
    renderSectorHeatmap(res.dates, res.industries, res.data)
  } catch { /* 静默失败 */ }
  chartLoading.value = false
}

function fmtDate(n) {
  const s = String(n)
  return s.slice(0,4) + '年' + s.slice(4,6) + '月' + s.slice(6,8) + '日'
}

function renderSectorHeatmap(dates, industries, dataItems) {
  const gridEl = sectorChartRef.value
  const labelsEl = heatmapLabelsRef.value
  if (!gridEl || !labelsEl) return

  // 构建 2D 查找表 grid[ii][di] = rs
  const grid = {}
  dataItems.forEach(item => { grid[item.ii + '_' + item.di] = item.rs })

  // 限制列数为最近 90 个交易日（避免太宽）
  const maxCols = Math.min(dates.length, 90)
  const colOffset = dates.length - maxCols
  const visDates = dates.slice(colOffset)

  // 设置居中日期范围
  dateRange.value = fmtDate(visDates[0]) + ' ～ ' + fmtDate(visDates[visDates.length - 1])

  const cellW = 10
  const cellGap = 2
  const rowH = 16
  const cols = maxCols
  const rows = industries.length
  const gridW = cols * (cellW + cellGap)
  const totalH = rows * rowH + 4

  gridEl.style.width = gridW + 'px'
  gridEl.style.height = Math.max(500, totalH) + 'px'

  // 左侧行业名称列（固定不滚动）
  const lastDi = colOffset + cols - 1
  const prevDi = colOffset + cols - 2
  let labelsHtml = ''
  for (let ii = 0; ii < rows; ii++) {
    // 最后一天与前一天比较，标记方向
    const lastRs = grid[ii + '_' + lastDi]
    const prevRs = grid[ii + '_' + prevDi]
    let arrow = ''
    if (lastRs != null && !isNaN(lastRs) && prevRs != null && !isNaN(prevRs)) {
      arrow = lastRs > prevRs ? '<span class="arr-up">▴</span>' : lastRs < prevRs ? '<span class="arr-down">▾</span>' : ''
    }
    labelsHtml += `<div class="h-label" title="${industries[ii]}">${industries[ii]} ${arrow}</div>`
  }
  labelsEl.innerHTML = labelsHtml
  labelsEl.style.height = Math.max(500, totalH) + 'px'

  // 右侧热力图网格（可滚动）
  let gridHtml = `<div class="h-grid" style="display:grid;grid-template-columns:repeat(${cols},${cellW}px);grid-template-rows:repeat(${rows},${rowH}px);gap:${cellGap}px;padding:2px;">`

  for (let ii = 0; ii < rows; ii++) {
    for (let di = 0; di < cols; di++) {
      const diOrig = di + colOffset
      const rs = grid[ii + '_' + diOrig]
      const color = rsToColor(rs)
      gridHtml += `<div class="h-cell" style="background:${color}" data-date="${visDates[di]}" data-industry="${industries[ii]}" data-rs="${rs ?? ''}"></div>`
    }
  }

  gridHtml += '</div>'
  gridEl.innerHTML = gridHtml
}

function initSectorHistory() {
  loadSectorHistory()
}

onMounted(() => {
  loadWatchlist()
  initSectorHistory()
})

onUnmounted(() => {
  // 清理 tooltip
  tt.value.visible = false
})
</script>

<style scoped>
.confirm-overlay {
  position: fixed; inset: 0; z-index: 99999;
  background: rgba(0,0,0,0.6);
  display: flex; align-items: center; justify-content: center;
}
.confirm-box {
  background: #0A1330; border: 1px solid rgba(255,255,255,0.12);
  border-radius: 16px; padding: 28px 32px; max-width: 400px; width: 90%;
  text-align: center;
}
.confirm-title { font-weight: 600; font-size: 16px; color: #E2E8F0; margin-bottom: 10px; }
.confirm-body { color: #94A3B8; font-size: 14px; line-height: 1.6; margin-bottom: 22px; }
.confirm-footer { display: flex; justify-content: center; gap: 12px; }

.sector-chart-wrap {
  display: flex;
  align-items: flex-start;
  position: relative;
  max-height: 65vh;
  overflow: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,0.10) transparent;
  cursor: grab;
  user-select: none;
}
.sector-chart-wrap:active { cursor: grabbing; }
.sector-chart-wrap::-webkit-scrollbar { width: 5px; height: 5px; }
.sector-chart-wrap::-webkit-scrollbar-track { background: transparent; }
.sector-chart-wrap::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.10); border-radius: 10px; }
.sector-chart-wrap::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.20); }

/* 左侧固定行业名称列 */
.heatmap-labels {
  flex-shrink: 0;
  position: sticky;
  left: 0;
  z-index: 10;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 2px 12px 2px 0;
}

.sector-chart { transition: opacity .3s; flex-shrink: 0; }
.chart-loading {
  position: absolute; inset: 0; z-index: 1;
  display: flex; align-items: center; justify-content: center;
  color: var(--muted); font-size: 14px;
}

/* 日期范围 */
.heat-date-range {
  text-align: center;
  font-size: 11px;
  color: #7B8AA6;
  padding: 6px 0 10px;
  letter-spacing: 0.3px;
}

/* 悬浮 tooltip */
.heatmap-tooltip-fixed {
  position: fixed;
  z-index: 999999;
  pointer-events: none;
  background: rgba(10,20,45,0.7);
  border: 1px solid rgba(168,85,247,0.45);
  border-radius: 8px;
  padding: 8px 12px;
  white-space: nowrap;
}
.heatmap-tooltip-fixed .tt-date { font-size: 12px; color: #7B8AA6; }
.heatmap-tooltip-fixed .tt-industry { font-size: 13px; color: #E2E8F0; font-weight: 600; }
.heatmap-tooltip-fixed .tt-value { font-size: 12px; color: #C9D3E4; }
.heatmap-tooltip-fixed .tt-value b { color: #E2E8F0; }
</style>

<!-- 非 scoped：innerHTML 生成的网格元素不受 scoped 影响 -->
<style>
.h-grid { font-size: 0; }
.h-label {
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; color: #C9D3E4; font-weight: 500;
  padding: 0 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  background: rgba(10,20,45,0.7);
  width: 90px; height: 16px; flex-shrink: 0;
  box-sizing: border-box;
}
.h-label:hover { color: #E2E8F0; }
.arr-up { color: #ef4444; font-size: 14px; }
.arr-down { color: #22c55e; font-size: 14px; }
.h-cell {
  width: 10px; height: 16px;
  border-radius: 1px;
  cursor: pointer;
  transition: opacity .15s;
}
.h-cell:hover { opacity: 0.7; outline: 1.5px solid rgba(255,255,255,0.5); outline-offset: -1px; }
.h-label { cursor: pointer; }
.h-label:hover { color: var(--cyan) !important; text-decoration: underline; }

/* 行业股票弹窗 */
.industry-modal-overlay {
  position: fixed; inset: 0; z-index: 99999;
  background: rgba(0,0,0,0.6);
  display: flex; align-items: flex-start; justify-content: center;
  padding-top: 8vh;
}
.industry-modal-box {
  background: #0A1330;
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 16px;
  width: min(860px, 95vw);
  max-height: 80vh;
  display: flex; flex-direction: column;
}
.industry-modal-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 24px 0;
}
.industry-modal-title { font-weight: 600; font-size: 16px; color: #E2E8F0; }
.industry-modal-close {
  background: none; border: none; color: #7B8AA6; font-size: 18px;
  cursor: pointer; padding: 4px 8px; border-radius: 4px;
}
.industry-modal-close:hover { background: rgba(255,255,255,0.08); color: #E2E8F0; }
.industry-modal-body {
  padding: 16px 24px 24px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,0.10) transparent;
}
.industry-modal-body::-webkit-scrollbar { width: 4px; }
.industry-modal-body::-webkit-scrollbar-track { background: transparent; }
.industry-modal-body::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.10); border-radius: 10px; }
.industry-modal-body::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.20); }
.industry-modal-loading { text-align: center; color: #7B8AA6; padding: 40px 0; }

/* 表格列样式 */
.ind-col-code { color: var(--cyan); font-family: monospace; font-size: 12px; }
.ind-code-link {
  color: var(--cyan); font-family: "SF Mono", Consolas, monospace;
  font-size: 12px; cursor: pointer;
}
.ind-code-link:hover { text-decoration: underline; }
.ind-col-pct { font-family: monospace; font-size: 12px; font-weight: 600; }

/* 操作按钮 */
.ind-action-btn {
  display: inline-block; padding: 3px 8px; border-radius: 6px;
  font-size: 11px; background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.10); color: var(--text);
  cursor: pointer; margin-right: 4px; transition: all .15s;
}
.ind-action-btn:hover { border-color: var(--cyan); color: var(--cyan); }
.ind-btn-bt { font-size: 11px; }
.ind-btn-bt:hover { border-color: var(--purple); color: var(--purple); }
.ind-action-tag {
  display: inline-block; padding: 3px 8px; border-radius: 6px;
  font-size: 11px; background: rgba(34,211,238,0.08);
  border: 1px solid rgba(34,211,238,0.25); color: var(--cyan);
  margin-right: 4px;
}
</style>