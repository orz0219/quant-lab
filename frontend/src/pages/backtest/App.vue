<template>
  <div>
    <div class="bg-aurora"></div>
    <div class="bg-grid"></div>
    <Nav active="backtest" />
    <main class="workspace">
      <aside class="sidebar glass">
        <div class="panel">
          <div class="panel-title"><span class="dot dot-cyan"></span>股票 &amp; 时间</div>
          <div class="field"><label>股票代码</label><StockCombobox v-model="stockCode" @select="onStockSelect" /></div>
          <div v-if="stockName" class="field">
            <div class="meta-row"><span class="muted">名称</span><span>{{ stockName }}</span></div>
            <div class="meta-row"><span class="muted">行业</span><span>{{ stockIndustry }}</span></div>
          </div>
          <div class="field two-col">
            <div><label>起始日</label><input type="date" v-model="startDate" @change="loadKline" /></div>
            <div><label>结束日</label><input type="date" v-model="endDate" @change="loadKline" /></div>
          </div>
          <div class="field"><label>初始资金</label><input type="number" v-model.number="initialCash" /></div>
        </div>
        <div class="panel">
          <div class="panel-title"><span class="dot dot-pink"></span>策略 &amp; 参数</div>
          <div class="field">
            <label>策略类型</label>
            <SelectBox v-model="strategyKey" :options="strategyOptions" @change="onStrategyChange" />
          </div>
          <div class="field">
            <div v-for="p in strategyParams" :key="p.id" class="field">
              <label>{{ p.label }}</label>
              <input :type="p.type" v-model="p.value" />
            </div>
          </div>
        </div>
        <StopSettings :settings="stopSettings" @update="onStopUpdate" />
        <div class="action-row">
          <button class="btn-primary big" @click="runBacktest"><span class="play">▶</span> 运行回测</button>
        </div>
        <div class="tiny muted">© 2026 QuantLab · 仅供研究演示</div>
      </aside>
      <section class="main-area">
        <div class="headline">
          <h2 class="head-title">用 <span class="grad-text">AI</span> 重新定义<span class="grad-text-2"> 股票策略回测</span></h2>
          <p class="head-sub">用自然语言描述你的交易思路，系统会自动生成策略代码并完成回测验证。</p>
        </div>
        <KlineCard
          :klines="klines"
          :trades="trades"
          :stock-name="stockName"
          :freq="freq"
          :indicator-settings="indicatorSettings"
          @update:freq="onFreqChange"
          @open-settings="drawerVisible = true"
        />
        <MetricCards :metric="metric" />
        <div class="glass card">
          <div class="card-head"><div class="card-title"><span class="title-dot cyan"></span>权益曲线</div><span class="muted small">{{ equityMeta }}</span></div>
          <div ref="equityContainer" class="chart"></div>
        </div>
        <div class="glass card">
          <div class="card-head"><div class="card-title"><span class="title-dot pink"></span>交易明细</div><span class="muted small">{{ trades.length ? trades.length + ' 笔交易' : '暂无数据' }}</span></div>
          <TradeTable :trades="trades" />
        </div>
      </section>
    </main>
    <IndicatorDrawer v-model:visible="drawerVisible" v-model:showKline="indicatorSettings.showKline" v-model:showVolume="indicatorSettings.showVolume" v-model:showMA="indicatorSettings.showMA" v-model:upColor="indicatorSettings.upColor" v-model:downColor="indicatorSettings.downColor" v-model:maList="indicatorSettings.maList" @close="drawerVisible = false" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick, computed, watch } from 'vue'
import Nav from '@/components/Nav.vue'
import StockCombobox from '@/components/StockCombobox.vue'
import StopSettings from '@/components/StopSettings.vue'
import KlineCard from '@/components/KlineCard.vue'
import SelectBox from '@/components/SelectBox.vue'
import MetricCards from '@/components/MetricCards.vue'
import TradeTable from '@/components/TradeTable.vue'
import IndicatorDrawer from '@/components/IndicatorDrawer.vue'
import { fetchKline, strategyApi, loadIndicatorSettings, saveIndicatorSettings } from '@/utils/request.js'
import { todayISO } from '@/utils/date.js'
import { fmtNum } from '@/utils/format.js'
import { resample, simpleMA, sharpeRatio } from '@/utils/math.js'
import { useStopSettings } from '@/hooks/useStopSettings.js'
import { useCache } from '@/hooks/useCache.js'

const { settings: stopSettings, save: saveStop, collect: collectStop } = useStopSettings()

const stockCode = useCache('backtest_code', '600000.SH | 浦发银行')
const stockName = useCache('backtest_name', '浦发银行')
const stockIndustry = useCache('backtest_industry', '')
const startDate = useCache('backtest_start', '2025-01-02')
const endDate = useCache('backtest_end', todayISO())
const initialCash = useCache('backtest_cash', 100000)
const strategyKey = useCache('backtest_strategy', '')
const strategies = ref([])
const strategyParams = ref([])
const strategyCode = ref('')
const rawKlines = ref([])
const klines = ref([])
const trades = ref([])
const equityCurve = ref([])
const metric = ref({})
const freq = ref('daily')
const drawerVisible = ref(false)
const indicatorSettings = reactive({ showKline: true, showVolume: true, showMA: true, upColor: '#EC4899', downColor: '#22D3EE', maList: [{ period: 5, color: '#A855F7' }, { period: 20, color: '#FBBF24' }] })
const equityContainer = ref(null)
let equityChart = null
let settingsReady = false

const strategyOptions = computed(() =>
  strategies.value.map(s => ({ value: s.key, label: s.name }))
)

const equityMeta = computed(() => equityCurve.value.length ? equityCurve.value.length + ' 个交易日' : '')

function onStopUpdate(key, value) { stopSettings.value[key] = value; saveStop() }

async function loadKline() {
  const code = (stockCode.value || '').split('|')[0].trim()
  if (!code) return
  const data = await fetchKline(code, startDate.value, endDate.value)
  rawKlines.value = data?.length ? data : []
  applyFreq()
}

function applyFreq() {
  klines.value = resample(rawKlines.value, freq.value) || []
  nextTick(() => renderEquity())
}

function onFreqChange(f) {
  if (f === freq.value) return
  freq.value = f; trades.value = []; equityCurve.value = []; metric.value = {}; applyFreq()
}

function initEquityChart() {
  if (equityChart || !equityContainer.value) return
  equityChart = echarts.init(equityContainer.value)
  window.addEventListener('resize', () => equityChart?.resize())
}

function renderEquity() {
  initEquityChart()
  if (!equityCurve.value.length || !equityChart) { equityChart?.clear(); return }
  const dates = equityCurve.value.map(p => p.date)
  const values = equityCurve.value.map(p => p.equity)
  const baseline = initialCash.value || equityCurve.value[0].equity
  equityChart.setOption({
    animation: true, backgroundColor: 'transparent', textStyle: { color: '#C9D3E4' },
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(10,20,45,0.92)', borderColor: 'rgba(168,85,247,0.45)', textStyle: { color: '#E2E8F0' }, formatter: (p) => p[0].axisValueLabel + '<br/>权益：<b>' + fmtNum(p[0].value) + '</b>' },
    grid: { left: '4%', right: '3%', top: '12%', bottom: '10%', containLabel: true },
    xAxis: { type: 'category', data: dates, boundaryGap: false, axisLabel: { color: '#7B8AA6' }, axisLine: { lineStyle: { color: '#1E293B' } } },
    yAxis: { type: 'value', scale: true, axisLabel: { color: '#7B8AA6' }, splitLine: { lineStyle: { color: 'rgba(148,163,184,0.1)' } } },
    dataZoom: [{ type: 'inside', start: 0, end: 100 }, { type: 'slider', bottom: 6, height: 14, start: 0, end: 100, borderColor: 'transparent', backgroundColor: 'rgba(255,255,255,0.03)', fillerColor: 'rgba(168,85,247,0.15)', handleStyle: { color: '#A855F7' }, textStyle: { color: '#7B8AA6' } }],
    series: [{ type: 'line', data: values, smooth: true, showSymbol: false, lineStyle: { color: '#A855F7', width: 2 }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(168,85,247,0.35)' }, { offset: 1, color: 'rgba(168,85,247,0.02)' }] } }, markLine: { silent: true, symbol: 'none', lineStyle: { color: 'rgba(236,72,153,0.35)', type: 'dashed' }, data: [{ yAxis: baseline, label: { formatter: '初始资金', color: '#9AA5BD' } }] } }],
  }, true)
}

async function loadSettings() {
  try {
    const res = await loadIndicatorSettings('default')
    if (res?.settings && Object.keys(res.settings).length) {
      const s = res.settings
      if (s.showKline != null) indicatorSettings.showKline = s.showKline
      if (s.showVolume != null) indicatorSettings.showVolume = s.showVolume
      if (s.showMA != null) indicatorSettings.showMA = s.showMA
      if (s.upColor) indicatorSettings.upColor = s.upColor
      if (s.downColor) indicatorSettings.downColor = s.downColor
      if (Array.isArray(s.maList)) indicatorSettings.maList = s.maList
    }
  } catch { /* 使用默认设置 */ }
  settingsReady = true
}

// 每次修改设置时保存到后端
watch(indicatorSettings, () => {
  if (!settingsReady) return
  saveIndicatorSettings({ ...indicatorSettings }, 'default')
}, { deep: true })

function onStockSelect({ code, name, industry }) {
  stockName.value = name || ''
  stockIndustry.value = industry || ''
  stockCode.value = name ? `${code} | ${name}` : code
  loadKline()
}

async function loadStrategies() {
  try {
    const res = await strategyApi.list()
    strategies.value = (res.items || []).map(s => ({ key: 'user_' + s.id, name: s.name, id: s.id }))
    if (strategies.value.length) {
      if (!strategyKey.value || !strategies.value.some(s => s.key === strategyKey.value)) {
        strategyKey.value = strategies.value[0].key
      }
      await onStrategyChange()
    }
  } catch { strategies.value = [] }
}

function restoreCachedParams() {
  if (!strategyKey.value) return
  try {
    const raw = localStorage.getItem('ql_params_' + strategyKey.value)
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
  if (!strategyKey.value || !strategyParams.value.length) return
  const obj = {}
  strategyParams.value.forEach(p => { obj[p.id] = p.value })
  try { localStorage.setItem('ql_params_' + strategyKey.value, JSON.stringify(obj)) } catch {}
}

async function onStrategyChange() {
  if (!strategyKey.value) return
  try {
    const item = await strategyApi.get(strategyKey.value.slice(5))
    strategyCode.value = item.code || ''
    const schema = item.params_schema?.properties || {}
    strategyParams.value = Object.keys(schema).map(k => ({ id: k, label: schema[k].label || k, type: schema[k].type === 'number' ? 'number' : 'text', value: schema[k].default != null ? schema[k].default : '' }))
    restoreCachedParams()
  } catch { strategyParams.value = [] }
}

watch(strategyParams, saveParamsToCache, { deep: true })

function runStrategySandbox(code, params, klines) {
  const allSignals = []
  const context = {
    params: params || {},
    state: {},
    buy(opts) {
      allSignals.push({ type: 'buy', price: opts?.price || 0, reason: opts?.reason || '', trade_date: this._currentDate })
    },
    sell(opts) {
      allSignals.push({ type: 'sell', price: opts?.price || 0, reason: opts?.reason || '', trade_date: this._currentDate })
    },
    log(msg) { /* 静默记录 */ },
  }
  const src = code + '\nif (typeof init !== "function") throw new Error("缺少 init(context)"); if (typeof onTick !== "function") throw new Error("缺少 onTick(context, bar)"); return { init, onTick, onDestroy: typeof onDestroy === "function" ? onDestroy : function(){} };'
  const { init: initFn, onTick: onTickFn, onDestroy: destroyFn } = new Function(src)()
  initFn(context)
  for (const k of klines) {
    context._currentDate = String(k.trade_date)
    onTickFn(context, { open: k.open, high: k.high, low: k.low, close: k.close, volume: k.vol, vol: k.vol, trade_date: k.trade_date })
  }
  destroyFn(context)
  return allSignals
}

function runBacktest() {
  if (!klines.value.length) { alert('请先加载 K 线数据。'); return }
  if (!strategyCode.value) { alert('当前策略无代码，请选择含自定义 JS 的策略'); return }

  const closes = klines.value.map(k => Number(k.close))
  const dates = klines.value.map(k => k.trade_date)

  // 收集策略参数
  const params = {}
  strategyParams.value.forEach(p => { params[p.id] = p.value })

  // 在沙箱中执行策略代码，获得全部信号
  let signals
  try {
    signals = runStrategySandbox(strategyCode.value, params, klines.value)
  } catch (err) {
    alert('策略执行异常: ' + (err.message || String(err)))
    return
  }

  // 将信号转换为买卖指令
  const signalByDate = {}
  signals.forEach(s => { signalByDate[s.trade_date || s.date] = s })

  let cash = initialCash.value, position = 0, openTrade = null
  const t = [], eq = []
  const sp = collectStop()

  for (let i = 0; i < klines.value.length; i++) {
    const price = closes[i]
    const k = klines.value[i]
    const tradeDate = String(k.trade_date)
    let stopExited = false

    // 止损止盈（持仓时检查）
    if (position > 0 && openTrade) {
      const entry = openTrade.open_price, chg = (price - entry) / entry
      let exit = null
      if (sp.fixedTP > 0 && chg >= sp.fixedTP / 100) exit = '固定止盈'
      else if (sp.fixedSL > 0 && chg <= -sp.fixedSL / 100) exit = '固定止损'
      if (!exit && sp.breakevenSL > 0 && chg >= sp.breakevenSL / 100 && price <= entry) exit = '保本止损'
      if (!exit && sp.maSL > 0 && i >= sp.maSL - 1) { const slice = closes.slice(i - sp.maSL + 1, i + 1); if (price < slice.reduce((a, b) => a + b, 0) / slice.length) exit = '下破MA' + sp.maSL + '止损' }
      if (!exit && sp.trailingTP > 0) { if (price > (openTrade.peak_price || entry)) openTrade.peak_price = price; if ((price - (openTrade.peak_price || price)) / (openTrade.peak_price || price) <= -sp.trailingTP / 100) exit = '移动止盈' }
      if (!exit && sp.maTP > 0 && i >= sp.maTP - 1) { const slice = closes.slice(i - sp.maTP + 1, i + 1); if (price < slice.reduce((a, b) => a + b, 0) / slice.length) exit = '下破MA' + sp.maTP + '止盈' }
      if (exit) {
        const proceeds = openTrade.shares * price; cash += proceeds
        const pnl = proceeds - openTrade.shares * entry
        t.push({ open_date: String(openTrade.open_date), close_date: tradeDate, side: 'long', open_price: entry, close_price: price, pnl: +pnl.toFixed(2), pnl_pct: +((pnl / (openTrade.shares * entry)) * 100).toFixed(2), hold_days: Math.max(1, i - openTrade.open_index), reason: exit })
        position = 0; openTrade = null; stopExited = true
      }
    }

    // 策略信号（无持仓时买入信号、有持仓时卖出信号）
    // 注：止损/止盈触发的当天不允许再次买入
    const signal = signalByDate[tradeDate]
    if (signal) {
      if (signal.type === 'buy' && position === 0 && !stopExited) {
        const shares = Math.floor(cash / price / 100) * 100
        if (shares > 0) { cash -= shares * price; position = shares; openTrade = { open_index: i, open_date: tradeDate, open_price: price, shares, peak_price: price } }
      } else if (signal.type === 'sell' && position > 0 && openTrade) {
        const proceeds = openTrade.shares * price; cash += proceeds
        const pnl = proceeds - openTrade.shares * openTrade.open_price
        t.push({ open_date: String(openTrade.open_date), close_date: tradeDate, side: 'long', open_price: openTrade.open_price, close_price: price, pnl: +pnl.toFixed(2), pnl_pct: +((pnl / (openTrade.shares * openTrade.open_price)) * 100).toFixed(2), hold_days: Math.max(1, i - openTrade.open_index), reason: signal.reason || '信号卖出' })
        position = 0; openTrade = null
      }
    }

    eq.push({ date: tradeDate, equity: cash + position * price })
  }

  // 持有至期末（保留买入记录但不设 close_date → 图表上保留买入标记、不显示卖出标记）
  if (position > 0 && openTrade) {
    const i = klines.value.length - 1, price = closes[i]
    cash += openTrade.shares * price
    t.push({ open_date: String(openTrade.open_date), side: 'long', open_price: openTrade.open_price, reason: '持有至期末' })
    position = 0; openTrade = null; if (eq.length) eq[eq.length - 1].equity = cash
  }

  // 计算指标
  const finalEq = eq.length ? eq[eq.length - 1].equity : initialCash.value
  const totalRet = initialCash.value > 0 ? ((finalEq - initialCash.value) / initialCash.value) * 100 : 0
  const firstD = eq.length ? new Date(eq[0].date) : new Date(), lastD = eq.length ? new Date(eq[eq.length - 1].date) : new Date()
  const days = Math.max(1, Math.round((lastD - firstD) / 86400000))
  let peak = initialCash.value, maxDD = 0
  eq.forEach(p => { if (p.equity > peak) peak = p.equity; const dd = peak > 0 ? (peak - p.equity) / peak : 0; if (dd > maxDD) maxDD = dd })
  const wins = t.filter(x => (x.pnl || 0) > 0).length
  metric.value = { total_return: +totalRet.toFixed(2), annual_return: +((Math.pow(1 + totalRet / 100, 365 / days) - 1) * 100).toFixed(2), max_drawdown: +(-maxDD * 100).toFixed(2), sharpe_ratio: +sharpeRatio(eq).toFixed(2), win_rate: +(t.length > 0 ? (wins / t.length) * 100 : 0).toFixed(2), trade_count: t.length }
  trades.value = t.reverse(); equityCurve.value = eq
  nextTick(() => renderEquity())
}

onMounted(async () => {
  endDate.value = todayISO()

  // 从选股页跳转过来的待回测股票
  let autoRunStock = null
  try {
    const raw = localStorage.getItem('ql_pending_backtest')
    if (raw) {
      const parsed = JSON.parse(raw)
      if (parsed?.ts_code) {
        autoRunStock = parsed
        stockCode.value = parsed.name ? `${parsed.ts_code} | ${parsed.name}` : parsed.ts_code
        stockName.value = parsed.name || ''
        stockIndustry.value = parsed.industry || ''
        localStorage.removeItem('ql_pending_backtest')
      }
    }
  } catch {}

  await loadSettings()
  await loadStrategies()
  await loadKline()

  if (autoRunStock) {
    // 等待 nextTick 确保 KlineCard 已渲染，再运行回测
    await nextTick()
    runBacktest()
  }
})
onUnmounted(() => { if (equityChart) { window.removeEventListener('resize', equityChart.resize); equityChart.dispose() } })
</script>
