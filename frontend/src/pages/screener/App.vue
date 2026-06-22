<template>
  <div>
    <div class="bg-aurora"></div>
    <div class="bg-grid"></div>
    <Nav active="screener" />
    <main class="workspace-single">
      <div class="headline center">
        <div class="pill"><span class="pill-dot"></span> 最近一周策略买点扫描</div>
        <h2 class="head-title"><span class="grad-text">选股</span> 标签 · 发现你的<span class="grad-text-2">目标股票</span></h2>
        <p class="head-sub">选择你关注的策略，系统将自动扫描所有可查询股票，挑出最近一周内出现买点信号的标的。</p>
      </div>
      <section class="glass card">
        <div class="card-head"><div class="card-title"><span class="title-dot cyan"></span> 策略选择</div></div>
        <div class="screener-body">
          <div class="screener-row-top">
            <div class="screener-left">
              <div class="screener-strategy"><label>回测策略</label><SelectBox v-model="selectedStrategy" :options="strategyOptions" /></div>
              <div class="screener-cycle"><label>K线周期</label><SelectBox v-model="cycle" :options="cycleOptions" /></div>
            </div>
            <div v-if="strategyParams.length" class="screener-separator"></div>
            <div class="screener-params">
              <div v-for="p in strategyParams" :key="p.id" class="field" style="margin-bottom:0;">
                <label>{{ p.label }}</label>
                <input :type="p.type" v-model="p.value" />
              </div>
            </div>
          </div>
          <div class="screener-row-bottom" style="flex-direction:column;align-items:center;">
            <div class="scan-divider"></div>
            <button class="btn-primary scan-btn" @click="startScan">{{ btnLabel }}</button>
          </div>
        </div>
      </section>
      <section v-if="summaryVisible" class="glass card">
        <div class="card-head"><div class="card-title"><span class="title-dot"></span> 扫描结果</div></div>
        <div class="summary-stats">
          <div class="stat"><div class="stat-label">总扫描</div><div class="stat-value">{{ totalScanned }}</div></div>
          <div class="stat"><div class="stat-label">命中数</div><div class="stat-value ok">{{ hits.length }}</div></div>
          <div class="stat"><div class="stat-label">命中率</div><div class="stat-value">{{ hitRate }}</div></div>
          <div class="stat"><div class="stat-label">最近信号</div><div class="stat-value">{{ latestDate }}</div></div>
        </div>
      </section>
      <section class="glass card">
        <div class="card-head">
          <div class="card-title"><span class="title-dot pink"></span> 一周内出现买点的股票</div>
          <div class="card-head-actions">
            <input type="text" v-model="keyword" placeholder="过滤代码/名称..." class="card-filter-input" />
            <button class="small-btn btn-primary" style="padding:5px 12px;font-size:12px;white-space:nowrap;" @click="addAllToWatchlist" :disabled="!filteredHits.length">一键添加自选</button>
          </div>
        </div>
        <DataTable
          :columns="tableColumns"
          :rows="filteredHits"
          empty-text="请先选择策略，然后点击「开始扫描」以获得最近一周内出现买点的股票。"
        >
          <template #cell-ts_code="{ row }"><span class="pool-stock-code clickable" @click="openDetail(row)">{{ row.ts_code }}</span></template>
          <template #cell-name="{ value }"><span style="font-weight:600;">{{ value || '—' }}</span></template>
          <template #cell-industry="{ value }"><span class="screener-item-industry">{{ value || '—' }}</span></template>
          <template #cell-signal_date="{ value }"><span class="mono">{{ value || '—' }}</span></template>
          <template #cell-signal_price="{ value }"><span class="mono">{{ value != null ? fmtPrice(value) : '—' }}</span></template>
          <template #cell-_actions="{ row }">
            <span style="display:flex;gap:6px;align-items:center;">
              <button v-if="!inWatchlist(row.ts_code)" class="small-btn btn-primary" style="padding:4px 10px;font-size:12px;" @click="addWatch(row)">+ 自选</button>
              <span v-else class="muted" style="font-size:12px;">✓ 自选</span>
              <button class="small-btn btn-ghost" style="margin-left:auto;padding:4px 10px;font-size:12px;" @click="goBacktest(row)">回测</button>
            </span>
          </template>
        </DataTable>
      </section>
    </main>

    <StockDetailModal
      :visible="detailVisible"
      :stock="detailStock"
      :strategy-code="strategyCode"
      :strategy-params="strategyParams"
      @close="closeDetail"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import Nav from '@/components/Nav.vue'
import EmptyState from '@/components/EmptyState.vue'
import DataTable from '@/components/DataTable.vue'
import StockDetailModal from '@/components/StockDetailModal.vue'
import SelectBox from '@/components/SelectBox.vue'
import { fetchStocks, fetchKline, strategyApi } from '@/utils/request.js'
import { fmtNum } from '@/utils/format.js'
import { getAll as getWatchlist, add as addWatchlist } from '@/utils/watchlist.js'
import { useScreenerCache } from '@/hooks/useScreenerCache.js'
import { useCache } from '@/hooks/useCache.js'

const strategies = ref([])
const selectedStrategy = useCache('backtest_strategy', '')
const cycle = useCache('screener_cycle', 'daily')
const strategyParams = ref([])
const strategyCode = ref('')
const hits = ref([])
const totalScanned = ref(0)
const summaryVisible = ref(false)
const keyword = useCache('screener_keyword', '')
const running = ref(false)
const stopRequested = ref(false)
const cache = useScreenerCache()

const strategyOptions = computed(() =>
  strategies.value.map(s => ({ value: s.key, label: s.name }))
)

const cycleOptions = [
  { value: 'daily', label: '日线' },
  { value: 'weekly', label: '周线' },
]

const tableColumns = [
  { key: 'ts_code', label: '代码', class: 'pool-stock-code' },
  { key: 'name', label: '名称', width: '140px' },
  { key: 'industry', label: '行业' },
  { key: 'signal_date', label: '信号日期', class: 'mono' },
  { key: 'signal_price', label: '信号价格', class: 'mono' },
  { key: '_actions', label: '操作', width: '140px' },
]

const filteredHits = computed(() => {
  if (!keyword.value) return hits.value
  const kw = keyword.value.toLowerCase()
  return hits.value.filter(s => s.ts_code.toLowerCase().includes(kw) || (s.name || '').toLowerCase().includes(kw))
})
const btnLabel = computed(() => {
  if (!running.value) return '🔍 开始扫描'
  return '⏹ 停止扫描'
})
const hitRate = computed(() => totalScanned.value ? ((hits.value.length / totalScanned.value) * 100).toFixed(1) + '%' : '—')
const latestDate = computed(() => hits.value.length ? hits.value[0].signal_date || '—' : '—')

const fmtPrice = (v) => fmtNum(v)
const watchlist = ref(getWatchlist())
function inWatchlist(tsCode) { return watchlist.value.some(s => s.ts_code === tsCode) }
function addWatch(stock) {
  if (addWatchlist(stock)) { watchlist.value = getWatchlist(); hits.value = [...hits.value] }
}
function addAllToWatchlist() {
  let added = 0
  filteredHits.value.forEach(s => { if (addWatchlist(s)) added++ })
  if (added > 0) { watchlist.value = getWatchlist(); hits.value = [...hits.value] }
}
function goBacktest(stock) {
  localStorage.setItem('ql_pending_backtest', JSON.stringify({ ts_code: stock.ts_code, name: stock.name, industry: stock.industry }))
  location.href = '/pages/backtest/'
}

// ---------- 股票详情弹窗 ----------
const detailVisible = ref(false)
const detailStock = ref(null)
function openDetail(stock) { detailStock.value = stock; detailVisible.value = true }
function closeDetail() { detailVisible.value = false; detailStock.value = null }

const paramsCacheKey = computed(() => 'params_' + selectedStrategy.value)

function restoreCachedParams() {
  if (!selectedStrategy.value) return
  try {
    const raw = localStorage.getItem('ql_' + paramsCacheKey.value)
    if (!raw) return
    const cached = JSON.parse(raw)
    if (cached && typeof cached === 'object') {
      strategyParams.value.forEach(p => {
        if (cached[p.id] !== undefined) p.value = cached[p.id]
      })
    }
  } catch { /* 忽略 */ }
}

function saveParamsToCache() {
  if (!selectedStrategy.value || !strategyParams.value.length) return
  const obj = {}
  strategyParams.value.forEach(p => { obj[p.id] = p.value })
  try { localStorage.setItem('ql_' + paramsCacheKey.value, JSON.stringify(obj)) } catch {}
}

async function loadStrategyParams() {
  if (!selectedStrategy.value) { strategyParams.value = []; strategyCode.value = ''; return }
  try {
    const item = await strategyApi.get(selectedStrategy.value.slice(5))
    strategyCode.value = item.code || ''
    const schema = item.params_schema?.properties || {}
    strategyParams.value = Object.keys(schema).map(k => ({
      id: k, label: schema[k].label || k,
      type: schema[k].type === 'number' ? 'number' : 'text',
      value: schema[k].default != null ? schema[k].default : '',
    }))
    restoreCachedParams()
  } catch { strategyParams.value = [] }
}

// 参数值变化时自动保存缓存
watch(strategyParams, saveParamsToCache, { deep: true })

watch(selectedStrategy, loadStrategyParams)

async function loadStrategies() {
  try {
    const res = await strategyApi.list()
    strategies.value = (res.items || []).map(s => ({ key: 'user_' + s.id, name: s.name, id: s.id }))
    if (strategies.value.length) {
      // 如果已有缓存值且存在于策略列表，保留缓存值；否则使用第一个策略
      if (!selectedStrategy.value || !strategies.value.some(s => s.key === selectedStrategy.value)) {
        selectedStrategy.value = strategies.value[0].key
      }
      await loadStrategyParams()
    }
  } catch { strategies.value = [] }
}

// ---------- 沙箱执行策略，返回该股票是否有买入信号 ----------
function runStrategyOnStock(code, params, klines) {
  const signals = []
  const ctx = {
    params: params || {},
    state: {},
    buy(opts) {
      signals.push({ type: 'buy', price: opts?.price || 0, reason: opts?.reason || '', trade_date: this._curDate })
    },
    sell(opts) {
      signals.push({ type: 'sell', price: opts?.price || 0, reason: opts?.reason || '', trade_date: this._curDate })
    },
    log() {},
  }
  const src = code + '\nif (typeof init !== "function") throw new Error("缺少 init"); if (typeof onTick !== "function") throw new Error("缺少 onTick"); return { init, onTick, onDestroy: typeof onDestroy === "function" ? onDestroy : function(){} };'
  const { init: initFn, onTick: onTickFn, onDestroy: destroyFn } = new Function(src)()
  initFn(ctx)
  for (const k of klines) {
    ctx._curDate = String(k.trade_date)
    onTickFn(ctx, { open: k.open, high: k.high, low: k.low, close: k.close, volume: k.vol, vol: k.vol, trade_date: k.trade_date })
  }
  destroyFn(ctx)
  return signals
}

function runBuySignalsOnStock(code, params, klines) {
  return runStrategyOnStock(code, params, klines).filter(s => s.type === 'buy')
}

// ---------- 获取某只股票最近一周的 K 线 ----------
async function fetchKlineForStock(tsCode) {
  const now = new Date()
  const toYMD = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`

  const endStr = toYMD(now)
  const ago = new Date(now)
  ago.setFullYear(ago.getFullYear() - 1) // 取一年数据保证 MA 等指标计算不失真
  const startStr = toYMD(ago)

  const klines = await fetchKline(tsCode, startStr, endStr, cycle.value)
  return (klines || []).map(k => ({
    trade_date: String(k.trade_date || k.date),
    open: k.open, high: k.high, low: k.low, close: k.close, vol: k.vol || k.volume || 0,
  }))
}

// ---------- 主扫描流程（分批 + 实时更新） ----------
async function startScan() {
  if (running.value) {
    if (!stopRequested.value) stopRequested.value = true
    return
  }
  if (!strategyCode.value) { alert('当前策略无代码，请选含 JS 的策略'); return }

  cache.clear()
  running.value = true
  if (!summaryVisible.value) summaryVisible.value = true
  totalScanned.value = 0
  hits.value = []

  const params = {}
  strategyParams.value.forEach(p => { params[p.id] = p.value })

  // 最近 7 天的截止日期（与 API trade_date 格式一致：YYYY-MM-DD）
  const now = new Date()
  const weekAgo = new Date(now)
  weekAgo.setDate(weekAgo.getDate() - 7)
  const toYMD = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  const cutoffStr = toYMD(weekAgo)

  try {
    // 1. 获取股票列表
    const stockRes = await fetchStocks('')
    const allStocks = stockRes?.items || []
    const total = allStocks.length

    const results = []
    let scannedCount = 0
    const BATCH = 5
    let idx = 0

    function processBatch() {
      if (stopRequested.value) {
        cache.save(results, scannedCount)
        running.value = false
        stopRequested.value = false
        return
      }
      const batch = allStocks.slice(idx, idx + BATCH)
      if (!batch.length) {
        cache.save(results, scannedCount)
        running.value = false
        return
      }

      Promise.all(batch.map(async (stk) => {
        try {
          const klines = await fetchKlineForStock(stk.ts_code, '')
          if (klines.length < 20) return { skip: true }
          const buySignals = runBuySignalsOnStock(strategyCode.value, params, klines)
          if (!buySignals.length) return { skip: true }
          // 只取最近一周内的买入信号（信号日期为数字格式 YYYYMMDD）
          const recent = buySignals.filter(s => s.trade_date >= cutoffStr)
          if (!recent.length) return { skip: true }
          const last = recent[recent.length - 1]
          return {
            ts_code: stk.ts_code,
            name: stk.name || '',
            industry: stk.industry || '',
            signal_date: last.trade_date,
            signal_price: last.price,
          }
        } catch { return { skip: true } }
      })).then((batchResults) => {
        batchResults.forEach(r => {
          if (r && !r.skip) results.push(r)
          if (r) scannedCount++
        })
        idx += BATCH
        totalScanned.value = scannedCount
        // 按信号日期降序排列，最新信号排第一
        results.sort((a, b) => b.signal_date.localeCompare(a.signal_date))
        hits.value = [...results]
        // 每批完成后更新缓存
        cache.save(results, scannedCount)

        // 安排下一批
        setTimeout(processBatch, 30)
      })
    }

    processBatch()
  } catch (err) {
    alert('扫描异常: ' + (err.message || String(err)))
    running.value = false
  }
}

onMounted(() => {
  loadStrategies()
  const cached = cache.load()
  if (cached?.hits?.length) { hits.value = cached.hits; totalScanned.value = cached.totalScanned || cached.hits.length; summaryVisible.value = true }
})
</script>
