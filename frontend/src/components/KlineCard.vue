<template>
  <div class="glass card kline-card">
    <div class="card-head">
      <div class="card-title"><span class="title-dot"></span>价格走势<span class="muted small"> {{ klineMeta }}</span></div>
      <div class="tabs">
        <span :class="['tab', { active: freq === 'daily' }]" @click="switchFreq('daily')">日 K</span>
        <span :class="['tab', { active: freq === 'weekly' }]" @click="switchFreq('weekly')">周 K</span>
      </div>
    </div>
    <KLineInfo
      :data="currentKline"
      :prev-close="prevClose"
      :ma-values="currentMAValues"
      @openSettings="$emit('openSettings')"
    />
    <div ref="klineContainer" class="chart tall"></div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import KLineInfo from '@/components/KLineInfo.vue'
import { useKlineChart } from '@/hooks/useKlineChart.js'
import { simpleMA } from '@/utils/math.js'
import { fmtNum } from '@/utils/format.js'

const props = defineProps({
  klines: { type: Array, default: () => [] },
  trades: { type: Array, default: () => [] },
  stockName: { type: String, default: '' },
  freq: { type: String, default: 'daily' },
  indicatorSettings: { type: Object, default: () => ({ maList: [] }) },
})

const emit = defineEmits(['update:freq', 'openSettings'])

const klineContainer = ref(null)
const currentKline = ref(null)
const prevClose = ref(null)
const currentMAValues = ref([])

const {
  init, render, onCrosshairMove, destroy,
  updateColors, setMAVisible, setCandlestickVisible, setVolumeVisible, maConfigs,
} = useKlineChart(klineContainer)

// ========== 十字线联动 KLineInfo ==========

function handleCrosshairMove(data, idx) {
  currentKline.value = data[idx]
  prevClose.value = idx > 0 ? data[idx - 1].close : null
  const closes = data.map(d => d.close)
  currentMAValues.value = (props.indicatorSettings.maList || []).map(cfg => {
    const ma = simpleMA(closes, cfg.period)
    return { label: `MA${cfg.period}`, value: ma[idx] != null ? fmtNum(ma[idx]) : '—', color: cfg.color }
  })
}

// ========== 渲染图表（render + 注册十字线 + 应用设置） ==========

function renderChart() {
  nextTick(() => {
    // 先更新 MA 配置，再 render（否则 renderMASeries 读到的是旧配置）
    maConfigs.value = props.indicatorSettings.maList || []
    render(props.klines, props.trades)
    onCrosshairMove(handleCrosshairMove)
    updateColors(props.indicatorSettings.upColor, props.indicatorSettings.downColor)
    setMAVisible(props.indicatorSettings.showMA)
    setCandlestickVisible(props.indicatorSettings.showKline)
    setVolumeVisible(props.indicatorSettings.showVolume)
  })
}

// ========== meta 信息 ==========

const klineMeta = computed(() => {
  const k = props.klines
  if (!k.length) return ''
  return `${props.stockName ? props.stockName + ' · ' : ''}${props.freq === 'weekly' ? '周K' : '日K'} · ${k[0].trade_date} → ${k[k.length - 1].trade_date} · ${k.length} 根`
})

// ========== 频率切换 ==========

function switchFreq(f) {
  if (f === props.freq) return
  emit('update:freq', f)
}

// ========== 初始化 currentKline/prevClose（数据变化时） ==========

watch(() => props.klines, (newKlines) => {
  if (newKlines.length) {
    const idx = newKlines.length - 1
    currentKline.value = newKlines[idx]
    prevClose.value = idx > 0 ? newKlines[idx - 1].close : null
    // 根据末根K线计算初始 MA 值（让 KLineInfo 首次渲染就有数据）
    const closes = newKlines.map(d => d.close)
    currentMAValues.value = (props.indicatorSettings.maList || []).map(cfg => {
      const ma = simpleMA(closes, cfg.period)
      return { label: `MA${cfg.period}`, value: ma[idx] != null ? fmtNum(ma[idx]) : '—', color: cfg.color }
    })
  }
}, { immediate: true })

// ========== klines / trades 变化 → 重绘图表 ==========

watch([() => props.klines, () => props.trades], renderChart, { deep: true })

// ========== 指标设置同步到图表 ==========

watch(() => [props.indicatorSettings.upColor, props.indicatorSettings.downColor], ([up, down]) => {
  updateColors(up, down)
})

watch(() => props.indicatorSettings.maList, (list) => {
  maConfigs.value = list
  if (props.klines.length) renderChart()
}, { deep: true })

watch(() => props.indicatorSettings.showMA, (v) => {
  setMAVisible(v)
})

watch(() => props.indicatorSettings.showKline, (v) => {
  setCandlestickVisible(v)
})

watch(() => props.indicatorSettings.showVolume, (v) => {
  setVolumeVisible(v)
})

// ========== 生命周期 ==========

onMounted(() => {
  if (props.klines.length) renderChart()
})

onUnmounted(() => {
  destroy()
})
</script>
