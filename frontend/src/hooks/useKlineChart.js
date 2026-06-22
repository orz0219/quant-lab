import { ref } from 'vue'
import { simpleMA } from '@/utils/math.js'
import { fmtNum } from '@/utils/format.js'

export function useKlineChart(containerRef) {
  let chart = null
  let candlestickSeries = null
  let volumeSeries = null
  let maSeriesList = []
  const maConfigs = ref([{ period: 5, color: '#A855F7' }, { period: 20, color: '#FBBF24' }])
  let lastKlines = null
  let crosshairHandler = null
  let markersCache = null

  function init() {
    if (!containerRef.value || chart) return
    chart = LightweightCharts.createChart(containerRef.value, {
      layout: { background: { type: 'solid', color: 'transparent' }, textColor: '#C9D3E4' },
      grid: { vertLines: { color: 'rgba(148,163,184,0.08)' }, horzLines: { color: 'rgba(148,163,184,0.08)' } },
      crosshair: { mode: LightweightCharts.CrosshairMode.Normal, vertLine: { color: '#7C8AA7', style: LightweightCharts.LineStyle.Dashed, width: 1, labelBackgroundColor: '#0A1330' }, horzLine: { color: '#7C8AA7', style: LightweightCharts.LineStyle.Dashed, width: 1, labelBackgroundColor: '#0A1330' } },
      rightPriceScale: { borderColor: 'rgba(255,255,255,0.08)', scaleMargins: { top: 0.05, bottom: 0.25 } },
      timeScale: { borderColor: 'rgba(255,255,255,0.08)', timeVisible: true },
    })
    candlestickSeries = chart.addCandlestickSeries({ upColor: '#EC4899', downColor: '#22D3EE', borderUpColor: '#EC4899', borderDownColor: '#22D3EE', wickUpColor: '#EC4899', wickDownColor: '#22D3EE' })
    volumeSeries = chart.addHistogramSeries({ priceFormat: { type: 'volume' }, priceScaleId: 'volume', color: 'rgba(34,211,238,0.3)' })
    chart.priceScale('volume').applyOptions({ scaleMargins: { top: 0.72, bottom: 0 } })

    // 缩放/拖动时重新应用买卖标记，防止 markers 丢失
    chart.timeScale().subscribeVisibleTimeRangeChange(() => {
      if (markersCache?.length) {
        candlestickSeries?.setMarkers(markersCache)
      }
    })
  }

  function render(klines, trades) {
    if (!chart) init()
    lastKlines = klines
    if (!klines || !klines.length) {
      candlestickSeries?.setData([])
      volumeSeries?.setData([])
      maSeriesList.forEach(s => chart?.removeSeries(s))
      maSeriesList = []
      return
    }

    // 构建买入/卖出日期集合
    const buyDates = new Set()
    const sellDates = new Set()
    if (trades?.length) {
      trades.forEach(t => {
        if (t.open_date) buyDates.add(t.open_date)
        if (t.close_date) sellDates.add(t.close_date)
      })
    }

    // K 线数据：买卖点用鲜明纯色标识，其余保持默认涨跌色
    const candleData = klines.map(k => {
      const d = { time: k.trade_date, open: k.open, high: k.high, low: k.low, close: k.close }
      if (buyDates.has(k.trade_date)) {
        // 买入点 → 亮红色实体 + 金色边框，视觉上突出
        d.color = '#FF3333'
        d.borderColor = '#FFD700'
        d.wickColor = '#FFD700'
      } else if (sellDates.has(k.trade_date)) {
        // 卖出点 → 亮绿色实体 + 白色边框
        d.color = '#00CC00'
        d.borderColor = '#FFFFFF'
        d.wickColor = '#FFFFFF'
      }
      return d
    })
    candlestickSeries?.setData(candleData)

    // 买卖标记：大尺寸形状 + 买入▲/卖出▼，在 init 中注册了缩放恢复
    if (trades?.length) {
      markersCache = trades.flatMap(t => {
        const m = []
        if (t.open_date) m.push({ time: t.open_date, position: 'belowBar', color: '#FF3333', shape: 'arrowUp', size: 1, text: 'B' })
        if (t.close_date) m.push({ time: t.close_date, position: 'aboveBar', color: '#00CC00', shape: 'arrowDown', size: 1, text: 'S' })
        return m
      })
      candlestickSeries?.setMarkers(markersCache)
    } else {
      markersCache = null
      candlestickSeries?.setMarkers([])
    }

    const volData = klines.map(k => ({ time: k.trade_date, value: k.vol, color: k.close >= k.open ? 'rgba(236,72,153,0.4)' : 'rgba(34,211,238,0.4)' }))
    volumeSeries?.setData(volData)
    renderMASeries(klines)
    chart?.timeScale().fitContent()
  }

  function renderMASeries(klines) {
    if (!chart) return
    maSeriesList.forEach(s => chart.removeSeries(s))
    maSeriesList = []
    const closes = klines.map(d => d.close)
    maConfigs.value.forEach(cfg => {
      if (cfg.period < 1) return
      const s = chart.addLineSeries({ color: cfg.color, lineWidth: 1, lastValueVisible: false, priceLineVisible: false })
      const ma = simpleMA(closes, cfg.period)
      const data = []
      for (let i = 0; i < klines.length; i++) {
        if (ma[i] != null) data.push({ time: klines[i].trade_date, value: ma[i] })
      }
      s.setData(data)
      maSeriesList.push(s)
    })
  }

  function updateColors(upColor, downColor) {
    candlestickSeries?.applyOptions({ upColor, borderUpColor: upColor, wickUpColor: upColor, downColor, borderDownColor: downColor, wickDownColor: downColor })
  }

  function setMAVisible(visible) {
    maSeriesList.forEach(s => s.applyOptions({ visible }))
  }

  function setCandlestickVisible(visible) {
    candlestickSeries?.applyOptions({ visible })
  }

  function setVolumeVisible(visible) {
    volumeSeries?.applyOptions({ visible })
  }

  function onCrosshairMove(callback) {
    if (!chart) return
    if (crosshairHandler) chart.unsubscribeCrosshairMove(crosshairHandler)
    crosshairHandler = (param) => {
      if (param?.time && lastKlines) {
        const idx = lastKlines.findIndex(k => String(k.trade_date) === String(param.time))
        if (idx >= 0) callback(lastKlines, idx)
      }
    }
    chart.subscribeCrosshairMove(crosshairHandler)
  }

  function resize() {
    if (chart && containerRef.value) {
      chart.applyOptions({ width: containerRef.value.clientWidth, height: containerRef.value.clientHeight })
    }
  }

  function destroy() {
    if (crosshairHandler && chart) chart.unsubscribeCrosshairMove(crosshairHandler)
    maSeriesList.forEach(s => chart?.removeSeries(s))
    maSeriesList = []
    chart?.remove()
    chart = null; candlestickSeries = null; volumeSeries = null; lastKlines = null; markersCache = null
  }

  return { init, render, updateColors, setMAVisible, setCandlestickVisible, setVolumeVisible, onCrosshairMove, resize, destroy, maConfigs }
}
