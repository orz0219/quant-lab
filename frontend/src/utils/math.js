export function simpleMA(values, n) {
  const out = []
  let sum = 0
  for (let i = 0; i < values.length; i++) {
    sum += Number(values[i])
    if (i >= n) sum -= Number(values[i - n])
    out.push(i >= n - 1 ? +(sum / n).toFixed(4) : null)
  }
  return out
}

function stddev(values) {
  if (!values || values.length === 0) return 0
  const n = values.length
  const mean = values.reduce((a, b) => a + b, 0) / n
  const variance = values.reduce((a, b) => a + (b - mean) * (b - mean), 0) / n
  return Math.sqrt(variance)
}

export function sharpeRatio(equityCurve) {
  if (!equityCurve || equityCurve.length < 2) return 0
  const rets = []
  for (let i = 1; i < equityCurve.length; i++) {
    const prev = equityCurve[i - 1].equity
    const cur = equityCurve[i].equity
    if (prev > 0) rets.push(cur / prev - 1)
  }
  if (rets.length === 0) return 0
  const mean = rets.reduce((a, b) => a + b, 0) / rets.length
  const sd = stddev(rets)
  if (sd === 0) return 0
  return (mean / sd) * Math.sqrt(252)
}

function normalizeDate(v) {
  if (v instanceof Date) return v
  if (v == null) return null
  const s = String(v).replace(/-/g, '')
  if (s.length !== 8) return null
  return new Date(Number(s.slice(0, 4)), Number(s.slice(4, 6)) - 1, Number(s.slice(6, 8)))
}

function formatDateKey(d) {
  const m = d.getMonth() + 1
  const day = d.getDate()
  return `${d.getFullYear()}-${m < 10 ? '0' + m : m}-${day < 10 ? '0' + day : day}`
}

function weekKey(date) {
  const d = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  const day = d.getDay()
  const diffToMonday = day === 0 ? -6 : 1 - day
  d.setDate(d.getDate() + diffToMonday)
  return formatDateKey(d)
}

function toWeekly(klines) {
  if (!klines || klines.length === 0) return []
  const sorted = klines.slice().sort((a, b) => {
    const da = normalizeDate(a.trade_date)
    const db = normalizeDate(b.trade_date)
    return (da ? da.getTime() : 0) - (db ? db.getTime() : 0)
  })
  const groups = new Map()
  const order = []
  for (const k of sorted) {
    const date = normalizeDate(k.trade_date)
    if (!date) continue
    const key = weekKey(date)
    let g = groups.get(key)
    if (!g) {
      g = { open: Number(k.open), high: Number(k.high), low: Number(k.low), close: Number(k.close), vol: Number(k.vol) || 0, lastDate: date }
      groups.set(key, g)
      order.push(key)
    } else {
      g.high = Math.max(g.high, Number(k.high))
      g.low = Math.min(g.low, Number(k.low))
      g.close = Number(k.close)
      g.vol = g.vol + (Number(k.vol) || 0)
      g.lastDate = date
    }
  }
  return order.map(key => {
    const g = groups.get(key)
    return { trade_date: formatDateKey(g.lastDate), open: +g.open.toFixed(4), high: +g.high.toFixed(4), low: +g.low.toFixed(4), close: +g.close.toFixed(4), vol: +g.vol.toFixed(2) }
  })
}

export function resample(klines, freq) {
  if (freq === 'weekly') return toWeekly(klines)
  return klines
}
