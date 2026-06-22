function pad2(n) { return n < 10 ? '0' + n : '' + n }

export function toDateInt(v) {
  if (!v) return ''
  const d = new Date(v)
  if (Number.isNaN(d.getTime())) return ''
  return `${d.getFullYear()}${pad2(d.getMonth() + 1)}${pad2(d.getDate())}`
}

export function todayISO() {
  const d = new Date()
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`
}

export function parseTsCode(raw) {
  if (!raw) return ''
  return String(raw).split('|')[0].trim()
}

export function parseDate(v) {
  if (!v) return null
  if (v instanceof Date) return v
  const s = String(v).replace(/-/g, '')
  if (s.length !== 8) return null
  return new Date(Number(s.slice(0, 4)), Number(s.slice(4, 6)) - 1, Number(s.slice(6, 8)))
}

export function daysBetween(a, b) {
  const d1 = parseDate(a)
  const d2 = parseDate(b)
  if (!d1 || !d2) return 0
  return Math.round((d2 - d1) / 86400000)
}
