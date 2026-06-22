<template>
  <Teleport to="body">
    <div v-if="visible" class="detail-overlay" @click.self="$emit('close')">
      <div class="detail-modal">
        <div class="detail-head">
          <span class="detail-title">{{ stock?.ts_code }} | {{ stock?.name }}</span>
          <button class="detail-close" @click="$emit('close')">✕</button>
        </div>
        <div class="detail-date-row">
          <div class="field" style="flex:1;"><label>起始日期</label><input type="date" v-model="startDate" /></div>
          <div class="field" style="flex:1;"><label>结束日期</label><input type="date" v-model="endDate" /></div>
        </div>
        <div class="detail-chart">
          <KlineCard
            v-if="klines.length"
            :klines="klines"
            :trades="trades"
            :stock-name="stock?.name || ''"
            :freq="freq"
            :indicator-settings="indicatorSettings"
            @update:freq="onFreqChange"
            @open-settings="drawerVisible = true"
          />
          <div v-else class="detail-loading">加载中...</div>
        </div>
      </div>
    </div>
    <IndicatorDrawer
      v-model:visible="drawerVisible"
      v-model:showKline="indicatorSettings.showKline"
      v-model:showVolume="indicatorSettings.showVolume"
      v-model:showMA="indicatorSettings.showMA"
      v-model:upColor="indicatorSettings.upColor"
      v-model:downColor="indicatorSettings.downColor"
      v-model:maList="indicatorSettings.maList"
      @close="drawerVisible = false"
    />
  </Teleport>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import KlineCard from '@/components/KlineCard.vue'
import IndicatorDrawer from '@/components/IndicatorDrawer.vue'
import { fetchKline, loadIndicatorSettings } from '@/utils/request.js'
import { resample } from '@/utils/math.js'

const props = defineProps({
  visible: { type: Boolean, default: false },
  stock: { type: Object, default: null },
  strategyCode: { type: String, default: '' },
  strategyParams: { type: Array, default: () => [] },
})
const emit = defineEmits(['close'])

const startDate = ref('')
const endDate = ref('')
const rawKlines = ref([])
const klines = ref([])
const trades = ref([])
const freq = ref('daily')
const drawerVisible = ref(false)

const indicatorSettings = reactive({
  showKline: true, showVolume: true, showMA: true,
  upColor: '#EC4899', downColor: '#22D3EE',
  maList: [{ period: 5, color: '#A855F7' }, { period: 20, color: '#FBBF24' }],
})

// ---------- 沙箱执行策略 ----------
function runStrategyOnStock(code, params, klinesData) {
  const signals = []
  const ctx = {
    params: params || {},
    state: {},
    buy(opts) { signals.push({ type: 'buy', price: opts?.price || 0, reason: opts?.reason || '', trade_date: this._curDate }) },
    sell(opts) { signals.push({ type: 'sell', price: opts?.price || 0, reason: opts?.reason || '', trade_date: this._curDate }) },
    log() {},
  }
  const src = code + '\nif (typeof init !== "function") throw new Error("缺少 init"); if (typeof onTick !== "function") throw new Error("缺少 onTick"); return { init, onTick, onDestroy: typeof onDestroy === "function" ? onDestroy : function(){} };'
  const { init, onTick, onDestroy } = new Function(src)()
  init(ctx)
  for (const k of klinesData) {
    ctx._curDate = String(k.trade_date)
    onTick(ctx, { open: k.open, high: k.high, low: k.low, close: k.close, volume: k.vol, vol: k.vol, trade_date: k.trade_date })
  }
  onDestroy(ctx)
  return signals
}

// ---------- 加载 K 线（日线）并用 resample 处理频率 ----------
async function loadKlines() {
  if (!props.stock || !startDate.value || !endDate.value) return
  klines.value = []
  trades.value = []

  // 始终获取日线原始数据
  const raw = await fetchKline(props.stock.ts_code, startDate.value, endDate.value)
  if (!raw || !raw.length) return

  rawKlines.value = raw.map(k => ({
    trade_date: String(k.trade_date || k.date),
    open: k.open, high: k.high, low: k.low, close: k.close, vol: k.vol || k.volume || 0,
  }))
  applyFreq()
}

function applyFreq() {
  klines.value = resample(rawKlines.value, freq.value) || []
  runSignals()
}

function runSignals() {
  trades.value = []
  if (!props.strategyCode || !klines.value.length) return
  const params = {}
  props.strategyParams.forEach(p => { params[p.id] = p.value })
  const allSignals = runStrategyOnStock(props.strategyCode, params, klines.value)

  // 配对买入/卖出构造 trades
  const result = []
  let open = null
  for (const s of allSignals) {
    if (s.type === 'buy' && !open) {
      open = { open_date: s.trade_date, open_price: s.price }
    } else if (s.type === 'sell' && open) {
      result.push({ open_date: open.open_date, close_date: s.trade_date, side: 'long', open_price: open.open_price, close_price: s.price, pnl: 0, reason: s.reason || '信号' })
      open = null
    }
  }
  trades.value = result
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
  } catch { /* 默认设置 */ }
}

// 打开弹窗时初始化日期 + 读取后台配置
watch(() => props.visible, async (v) => {
  if (!v || !props.stock) return
  await loadSettings()
  const now = new Date()
  const ago = new Date(now)
  ago.setFullYear(ago.getFullYear() - 1)
  startDate.value = `${ago.getFullYear()}-${String(ago.getMonth() + 1).padStart(2, '0')}-${String(ago.getDate()).padStart(2, '0')}`
  endDate.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
  loadKlines()
})

// 日期变化 → 自动重载
watch([startDate, endDate], () => {
  if (props.visible && props.stock) loadKlines()
})

// 频率切换 → 前端 resample，无需后端接口
function onFreqChange(f) {
  freq.value = f
  applyFreq()
}

// 策略代码变化 → 重新跑信号
watch(() => props.strategyCode, () => {
  if (props.visible && props.stock && rawKlines.value.length) runSignals()
})
</script>
